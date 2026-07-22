"""Depth×breadth research tree: learnings → follow-up queries (offline structure)."""
from __future__ import annotations

from typing import Any

from .reflect_search import reflect_coverage


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
