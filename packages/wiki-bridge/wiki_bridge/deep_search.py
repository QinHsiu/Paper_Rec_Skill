"""Live Search → Read → Reason loop (injectable Searcher / Reasoner)."""
from __future__ import annotations

from typing import Any, Protocol, TypedDict

from .deep_research import extract_learnings, followups_from_learnings
from .reflect_search import reflect_coverage
from .rrf import normalize_arxiv_id, normalize_doi


class PaperHit(TypedDict):
    title: str
    abstract: str
    arxiv: str
    doi: str
    year: str
    source_query: str
    url: str


def paper_id(hit: dict[str, Any]) -> str:
    arxiv = normalize_arxiv_id(str(hit.get("arxiv") or hit.get("id") or ""))
    if arxiv:
        return f"arxiv:{arxiv}"
    doi = normalize_doi(str(hit.get("doi") or ""))
    if doi:
        return f"doi:{doi}"
    title = " ".join(str(hit.get("title") or "").split()).lower()
    return f"title:{title}" if title else "title:"


class Searcher(Protocol):
    def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]: ...


class FakeSearcher:
    def __init__(self, table: dict[str, list[dict[str, Any]]]):
        self.table = table
        self.calls: list[str] = []

    def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        self.calls.append(query)
        rows = list(self.table.get(query) or [])
        return rows[:limit]


def _normalize_hit(hit: dict[str, Any], *, source_query: str) -> dict[str, Any]:
    out = dict(hit)
    out["title"] = str(hit.get("title") or "").strip()
    out["abstract"] = str(hit.get("abstract") or hit.get("summary") or "").strip()
    out["arxiv"] = normalize_arxiv_id(str(hit.get("arxiv") or ""))
    out["doi"] = str(hit.get("doi") or "").strip()
    out["year"] = str(hit.get("year") or (hit.get("published") or "")[:4])
    out["url"] = str(hit.get("url") or hit.get("paper_link") or "")
    out["source_query"] = source_query
    return out


def search_round(
    searcher: Searcher,
    queries: list[str],
    *,
    seen_ids: set[str] | None = None,
    limit_per_query: int = 8,
) -> tuple[list[dict[str, Any]], set[str]]:
    seen = set(seen_ids or [])
    new_hits: list[dict[str, Any]] = []
    for q in queries:
        q = (q or "").strip()
        if not q:
            continue
        for raw in searcher.search(q, limit=limit_per_query) or []:
            if not isinstance(raw, dict):
                continue
            hit = _normalize_hit(raw, source_query=q)
            pid = paper_id(hit)
            if not hit["title"] or pid in seen:
                continue
            seen.add(pid)
            new_hits.append(hit)
    return new_hits, seen


def clip_followups(followups: list[str], *, breadth: int) -> list[str]:
    out: list[str] = []
    for q in followups or []:
        q = str(q or "").strip()
        if q and q not in out:
            out.append(q)
        if len(out) >= max(1, breadth):
            break
    return out


class Reasoner(Protocol):
    def reason(
        self,
        topic: str,
        round_papers: list[dict[str, Any]],
        all_learnings: list[dict[str, Any]],
        *,
        breadth: int,
        round_index: int,
        max_depth: int,
    ) -> dict[str, Any]: ...


class HeuristicReasoner:
    def reason(
        self,
        topic: str,
        round_papers: list[dict[str, Any]],
        all_learnings: list[dict[str, Any]],
        *,
        breadth: int,
        round_index: int,
        max_depth: int,
    ) -> dict[str, Any]:
        learnings = extract_learnings(round_papers, max_items=max(4, breadth * 2))
        coverage = reflect_coverage(round_papers, query=topic)
        followups = followups_from_learnings(learnings, topic, breadth=breadth)
        for q in coverage.get("improved_queries") or []:
            if q not in followups:
                followups.append(q)
        followups = clip_followups(followups, breadth=breadth)
        known_n = len(all_learnings) + len(round_papers)
        sufficient = (
            round_index >= max_depth
            or not round_papers
            or not followups
            or (not coverage.get("should_retry") and known_n >= 8)
        )
        return {
            "learnings": learnings,
            "followups": followups,
            "sufficient": sufficient,
            "coverage": {k: coverage[k] for k in ("issues", "should_retry", "paper_count") if k in coverage},
        }


def run_deep_search(
    topic: str,
    *,
    searcher: Searcher,
    reasoner: Reasoner | None = None,
    breadth: int = 3,
    max_depth: int = 2,
    limit_per_query: int = 8,
) -> dict[str, Any]:
    reasoner = reasoner or HeuristicReasoner()
    breadth = max(1, int(breadth))
    max_depth = max(1, int(max_depth))
    queries = [str(topic).strip()]
    seen: set[str] = set()
    all_papers: list[dict[str, Any]] = []
    all_learnings: list[dict[str, Any]] = []
    rounds: list[dict[str, Any]] = []
    stop_reason = "max_depth"
    last_followups: list[str] = []

    for round_index in range(1, max_depth + 1):
        hits, seen = search_round(
            searcher, queries, seen_ids=seen, limit_per_query=limit_per_query
        )
        if not hits:
            stop_reason = "no_new_papers"
            break
        result = reasoner.reason(
            topic,
            hits,
            all_learnings,
            breadth=breadth,
            round_index=round_index,
            max_depth=max_depth,
        )
        all_papers.extend(hits)
        all_learnings.extend(result.get("learnings") or [])
        last_followups = list(result.get("followups") or [])
        rounds.append(
            {
                "round": round_index,
                "queries": list(queries),
                "hits": hits,
                "learnings": result.get("learnings") or [],
                "followups": last_followups,
                "sufficient": bool(result.get("sufficient")),
            }
        )
        if result.get("sufficient"):
            stop_reason = "max_depth" if round_index >= max_depth else "sufficient"
            break
        queries = last_followups
        if not queries:
            stop_reason = "no_followups"
            break
    else:
        stop_reason = "max_depth"

    return {
        "topic": topic,
        "breadth": breadth,
        "max_depth": max_depth,
        "stop_reason": stop_reason,
        "rounds": rounds,
        "papers": all_papers,
        "learnings": all_learnings,
        "followups": last_followups,
    }
