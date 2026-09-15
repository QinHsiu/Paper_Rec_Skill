"""Depth×breadth research tree: learnings → follow-up queries (offline structure)."""
from __future__ import annotations

import json as _json
import re
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutTimeout
from typing import Any, Callable

from .reflect_search import reflect_coverage

_WS = re.compile(r"[^a-z0-9\u4e00-\u9fff]+")


def extract_learnings(papers: list[dict[str, Any]], *, max_items: int = 8) -> list[dict[str, Any]]:
    learnings = []
    for p in papers or []:
        if not isinstance(p, dict):
            continue
        title = str(p.get("title") or "").strip()
        abs_ = str(p.get("abstract") or p.get("summary") or "").strip()
        if not title:
            continue
        snippet = abs_[:180] if abs_ else title
        learnings.append(
            {
                "learning": snippet,
                "citation": title,
                "year": p.get("year"),
                "doi": p.get("doi"),
                "paper_path": p.get("paper_path"),
            }
        )
        if len(learnings) >= max_items:
            break
    return learnings


def followups_from_learnings(learnings: list[dict[str, Any]], topic: str, *, breadth: int = 3) -> list[str]:
    qs: list[str] = []
    for L in learnings[:breadth]:
        cite = str(L.get("citation") or "prior work")
        qs.append(f"{topic} related to: {cite[:80]}")
        qs.append(f"limitations of {cite[:60]}")
    # unique preserve
    out: list[str] = []
    for q in qs:
        if q not in out:
            out.append(q)
    return out[: max(2, breadth * 2)]


def deep_research_step(
    topic: str,
    papers: list[dict[str, Any]],
    *,
    depth: int = 1,
    breadth: int = 3,
    max_depth: int = 2,
) -> dict[str, Any]:
    """One node of a deep-research tree; recurse structurally (agent runs searches)."""
    learnings = extract_learnings(papers, max_items=max(4, breadth * 2))
    coverage = reflect_coverage(papers, query=topic)
    followups = followups_from_learnings(learnings, topic, breadth=breadth)
    if coverage.get("improved_queries"):
        for q in coverage["improved_queries"]:
            if q not in followups:
                followups.append(q)
    node = {
        "topic": topic,
        "depth": depth,
        "learnings": learnings,
        "followups": followups[: breadth * 2],
        "coverage": {k: coverage[k] for k in ("issues", "should_retry", "paper_count") if k in coverage},
        "children": [],
        "complete": depth >= max_depth or not followups,
    }
    return node


def build_deep_research_plan(
    topic: str,
    papers: list[dict[str, Any]],
    *,
    max_depth: int = 2,
    breadth: int = 3,
) -> dict[str, Any]:
    root = deep_research_step(topic, papers, depth=1, breadth=breadth, max_depth=max_depth)
    # structural children stubs for agent to fill after next search wave
    if not root["complete"]:
        for q in root["followups"][:breadth]:
            root["children"].append(
                {
                    "topic": q,
                    "depth": 2,
                    "status": "pending_search",
                    "learnings": [],
                    "followups": [],
                }
            )
    return {
        "topic": topic,
        "max_depth": max_depth,
        "breadth": breadth,
        "tree": root,
        "next_queries": root.get("followups") or [],
    }


def _norm_title(t: str) -> str:
    return _WS.sub(" ", (t or "").lower()).strip()


def compress_learnings(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for lane in lanes:
        q = str(lane.get("query") or lane.get("topic") or "")
        is_parallel_lane = "query" in lane
        for L in lane.get("learnings") or []:
            key = str(L.get("doi") or "").lower() or "t:" + _norm_title(str(L.get("citation") or ""))
            if not key or key == "t:":
                continue
            if key not in merged:
                merged[key] = {
                    "learning": L.get("learning"),
                    "citation": L.get("citation"),
                    "year": L.get("year"),
                    "doi": L.get("doi"),
                    "paper_path": L.get("paper_path"),
                    "lane_hits": 0,
                    "lanes": [],
                }
                order.append(key)
            m = merged[key]
            if is_parallel_lane:
                m["lane_hits"] += 1
                if q and q not in m["lanes"]:
                    m["lanes"].append(q)
    out = [merged[k] for k in order]
    out.sort(
        key=lambda m: (
            -m["lane_hits"],
            -(int(m["year"]) if isinstance(m.get("year"), (int, float)) else 0),
            str(m.get("citation") or ""),
        )
    )
    return out


def run_parallel_research(
    topic: str,
    search_fn: Callable[[str], list[dict[str, Any]]],
    *,
    seed_papers: list[dict[str, Any]] | None = None,
    max_concurrent: int = 3,
    breadth: int = 3,
    max_depth: int = 2,
    compress: bool = True,
    timeout_per_lane: float = 60.0,
) -> dict[str, Any]:
    if max_concurrent < 1:
        raise ValueError("max_concurrent must be >= 1")
    root = deep_research_step(topic, seed_papers or [], depth=1, breadth=breadth, max_depth=max_depth)
    queries = list(root.get("followups") or [])[: max(1, breadth)]
    lanes: dict[str, dict[str, Any]] = {}
    failed: dict[str, str] = {}

    def lane(q: str) -> dict[str, Any]:
        hits = search_fn(q)
        node = deep_research_step(q, hits, depth=2, breadth=breadth, max_depth=max_depth)
        node["query"] = q
        node["hit_n"] = len(hits or [])
        return node

    with ThreadPoolExecutor(max_workers=max_concurrent) as ex:
        futs = {ex.submit(lane, q): q for q in queries}
        for fut, q in futs.items():
            try:
                lanes[q] = fut.result(timeout=timeout_per_lane)
            except _FutTimeout:
                failed[q] = "TimeoutError"
                fut.cancel()
            except Exception as exc:  # noqa: BLE001
                failed[q] = type(exc).__name__
    ordered_lanes = [lanes[q] for q in sorted(lanes)]
    failed_lanes = [{"query": q, "error": failed[q]} for q in sorted(failed)]
    compressed = compress_learnings([root] + ordered_lanes) if compress else []
    next_q: list[str] = []
    for ln in ordered_lanes:
        for fq in ln.get("followups") or []:
            if fq not in next_q and fq not in queries:
                next_q.append(fq)
    return {
        "ok": bool(ordered_lanes) or not queries,
        "topic": topic,
        "max_concurrent": max_concurrent,
        "root": root,
        "lanes": ordered_lanes,
        "failed_lanes": failed_lanes,
        "next_queries_attempted": queries,
        "compressed_learnings": compressed,
        "next_queries": next_q[: breadth * 2],
    }


def search_fn_from_command(cmd: str, *, timeout: float = 60.0) -> Callable[[str], list[dict[str, Any]]]:
    def run(q: str) -> list[dict[str, Any]]:
        proc = subprocess.run(  # noqa: S603
            cmd if isinstance(cmd, str) else shlex.join(cmd),
            input=q,
            capture_output=True,
            text=True,
            shell=True,
            timeout=timeout,
            check=True,
        )
        data = _json.loads(proc.stdout or "[]")
        if isinstance(data, dict):
            data = list(data.get("papers") or data.get("documents") or data.get("items") or [])
        return [d for d in data if isinstance(d, dict)]

    return run
