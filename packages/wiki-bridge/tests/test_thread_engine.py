"""Thread engine: proposals, non-compensatory verify, feedback rank, contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge import thread_evidence, thread_store
from wiki_bridge.prerank import prerank
from wiki_bridge.thread_engine import (
    bootstrap_thread,
    build_exp_contract,
    consolidate,
    decide,
    distill_skills,
    propose,
    rerank_with_feedback,
    rollback,
    verify_papers,
)


def _thread(tmp_path: Path, **patch):
    thread_store.create_thread(tmp_path, "method", thread_id="t1", keywords=["method"])
    if patch:
        thread_store.update_thread(tmp_path, "t1", patch)
    return tmp_path


def test_low_risk_auto_apply_and_rollback(tmp_path):
    _thread(tmp_path)
    proposal = propose(tmp_path, "t1", "add_claim", {"text": "Adapters reduce forgetting."})
    assert proposal["status"] == "applied"
    assert proposal["risk"] == "low"
    data = thread_store.load_thread(tmp_path, "t1")
    assert data["claims"][0]["node_state"] == "candidate"
    rolled = rollback(tmp_path, "t1", proposal["proposal_id"])
    assert rolled["status"] == "rolled_back"
    assert thread_store.load_thread(tmp_path, "t1")["claims"] == []


def test_high_risk_requires_reason(tmp_path):
    _thread(tmp_path, claims=[{"id": "C1", "text": "A claim", "status": "open", "node_state": "candidate"}])
    proposal = propose(tmp_path, "t1", "delete_node", {"kind": "claim", "id": "C1"}, reason="duplicate")
    assert proposal["status"] == "pending"
    try:
        decide(tmp_path, "t1", proposal["proposal_id"], "accept")
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert thread_store.load_thread(tmp_path, "t1")["claims"]
    decide(tmp_path, "t1", proposal["proposal_id"], "accept", reason="claim was duplicated by C2")
    assert thread_store.load_thread(tmp_path, "t1")["claims"] == []


def test_rejected_pattern_holds_low_proposal(tmp_path):
    _thread(tmp_path, claims=[{"id": "C1", "text": "A claim", "status": "open", "node_state": "verified"}])
    thread_store.record_feedback(tmp_path, "t1", action="skip", path="llm/2026/preprint", note="preprint only")
    proposal = propose(
        tmp_path,
        "t1",
        "add_evidence",
        {"claim_id": "C1", "quote": "preprint only", "paper_path": "llm/2026/preprint"},
    )
    assert proposal["status"] == "pending"
    assert proposal["held_by"] == "preprint only"
    assert thread_evidence.list_evidences(tmp_path, "t1") == []


def test_feedback_changes_rank(tmp_path):
    _thread(tmp_path)
    thread_store.record_feedback(tmp_path, "t1", action="accept", path="llm/2026/adapter-forgetting")
    ranked = rerank_with_feedback(
        tmp_path,
        "t1",
        [
            {"title": "baseline method", "summary": "method paper"},
            {"title": "adapter method", "summary": "method paper"},
        ],
    )
    assert ranked["papers"][0]["title"] == "adapter method"
    assert ranked["papers"][0]["factors"]["feedback_boost"] > ranked["papers"][1]["factors"]["feedback_boost"]


def test_prerank_feedback_boost_is_visible():
    base = prerank("method", [{"title": "baseline method"}, {"title": "adapter method"}], use_citations=False)
    boosted = prerank(
        "method",
        [{"title": "baseline method"}, {"title": "adapter method"}],
        use_citations=False,
        feedback_terms=["adapter"],
    )
    assert base["items"][0]["prerank_feedback"] == 0
    assert boosted["items"][0]["title"] == "adapter method"
    assert boosted["items"][0]["prerank_feedback"] > 0


def test_verify_is_non_compensatory(tmp_path):
    _thread(
        tmp_path,
        claims=[{"id": "C1", "text": "parameter efficient adapters reduce catastrophic forgetting", "status": "open"}],
        evidence_gaps=[{"id": "G1", "claim_id": "C1", "need": "evidence", "note": "adapters reduce catastrophic forgetting"}],
    )
    papers = [
        {
            "title": "Adapters",
            "summary": "parameter efficient adapters reduce catastrophic forgetting in sequential training",
            "metrics": "accuracy 0.91",
            "path": "llm/2026/adapters",
        },
        {
            "title": "Quantum chemistry basis sets",
            "summary": "Complete basis set extrapolation for molecular energies",
            "metrics": "F1 0.99",
        },
    ]
    readme = tmp_path / "README.md"
    readme.write_text("# Wiki\n\n## Notes\n\nkeep\n", encoding="utf-8")
    report = verify_papers(tmp_path, "t1", papers, readme_path=str(readme))
    by_title = {row["title"]: row["verdict"] for row in report["papers"]}
    assert by_title["Adapters"] == "thread_pass"
    assert by_title["Quantum chemistry basis sets"] == "thread_conflict"
    text = readme.read_text(encoding="utf-8")
    assert "主线冲突" in text
    assert "## Notes" in text
    assert report["counts"]["thread_conflict"] == 1


def test_verify_abstain_and_screen(tmp_path):
    _thread(tmp_path)
    empty = verify_papers(tmp_path, "t1", [{"title": "Anything", "metrics": "F1 1.0"}])
    assert empty["papers"][0]["verdict"] == "abstain"
    thread_store.update_thread(
        tmp_path,
        "t1",
        {
            "claims": [{"id": "C1", "text": "sequential adapters preserve prior tasks", "status": "open"}],
            "evidence_gaps": [{"id": "G1", "claim_id": "C1", "need": "evidence", "note": "sequential training needs more evidence here"}],
        },
    )
    screened = verify_papers(
        tmp_path,
        "t1",
        [{"title": "sequential rendering of indoor scenes", "summary": "sequential rendering of indoor scenes"}],
    )
    assert screened["papers"][0]["verdict"] == "needs_screen"


def test_bootstrap_stays_pending_until_accept(tmp_path):
    papers = [
        {
            "title": "A",
            "contribution": "Adapters reduce catastrophic forgetting.",
            "weaknesses": "Only evaluated on English benchmarks.",
            "core_idea": "Adapters reduce catastrophic forgetting.",
            "path": "llm/2026/a",
        },
        {
            "title": "B",
            "contribution": "Adapters reduce catastrophic forgetting on sequential tasks.",
            "weaknesses": "Only evaluated on English benchmarks today.",
            "core_idea": "Adapters reduce catastrophic forgetting on sequential tasks.",
            "path": "llm/2026/b",
        },
    ]
    drafted = bootstrap_thread(tmp_path, papers, thread_id="boot", title="Adapters")
    assert drafted["status"] == "draft"
    assert thread_store.load_thread(tmp_path, "boot")["claims"] == []
    assert all(p["status"] == "pending" for p in drafted["proposals"])
    decide(tmp_path, "boot", "all", "accept", reason="draft looks right")
    data = thread_store.load_thread(tmp_path, "boot")
    assert data["status"] == "active"
    assert data["claims"]
    assert data["claims"][0]["node_state"] == "candidate"
    assert thread_evidence.list_evidences(tmp_path, "boot")


def test_consolidate_flags_duplicate_gaps_and_unused_evidence(tmp_path):
    _thread(
        tmp_path,
        claims=[{"id": "C1", "text": "sequential adapters", "status": "open", "node_state": "candidate"}],
        evidence_gaps=[
            {"id": "G1", "claim_id": "C1", "need": "evidence", "note": "Only evaluated on English benchmarks", "node_state": "candidate"},
            {"id": "G2", "claim_id": "C1", "need": "evidence", "note": "Only evaluated on English benchmarks today", "node_state": "candidate"},
        ],
    )
    thread_evidence.add_evidence(
        tmp_path, "t1", claim_id="C1", quote="quantum chemistry basis sets are complete", gate="suggested"
    )
    out = consolidate(tmp_path, "t1")
    ops = {row["op"]: row["status"] for row in out["proposals"]}
    assert ops["mark_pending"] == "applied"
    assert ops["merge_gap"] == "pending"
    evidence = thread_evidence.list_evidences(tmp_path, "t1")[0]
    assert evidence["node_state"] == "pending"


def test_distill_waits_for_repetition_then_confirmation(tmp_path):
    _thread(tmp_path, evidence_gaps=[{"id": "G1", "claim_id": "C1", "need": "evidence", "note": "gap"}])
    for _ in range(2):
        propose(tmp_path, "t1", "add_claim", {"text": "one"})
        propose(tmp_path, "t1", "add_gap", {"note": "another gap"})
        propose(tmp_path, "t1", "add_claim", {"text": "two"})
    out = distill_skills(tmp_path, "t1", threshold=2)
    assert out["proposals"]
    assert out["proposals"][0]["status"] == "pending"
    decide(tmp_path, "t1", out["proposals"][0]["proposal_id"], "accept", reason="sequence is stable")
    skills = list((tmp_path / "content" / "threads" / "t1" / "skills").rglob("SKILL.md"))
    assert skills
    assert list((tmp_path / "content" / "threads" / "t1" / "skills").rglob("run.py"))
    index = json.loads((tmp_path / "content" / "skills" / "distilled" / "index.json").read_text(encoding="utf-8"))
    assert index


def test_experiment_node_starts_candidate(tmp_path):
    _thread(tmp_path)
    thread_store.link_exp(tmp_path, "t1", "exp-adapters")
    nodes = thread_store.load_thread(tmp_path, "t1")["experiment_nodes"]
    assert nodes[0]["id"] == "exp-adapters"
    assert nodes[0]["node_state"] == "candidate"


def test_consolidate_pending_when_verified_claim_loses_support(tmp_path):
    _thread(
        tmp_path,
        claims=[{"id": "C1", "text": "sequential adapters", "status": "supported", "node_state": "verified"}],
    )
    thread_evidence.add_evidence(tmp_path, "t1", claim_id="C1", quote="sequential adapters help", gate="accepted")
    rows = thread_evidence.list_evidences(tmp_path, "t1")
    rows[0]["node_state"] = "rejected"
    thread_evidence._rewrite_evidences(tmp_path, "t1", rows)
    out = consolidate(tmp_path, "t1")
    assert any(row["op"] == "set_node_state" and row["status"] == "pending" for row in out["proposals"])


def test_acceptance_rate_counts_explicit_decisions(tmp_path):
    from wiki_bridge.thread_engine import proposal_stats

    _thread(tmp_path, claims=[{"id": "C1", "text": "keep", "status": "open", "node_state": "candidate"}])
    proposal = propose(tmp_path, "t1", "delete_node", {"kind": "claim", "id": "C1"})
    decide(tmp_path, "t1", proposal["proposal_id"], "reject", reason="still needed")
    stats = proposal_stats(tmp_path, "t1")
    assert stats["rejected"] == 1
    assert stats["acceptance_rate"] == 0


def test_sync_rank_uses_recorded_feedback(tmp_path):
    _thread(tmp_path)
    thread_store.record_feedback(tmp_path, "t1", action="accept", path="llm/2026/adapter-forgetting")
    rows = thread_store.sync_papers_to_thread(
        tmp_path,
        "t1",
        [
            {"title": "baseline method", "summary": "method paper", "path": "a"},
            {"title": "adapter method", "summary": "method paper", "path": "b"},
        ],
    )
    by_title = {row["title"]: row["R"] for row in rows}
    assert by_title["adapter method"] > by_title["baseline method"]


def test_verify_writes_existing_wiki_readme(tmp_path):
    _thread(tmp_path)
    page = tmp_path / "content" / "wiki" / "pages" / "llm" / "2026" / "foo" / "README.md"
    page.parent.mkdir(parents=True)
    page.write_text("# Paper\n", encoding="utf-8")
    verify_papers(tmp_path, "t1", [{"title": "Anything", "path": "llm/2026/foo", "metrics": "F1 1.0"}])
    assert "覆盖检查" in page.read_text(encoding="utf-8")


def test_github_lookup_and_exp_proposals(tmp_path):
    from wiki_bridge.thread_engine import lookup_github_repo, write_exp_contract

    def fake(url):
        if url.endswith("/commits?per_page=1"):
            return [{"commit": {"message": "fix metric"}}]
        if "issues" in url:
            return [{"title": "install fails"}]
        return {"html_url": "https://github.com/ex/adapters", "stargazers_count": 4, "pushed_at": "2026-01-02T00:00:00Z"}

    info = lookup_github_repo("https://github.com/ex/adapters", get_json=fake)
    assert info["stars"] == 4
    assert "fix metric" in info["activity"]
    assert info["issues_summary"] == "install fails"
    _thread(tmp_path)
    out = write_exp_contract(
        {"title": "Adapter paper", "method": "LoRA", "metrics": "accuracy 0.9"},
        tmp_path / "contract",
        wiki_root=tmp_path,
        thread_id="t1",
        fetch_github=False,
    )
    ops = {item["op"]: item["status"] for item in out["proposals"]}
    assert ops["add_experiment"] == "pending"
    assert ops["add_gap"] == "pending"
    assert thread_store.load_thread(tmp_path, "t1")["experiment_nodes"] == []


def test_exp_contract_marks_missing_and_does_not_invent():
    contract = build_exp_contract(
        {
            "title": "Adapter paper",
            "method": "LoRA on attention",
            "metrics": "accuracy 0.91",
            "github": {"url": "https://github.com/example/adapters", "stars": 12, "issues_summary": "install fails on py3.12"},
        }
    )
    assert "data_split" in contract["missing"]
    assert "hyperparameters" in contract["missing"]
    assert contract["obligations"]["algorithm"] == "LoRA on attention"
    assert contract["github"]["stars"] == 12
    assert "accuracy 0.91" in json.dumps(contract)
