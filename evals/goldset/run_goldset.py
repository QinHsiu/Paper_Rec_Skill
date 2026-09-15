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
from wiki_bridge.verified_registry import hard_gate


def should_stop(labels: list[str], n: int) -> bool:
    if len(labels) < n:
        return False
    return all(x == "irrelevant" for x in labels[-n:])


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
        stopped = should_stop(case["labels"], int(case["n_consecutive_irrelevant"]))
        ok = stopped == bool(case["expect_stop"])
        return {"id": cid, "ok": ok, "detail": {"stopped": stopped}}
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
