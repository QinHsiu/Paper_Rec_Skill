# evals/goldset/run_goldset.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "wiki-bridge"))

from wiki_bridge.feedback_edit import critique_answer
from wiki_bridge.litsearch_eval import recall_at_k
from wiki_bridge.prerank import prerank
from wiki_bridge.screening_stop import StopRules, should_stop
from wiki_bridge.verified_registry import hard_gate


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
