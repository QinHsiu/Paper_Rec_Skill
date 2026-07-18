#!/usr/bin/env python3
"""Reproduce LitSearch eval (smoke fixture or full HF corpus)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "packages" / "wiki-bridge"
if str(BRIDGE) not in sys.path:
    sys.path.insert(0, str(BRIDGE))

from wiki_bridge.litsearch_eval import (  # noqa: E402
    evaluate,
    load_fixture,
    load_hf,
    write_result,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="LitSearch evaluation for Paper_Rec")
    p.add_argument("--fixture", action="store_true", help="offline smoke fixtures/")
    p.add_argument("--method", choices=("bm25", "prerank"), default="bm25")
    p.add_argument("--limit-queries", type=int, default=0, help="0 = all")
    p.add_argument("--top-k", type=int, default=100)
    p.add_argument("--candidate-pool", type=int, default=500, help="prerank only")
    p.add_argument(
        "--out",
        default="",
        help="write JSON (default: runs/<method>_<fixture|full>.json)",
    )
    p.add_argument("--cache-dir", default="", help="HF datasets cache")
    p.add_argument("--full-per-query", action="store_true", help="keep all per-query rows")
    args = p.parse_args(argv)

    bench = Path(__file__).resolve().parent
    if args.fixture:
        queries, corpus = load_fixture(bench / "fixtures")
        tag = "fixture"
    else:
        cache = Path(args.cache_dir) if args.cache_dir else bench / "cache"
        queries, corpus = load_hf(cache_dir=cache)
        tag = "full"

    limit = args.limit_queries or None
    result = evaluate(
        queries,
        corpus,
        method=args.method,
        top_k=args.top_k,
        limit_queries=limit,
        candidate_pool=args.candidate_pool,
    )
    result["tag"] = tag
    result["workspace_version"] = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    out = Path(args.out) if args.out else bench / "runs" / f"{args.method}_{tag}.json"
    write_result(out, result, slim=not args.full_per_query)
    print(json.dumps({"out": str(out), "metrics_mean": result["metrics_mean"], **{k: result[k] for k in ("method", "n_queries", "n_corpus", "elapsed_sec", "tag")}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
