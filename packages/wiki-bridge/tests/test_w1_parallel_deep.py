from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.deep_research import compress_learnings, run_parallel_research

SEED = [
    {"title": "Dense retrieval A", "abstract": "dense retrieval transformers", "doi": "10.1/a", "year": 2023},
    {"title": "Sparse retrieval B", "abstract": "bm25 sparse ranking", "doi": "10.1/b", "year": 2022},
    {"title": "Hybrid C", "abstract": "hybrid fusion rrf", "doi": "10.1/c", "year": 2024},
]


def _search_factory(delay=0.0, fail_on=None, tracker=None):
    lock = threading.Lock()
    state = {"inflight": 0, "peak": 0}

    def search(q: str):
        with lock:
            state["inflight"] += 1
            state["peak"] = max(state["peak"], state["inflight"])
        try:
            if delay:
                time.sleep(delay)
            if fail_on and fail_on in q:
                raise RuntimeError("boom")
            return [
                {"title": "Dense retrieval A", "abstract": "dup across lanes", "doi": "10.1/a", "year": 2023},
                {"title": f"Unique for {q}", "abstract": "x", "year": 2021},
            ]
        finally:
            with lock:
                state["inflight"] -= 1

    if tracker is not None:
        tracker.update(state)
    search.state = state  # type: ignore[attr-defined]
    return search


def test_compress_dedupes_by_doi_and_counts_lanes():
    lanes = [
        {"query": "q1", "learnings": [{"learning": "l", "citation": "Dense retrieval A", "doi": "10.1/a", "year": 2023}]},
        {"query": "q2", "learnings": [{"learning": "l", "citation": "Dense Retrieval A.", "doi": "10.1/a", "year": 2023}, {"learning": "m", "citation": "Other", "year": 2020}]},
    ]
    out = compress_learnings(lanes)
    assert [c["citation"] for c in out] == ["Dense retrieval A", "Other"]
    assert out[0]["lane_hits"] == 2 and out[0]["lanes"] == ["q1", "q2"]


def test_compress_dedupes_by_normalized_title_without_doi():
    lanes = [
        {"query": "q1", "learnings": [{"learning": "l", "citation": "Hybrid  Fusion: RRF", "year": 2024}]},
        {"query": "q2", "learnings": [{"learning": "l", "citation": "hybrid fusion rrf", "year": 2024}]},
    ]
    assert len(compress_learnings(lanes)) == 1


def test_parallel_respects_max_concurrent_and_is_deterministic():
    s = _search_factory(delay=0.05)
    out = run_parallel_research("retrieval", s, seed_papers=SEED, max_concurrent=2, breadth=3)
    assert out["ok"] is True
    assert s.state["peak"] <= 2
    assert [l["query"] for l in out["lanes"]] == sorted(l["query"] for l in out["lanes"])
    assert out["compressed_learnings"][0]["doi"] == "10.1/a"
    assert out["compressed_learnings"][0]["lane_hits"] == len(out["lanes"])
    out2 = run_parallel_research("retrieval", _search_factory(delay=0.0), seed_papers=SEED, max_concurrent=3, breadth=3)
    assert [l["query"] for l in out2["lanes"]] == [l["query"] for l in out["lanes"]]


def test_single_lane_failure_isolated():
    out = run_parallel_research("retrieval", _search_factory(fail_on="limitations of Dense"), seed_papers=SEED, max_concurrent=3, breadth=3)
    assert out["ok"] is True
    assert len(out["failed_lanes"]) == 1
    assert out["failed_lanes"][0]["error"] == "RuntimeError"
    assert len(out["lanes"]) + len(out["failed_lanes"]) == len(out["next_queries_attempted"])


def test_all_lanes_fail_not_ok():
    def s(q):
        raise RuntimeError("down")

    out = run_parallel_research("retrieval", s, seed_papers=SEED, max_concurrent=2, breadth=2)
    assert out["ok"] is False and out["lanes"] == [] and out["failed_lanes"]


def test_lane_timeout_recorded():
    out = run_parallel_research("retrieval", _search_factory(delay=0.3), seed_papers=SEED, max_concurrent=2, breadth=2, timeout_per_lane=0.05)
    assert out["failed_lanes"] and all(f["error"] == "TimeoutError" for f in out["failed_lanes"])
