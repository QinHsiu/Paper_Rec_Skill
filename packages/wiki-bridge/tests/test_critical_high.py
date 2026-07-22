"""Critical→High engines: evidence score, stats rigor, survey, novelty, fig, deep research, session, AL."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.deep_research import build_deep_research_plan
from wiki_bridge.evidence_ground import ground_answer
from wiki_bridge.evidence_score import gather_evidence, relevance_score
from wiki_bridge.fig_review import review_figures
from wiki_bridge.novelty_check import novelty_against_corpus
from wiki_bridge import research_session as rs
from wiki_bridge.screen_next import screen_next
from wiki_bridge.stats_rigor import check_stats_rigor
from wiki_bridge.survey_write import build_survey_draft


def test_relevance_score_and_gather():
    q = "transformer attention retrieval"
    assert relevance_score(q, "Transformers use attention for retrieval tasks.") >= 3.0
    assert relevance_score(q, "Cooking pasta with tomato sauce.") < 3.0
    out = gather_evidence(
        q,
        [
            {
                "title": "good",
                "abstract": "We study transformer attention for dense retrieval benchmarks.",
            },
            {"title": "noise", "abstract": "A recipe for tomato pasta."},
        ],
        cutoff=3.0,
    )
    assert out["kept_n"] >= 1
    assert out["evidences"][0]["relevance_score"] >= 3.0


def test_ground_respects_relevance_cutoff():
    evs = [
        {"eid": "E1", "quote": "ok", "relevance_score": 8.0, "paper_path": "a"},
        {"eid": "E2", "quote": "weak", "relevance_score": 1.0, "paper_path": "b"},
    ]
    out = ground_answer("Claim holds (E1).", evs, relevance_cutoff=3.0)
    assert out["has_successful_answer"]
    out2 = ground_answer("Claim holds (E2).", evs, relevance_cutoff=3.0)
    assert out2["cannot_answer"] or "E2" in (out2.get("unknown_citations") or [])


def test_stats_rigor_flags_bare_float():
    bad = "# Results\n\nWe achieve accuracy 92.5 on the test set.\n"
    assert check_stats_rigor(bad)["ok"] is False
    good = "# Results\n\nWe achieve accuracy 92.5 ± 0.3 over 5 seeds.\n"
    assert check_stats_rigor(good)["ok"] is True


def test_survey_draft_outline_merge():
    papers = [
        {"title": "Survey of foundations", "abstract": "A survey and taxonomy of foundations."},
        {"title": "New method X", "abstract": "We propose a novel method for ranking."},
        {"title": "Benchmark Y", "abstract": "A new evaluation benchmark and dataset."},
        {"title": "Clinical application", "abstract": "Application in clinical NLP."},
    ]
    out = build_survey_draft(papers, chunk_size=2, rag_k=2)
    assert out["section_n"] >= 1
    assert "Related Work" in out["markdown"]


def test_novelty_blocks_near_duplicate():
    idea = "We propose transformer attention for dense retrieval"
    papers = [
        {
            "title": "Dense retrieval with transformers",
            "abstract": "We propose transformer attention for dense retrieval benchmarks.",
        }
    ]
    out = novelty_against_corpus(idea, papers, high_overlap=5.0)
    assert out["novel"] is False


def test_fig_review_orphan_ref():
    md = "As shown in Figure 2, accuracy rises.\n\n**Figure 1.** Accuracy curve.\n"
    out = review_figures(md)
    assert out["issue_n"] >= 1


def test_deep_research_followups():
    papers = [{"title": "Paper A on RAG", "abstract": "Retrieval augmented generation limits."}]
    out = build_deep_research_plan("RAG evaluation", papers, max_depth=2, breadth=2)
    assert out["next_queries"]


def test_research_session_roundtrip(tmp_path):
    created = rs.create_session(tmp_path, topic="t", sources=[{"title": "p1"}])
    rid = created["research_id"]
    src = rs.get_sources(tmp_path, rid)
    assert src["ok"] and len(src["sources"]) == 1
    rep = rs.write_report_payload(tmp_path, rid)
    assert rep["ok"] and rep["research_id"] == rid


def test_screen_next_al_hybrid():
    cands = [
        {"title": "neural ranking for retrieval", "abstract": "dense retrieval neural"},
        {"title": "cooking pasta recipes", "abstract": "tomato sauce pasta"},
        {"title": "learning to rank neural", "abstract": "neural LTR retrieval"},
    ]
    labels = {"neural ranking for retrieval": 1, "cooking pasta recipes": 0}
    out = screen_next(cands, labels, batch_size=1, strategy="hybrid")
    assert out["batch_n"] == 1
    assert "learning" in (out["batch"][0].get("title") or "").lower()


def test_repro_and_exp_reflect():
    skill_exp = ROOT.parents[1] / "skill-exp"
    assert skill_exp.is_dir(), skill_exp
    sys.path.insert(0, str(skill_exp))
    from reference.exp_reflect import build_findings
    from reference.repro_design import default_design, double_exec_check, validate_design

    d = default_design("F1")
    assert validate_design(d)["ok"]
    ok = double_exec_check({"F1": 0.80}, {"F1": 0.801}, metric="F1", max_rel_diff=0.02)
    assert ok["ok"]
    bad = double_exec_check({"F1": 0.80}, {"F1": 0.90}, metric="F1", max_rel_diff=0.02)
    assert bad["ok"] is False

    with tempfile.TemporaryDirectory() as td:
        exp = Path(td)
        (exp / "metrics").mkdir()
        (exp / "metrics" / "summary.json").write_text(
            json.dumps({"primary_metric": "F1", "primary_value": 0.8, "target_met": False}),
            encoding="utf-8",
        )
        out = build_findings(exp, hypothesis="h")
        assert Path(out["findings_path"]).is_file()
