"""Citation trust metadata: retraction flags + OA/S2 citation-count conflict (W1)."""
from __future__ import annotations

import os
import re
import urllib.parse
from typing import Any, Callable

from .http_client import HttpError, HttpStatusError, Transport, get_json

Fetcher = Callable[[dict[str, Any]], dict[str, Any] | None]

_RETRACTED_TITLE = re.compile(r"(?i)^\s*(retracted|withdrawn)\b")


def paper_key(paper: dict[str, Any]) -> str:
    return str(paper.get("doi") or paper.get("arxiv_id") or paper.get("paper_path") or paper.get("title") or "")


def _doi(paper: dict[str, Any]) -> str:
    d = str(paper.get("doi") or "").strip()
    return d.replace("https://doi.org/", "").replace("http://doi.org/", "")


def openalex_fetcher(*, transport: Transport | None = None, mailto: str = "paper-rec@local") -> Fetcher:
    def fetch(paper: dict[str, Any]) -> dict[str, Any] | None:
        doi = _doi(paper)
        if not doi:
            return None
        url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='/')}?mailto={urllib.parse.quote(mailto)}"
        try:
            data = get_json(url, transport=transport)
        except HttpStatusError as exc:
            if exc.status == 404:
                return None
            raise
        if not isinstance(data, dict):
            return None
        title = str(data.get("display_name") or data.get("title") or "")
        retracted = bool(data.get("is_retracted")) or bool(_RETRACTED_TITLE.match(title)) or data.get("type") == "retraction"
        cite = data.get("cited_by_count")
        return {"cite": int(cite) if isinstance(cite, (int, float)) else None, "retracted": retracted}

    return fetch


def s2_fetcher(*, transport: Transport | None = None, api_key: str | None = None) -> Fetcher:
    key = api_key if api_key is not None else os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

    def fetch(paper: dict[str, Any]) -> dict[str, Any] | None:
        doi = _doi(paper)
        arxiv = str(paper.get("arxiv_id") or "").strip()
        if doi:
            pid = f"DOI:{doi}"
        elif arxiv:
            pid = f"ARXIV:{arxiv}"
        else:
            return None
        url = (
            "https://api.semanticscholar.org/graph/v1/paper/"
            + urllib.parse.quote(pid, safe=":/")
            + "?fields=citationCount,title,publicationTypes"
        )
        headers = {"x-api-key": key} if key else None
        try:
            data = get_json(url, headers=headers, transport=transport)
        except HttpStatusError as exc:
            if exc.status == 404:
                return None
            raise
        if not isinstance(data, dict):
            return None
        title = str(data.get("title") or "")
        retracted = bool(data.get("isRetracted")) or bool(_RETRACTED_TITLE.match(title))
        cite = data.get("citationCount")
        return {"cite": int(cite) if isinstance(cite, (int, float)) else None, "retracted": retracted}

    return fetch


def _pull(fetch: Fetcher | None, paper: dict[str, Any], tag: str, reasons: list[str]) -> dict[str, Any] | None:
    if fetch is None:
        reasons.append(f"{tag}_no_fetcher")
        return None
    try:
        res = fetch(paper)
    except HttpError as exc:
        reasons.append(f"{tag}_error:{type(exc).__name__}")
        return None
    except Exception as exc:  # noqa: BLE001
        reasons.append(f"{tag}_error:{type(exc).__name__}")
        return None
    if res is None:
        reasons.append(f"{tag}_unresolved")
    return res


def annotate_papers(
    papers: list[dict[str, Any]],
    *,
    fetch_oa: Fetcher | None = None,
    fetch_s2: Fetcher | None = None,
    conflict_ratio: float = 0.30,
    min_count_for_conflict: int = 20,
    offline: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    top_reasons: list[str] = []
    if offline:
        top_reasons.append("offline")
    for p in papers or []:
        if not isinstance(p, dict):
            continue
        reasons: list[str] = []
        oa = None if offline else _pull(fetch_oa, p, "oa", reasons)
        s2 = None if offline else _pull(fetch_s2, p, "s2", reasons)
        sources = [s for s, r in (("openalex", oa), ("s2", s2)) if r is not None]
        cite_oa = oa.get("cite") if oa else None
        cite_s2 = s2.get("cite") if s2 else None
        retracted = bool((oa or {}).get("retracted")) or bool((s2 or {}).get("retracted"))
        conflict: bool | None = None
        ratio: float | None = None
        if cite_oa is not None and cite_s2 is not None:
            mx = max(cite_oa, cite_s2)
            ratio = (abs(cite_oa - cite_s2) / mx) if mx else 0.0
            conflict = mx >= min_count_for_conflict and ratio >= conflict_ratio
        if retracted:
            status = "retracted"
        elif conflict is None:
            status = "unknown"
        elif conflict:
            status = "conflict"
        else:
            status = "ok"
        rows.append(
            {
                "key": paper_key(p),
                "title": p.get("title"),
                "trust_status": status,
                "retracted": retracted,
                "cite_oa": cite_oa,
                "cite_s2": cite_s2,
                "conflict": conflict,
                "conflict_ratio": ratio,
                "sources": sources,
                "degraded_reasons": reasons,
            }
        )
    blocked = [r["key"] for r in rows if r["trust_status"] == "retracted"]
    degraded = bool(top_reasons) or any(r["degraded_reasons"] for r in rows)
    return {
        "papers": rows,
        "retracted_n": sum(1 for r in rows if r["trust_status"] == "retracted"),
        "conflict_n": sum(1 for r in rows if r["trust_status"] == "conflict"),
        "unknown_n": sum(1 for r in rows if r["trust_status"] == "unknown"),
        "ok_n": sum(1 for r in rows if r["trust_status"] == "ok"),
        "blocked_for_writing": blocked,
        "degraded": degraded,
        "degraded_reasons": top_reasons,
        "conflict_ratio": conflict_ratio,
    }
