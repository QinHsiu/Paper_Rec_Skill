# evals/goldset/run_goldset.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "wiki-bridge"))

from wiki_bridge.deep_research import run_parallel_research
from wiki_bridge.feedback_edit import critique_answer
from wiki_bridge.fig_review import review_figures
from wiki_bridge.litsearch_eval import recall_at_k
from wiki_bridge.prerank import prerank
from wiki_bridge.screening_stop import StopRules, should_stop
from wiki_bridge.trust_meta import annotate_papers
from wiki_bridge.verified_registry import hard_gate
from wiki_bridge.interest_profile import build_profile, drift_report
from wiki_bridge.thread_store import score_paper_against_thread
from wiki_bridge.wiki_filters import apply_filters
from wiki_bridge.novelty_critic import run_novelty_critic
from wiki_bridge.survey_write import build_survey_draft
from wiki_bridge.writer import resolve_content_root


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    fam = case["family"]
    cid = case["id"]
    if fam == "hard_gate":
        # verified_registry expects dict[float, str] (value → metric name)
        reg = {float(v): str(k) for k, v in case["metrics"].items()}
        gate = hard_gate(case["prose"], reg)
        blocked = bool(gate.get("blocked"))
        ok = (case["expect"] == "blocked" and blocked) or (case["expect"] == "allowed" and not blocked)
        return {"id": cid, "ok": ok, "detail": gate}
    if fam == "citation_fidelity":
        fbs = critique_answer(case["query"], case["answer"], case["evidence"])
        blob = " ".join(str(f.get("feedback", "")) for f in fbs).lower()
        ok = case["expect_feedback_substring"].lower() in blob
        return {"id": cid, "ok": ok, "detail": {"feedback_n": len(fbs)}}
    if fam == "retrieval":
        # prerank() returns {"items": [...]} not a bare list
        out = prerank(case["query"], case["docs"], top_k=int(case["k"]), use_citations=False)
        ids = [str(d.get("id") or d.get("title")) for d in out.get("items") or []]
        rec = recall_at_k(ids, set(case["gold_ids"]), int(case["k"]))
        ok = rec >= float(case["min_recall"])
        return {"id": cid, "ok": ok, "detail": {"recall": rec, "ids": ids}}
    if fam == "screening_stop":
        hist = [0 if x == "irrelevant" else 1 for x in case["labels"]]
        rules = StopRules(
            n_consecutive_irrelevant=case.get("n_consecutive_irrelevant"),
            saturation_window=case.get("saturation_window"),
            saturation_max_relevant=int(case.get("saturation_max_relevant", 0)),
            min_labels_before_stop=int(case.get("min_labels_before_stop", 0)),
        )
        sd = should_stop(hist, rules)
        ok = sd["stopped"] == bool(case["expect_stop"])
        if ok and case.get("expect_reason"):
            ok = sd["reason"] == case["expect_reason"]
        return {"id": cid, "ok": ok, "detail": sd}
    if fam == "trust_meta":
        oa_map = case.get("oa") or {}
        s2_map = case.get("s2") or {}
        oa = lambda p: oa_map.get(p["doi"])
        s2 = lambda p: s2_map.get(p["doi"])
        out = annotate_papers(case["papers"], fetch_oa=oa, fetch_s2=s2, conflict_ratio=float(case.get("conflict_ratio", 0.3)))
        got = [r["trust_status"] for r in out["papers"]]
        ok = got == case["expect_status"]
        return {"id": cid, "ok": ok, "detail": {"got": got, "blocked": out["blocked_for_writing"]}}
    if fam == "fig_review":
        import os

        keys = ("OPENAI_API_KEY", "PAPER_REC_VLM_API_KEY")
        saved = {k: os.environ.pop(k) for k in keys if k in os.environ}
        try:
            out = review_figures(case["markdown"], use_vlm=case.get("use_vlm", "auto"))
        finally:
            os.environ.update(saved)
        ok = out["vlm_skipped"] == bool(case["expect_vlm_skipped"]) and out["vlm_skip_reason"] == case["expect_skip_reason"]
        return {"id": cid, "ok": ok, "detail": {k: out[k] for k in ("vlm_applied", "vlm_skipped", "vlm_skip_reason", "issue_n")}}
    if fam == "parallel_deep":
        table = case["search_results"]
        search = lambda q: table.get(q, table.get("*", []))
        out = run_parallel_research(
            case["topic"],
            search,
            seed_papers=case["seed"],
            max_concurrent=int(case["max_concurrent"]),
            breadth=int(case["breadth"]),
        )
        dois = [c.get("doi") for c in out["compressed_learnings"]]
        ok = out["ok"] and dois.count(case["dup_doi"]) == 1 and out["compressed_learnings"][0]["doi"] == case["dup_doi"]
        return {"id": cid, "ok": ok, "detail": {"lanes": len(out["lanes"]), "top": out["compressed_learnings"][:1]}}
    if fam == "wiki_filter":
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "wiki"
            for pg in case["pages"]:
                d = resolve_content_root(root) / pg["kw"] / str(pg["year"]) / pg["slug"]
                d.mkdir(parents=True)
                tags = ", ".join(pg.get("tags") or [])
                d.joinpath("README.md").write_text(
                    f"---\ntitle: {pg['title']}\nyear: {pg['year']}\ntags: [{tags}]\nkeyword: {pg['kw']}\n---\n", encoding="utf-8"
                )
            out = apply_filters(root, case["query"])
        slugs = [m["path"].split("/")[-1] for m in out["matched"]]
        ok = slugs == case["expect_slugs"] and (not out["matched"] or set(out["matched"][0]["reasons"]) == set(case["expect_reasons"]))
        return {"id": cid, "ok": ok, "detail": {"slugs": slugs, "matched_n": out["matched_n"]}}
    if fam == "drift":
        mk = lambda rows: [{"kind": "feedback", **r} for r in rows]
        older, recent = build_profile(mk(case["older"])), build_profile(mk(case["recent"]))
        rep = drift_report(older, recent)
        prof = build_profile(mk(case["older"] + case["recent"]))
        rk = case["rank"]
        ra = score_paper_against_thread(rk["thread"], title=rk["a"], profile=prof)["R"]
        rb = score_paper_against_thread(rk["thread"], title=rk["b"], profile=prof)["R"]
        first = "a" if ra > rb else "b"
        ok = case["expect_emerging_contains"] in rep["emerging"] and case["expect_fading_contains"] in rep["fading"] and first == rk["expect_first"]
        return {"id": cid, "ok": ok, "detail": {"drift": rep, "ra": ra, "rb": rb}}
    if fam == "novelty":
        out = run_novelty_critic(case["idea"], case["papers"])
        ok = True
        if "expect_verdict" in case:
            ok = ok and out["verdict"] == case["expect_verdict"]
        if "expect_verdict_in" in case:
            ok = ok and out["verdict"] in case["expect_verdict_in"]
        if "expect_novel" in case:
            ok = ok and (out["verdict"] != "duplicate") == bool(case["expect_novel"])
        if "expect_distinguishing_contains" in case:
            ok = ok and any(case["expect_distinguishing_contains"] in d for d in out["distinguishing_points"])
        return {"id": cid, "ok": ok, "detail": {"verdict": out["verdict"], "shared": out["shared_points"], "distinguishing": out["distinguishing_points"]}}
    if fam == "survey":
        base = build_survey_draft(case["papers"], chunk_size=int(case["chunk_size"]), rag_k=int(case["rag_k"]))
        hard = build_survey_draft(case["papers"], chunk_size=int(case["chunk_size"]), rag_k=int(case["rag_k"]), tau=float(case["strict_tau"]))
        ok = (
            (base["section_n"] or 0) >= int(case["default"]["expect_min_sections"])
            and base["cite_audit"]["unknown_keys"] == case["default"]["expect_unknown_keys"]
            and hard["cite_audit"]["unsupported_n"] > int(case["expect_strict_unsupported_gt"])
            and case["expect_strict_marker"] in hard["markdown"]
            and hard["ok"] is False
        )
        return {"id": cid, "ok": ok, "detail": {"section_n": base["section_n"], "base_unsupported": base["cite_audit"]["unsupported_n"], "hard_unsupported": hard["cite_audit"]["unsupported_n"]}}
    return {"id": cid, "ok": False, "detail": {"error": f"unknown family {fam}"}}


def run_all(cases_dir: Path) -> dict[str, Any]:
    results = []
    for path in sorted(cases_dir.glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        results.append(run_case(case))
    failed = [r for r in results if not r["ok"]]
    passed = [r for r in results if r["ok"]]
    return {"passed": len(passed), "failed": failed, "results": results}


def main() -> int:
    summary = run_all(Path(__file__).resolve().parent / "cases")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
