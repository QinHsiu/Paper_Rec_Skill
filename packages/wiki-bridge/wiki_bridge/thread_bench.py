"""Thread-Bench — evaluate Thread-conditioned ranking (not daily-rec PaperFlow-Bench)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import thread_store as ts


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def discover_cases(bench_root: Path) -> list[Path]:
    root = Path(bench_root)
    cases_dir = root / "cases"
    if not cases_dir.is_dir():
        return []
    out = []
    for d in sorted(cases_dir.iterdir()):
        if d.is_dir() and (d / "thread.json").is_file() and (d / "pool.jsonl").is_file():
            out.append(d)
    return out


def rank_pool(thread: dict[str, Any], pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for p in pool:
        scored = ts.score_paper_against_thread(
            thread,
            title=str(p.get("title") or ""),
            summary=str(p.get("summary") or p.get("abstract") or ""),
            tags=list(p.get("tags") or []),
            keyword=str(p.get("keyword") or ""),
        )
        row = dict(p)
        row["R"] = scored.get("R", 0.0)
        row["rationale"] = scored.get("rationale") or []
        row["claim_hits_pred"] = scored.get("claim_ids") or []
        row["gap_refs_pred"] = scored.get("gap_refs") or []
        ranked.append(row)
    ranked.sort(key=lambda x: float(x.get("R") or 0), reverse=True)
    return ranked


def _relevant_ids(pool: list[dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for p in pool:
        pid = str(p.get("paper_id") or p.get("id") or p.get("path") or "")
        if p.get("relevant") is True or float(p.get("oracle_score") or 0) >= 0.5:
            if pid:
                ids.add(pid)
    return ids


def _claim_gold(pool: list[dict[str, Any]]) -> dict[str, set[str]]:
    """claim_id -> set of paper_ids labeled as supporting that claim."""
    out: dict[str, set[str]] = {}
    for p in pool:
        pid = str(p.get("paper_id") or p.get("id") or p.get("path") or "")
        for cid in p.get("gold_claims") or p.get("claim_ids") or []:
            out.setdefault(str(cid), set()).add(pid)
    return out


def _gap_gold(pool: list[dict[str, Any]]) -> dict[str, set[str]]:
    """gap key (claim_id or need) -> paper_ids that fill the gap."""
    out: dict[str, set[str]] = {}
    for p in pool:
        pid = str(p.get("paper_id") or p.get("id") or p.get("path") or "")
        for g in p.get("gold_gaps") or []:
            out.setdefault(str(g), set()).add(pid)
    return out


def metrics_at_k(
    thread: dict[str, Any],
    ranked: list[dict[str, Any]],
    pool: list[dict[str, Any]],
    *,
    k: int = 5,
) -> dict[str, Any]:
    k = max(1, int(k))
    top = ranked[:k]
    top_ids = [str(p.get("paper_id") or p.get("id") or p.get("path") or "") for p in top]
    rel = _relevant_ids(pool)
    # Recall@K among relevant
    if rel:
        hit = sum(1 for i in top_ids if i in rel)
        recall_at_k = hit / len(rel)
    else:
        recall_at_k = None

    # MRR: first relevant rank
    mrr = 0.0
    for i, pid in enumerate(top_ids, start=1):
        if pid in rel:
            mrr = 1.0 / i
            break
    if not rel:
        mrr = None

    # claim coverage@K: fraction of thread claims that have ≥1 gold paper in top-K
    claim_gold = _claim_gold(pool)
    claims = [str(c.get("id")) for c in (thread.get("claims") or []) if c.get("id")]
    if claims:
        covered = 0
        for cid in claims:
            gold = claim_gold.get(cid) or set()
            if gold & set(top_ids):
                covered += 1
        claim_coverage = covered / len(claims)
    else:
        claim_coverage = None

    # gap fill rate: fraction of gaps with a gold gap-filling paper in top-K
    gaps = thread.get("evidence_gaps") or []
    gap_gold = _gap_gold(pool)
    if gaps:
        filled = 0
        for g in gaps:
            key = str(g.get("claim_id") or g.get("need") or "")
            gold = gap_gold.get(key) or set()
            if gold & set(top_ids):
                filled += 1
        gap_fill = filled / len(gaps)
    else:
        gap_fill = None

    return {
        "k": k,
        "recall_at_k": recall_at_k,
        "mrr_at_k": mrr,
        "claim_coverage_at_k": claim_coverage,
        "gap_fill_rate_at_k": gap_fill,
        "top_ids": top_ids,
        "n_relevant": len(rel),
        "n_claims": len(claims),
        "n_gaps": len(gaps),
    }


def evaluate_case(case_dir: Path, *, k: int = 5) -> dict[str, Any]:
    case_dir = Path(case_dir)
    thread = _load_json(case_dir / "thread.json")
    pool = _load_jsonl(case_dir / "pool.jsonl")
    ranked = rank_pool(thread, pool)
    metrics = metrics_at_k(thread, ranked, pool, k=k)
    return {
        "case_id": case_dir.name,
        "thread_id": thread.get("thread_id"),
        "pool_n": len(pool),
        "metrics": metrics,
        "top": [
            {
                "paper_id": p.get("paper_id") or p.get("id") or p.get("path"),
                "title": p.get("title"),
                "R": p.get("R"),
                "relevant": p.get("relevant"),
            }
            for p in ranked[:k]
        ],
    }


def evaluate_bench(bench_root: Path, *, k: int = 5) -> dict[str, Any]:
    cases = discover_cases(bench_root)
    results = [evaluate_case(c, k=k) for c in cases]
    # macro averages (skip None)
    def _avg(key: str) -> float | None:
        vals = [r["metrics"].get(key) for r in results if r["metrics"].get(key) is not None]
        if not vals:
            return None
        return round(sum(float(v) for v in vals) / len(vals), 4)

    return {
        "bench": "thread-bench",
        "k": k,
        "n_cases": len(results),
        "macro": {
            "recall_at_k": _avg("recall_at_k"),
            "mrr_at_k": _avg("mrr_at_k"),
            "claim_coverage_at_k": _avg("claim_coverage_at_k"),
            "gap_fill_rate_at_k": _avg("gap_fill_rate_at_k"),
        },
        "cases": results,
    }
