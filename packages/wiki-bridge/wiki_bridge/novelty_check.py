"""Literature novelty gate for thread/idea seeds (offline + optional OpenAlex)."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any

from .evidence_score import relevance_score, tokenize


def novelty_against_corpus(
    idea: str,
    papers: list[dict[str, Any]],
    *,
    high_overlap: float = 6.5,
) -> dict[str, Any]:
    """Compare idea text to local paper abstracts; flag near-duplicates."""
    hits = []
    for p in papers or []:
        if not isinstance(p, dict):
            continue
        text = " ".join(
            str(p.get(k) or "") for k in ("title", "abstract", "summary")
        )
        s = relevance_score(idea, text)
        if s >= high_overlap * 0.5:
            hits.append(
                {
                    "score": s,
                    "title": p.get("title"),
                    "year": p.get("year"),
                    "doi": p.get("doi"),
                    "paper_path": p.get("paper_path"),
                }
            )
    hits.sort(key=lambda x: float(x["score"]), reverse=True)
    top = hits[:8]
    blocked = any(float(h["score"]) >= high_overlap for h in top)
    return {
        "idea": idea[:500],
        "novel": not blocked,
        "decision": "not novel" if blocked else "novel",
        "hits": top,
        "hit_n": len(hits),
        "policy": f"block if any corpus hit relevance_score>={high_overlap}",
    }


def novelty_openalex(idea: str, *, mailto: str = "paper-rec@local", per_page: int = 5) -> dict[str, Any]:
    """Optional live OpenAlex search (network). Fail soft offline."""
    q = " ".join(tokenize(idea)[:12])
    if not q:
        return {"ok": False, "error": "empty_query", "hits": []}
    url = (
        "https://api.openalex.org/works?"
        + urllib.parse.urlencode(
            {"search": q, "per_page": str(per_page), "mailto": mailto}
        )
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperRecNovelty/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "hits": [], "offline": True}

    hits = []
    for w in data.get("results") or []:
        hits.append(
            {
                "title": w.get("display_name"),
                "year": w.get("publication_year"),
                "id": w.get("id"),
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "cited_by": w.get("cited_by_count"),
            }
        )
    # treat strong title token overlap as not-novel hint
    decision = novelty_against_corpus(
        idea,
        [{"title": h["title"], "abstract": h["title"]} for h in hits],
        high_overlap=7.0,
    )
    return {
        "ok": True,
        "query": q,
        "hits": hits,
        "novel": decision["novel"],
        "decision": decision["decision"],
        "local_scores": decision["hits"],
    }


def check_idea_novelty(
    idea: str,
    papers: list[dict[str, Any]] | None = None,
    *,
    use_openalex: bool = False,
    mailto: str = "paper-rec@local",
) -> dict[str, Any]:
    local = novelty_against_corpus(idea, papers or [])
    remote = novelty_openalex(idea, mailto=mailto) if use_openalex else None
    novel = local["novel"] and (remote.get("novel", True) if remote and remote.get("ok") else True)
    return {
        "novel": novel,
        "decision": "novel" if novel else "not novel",
        "local": local,
        "openalex": remote,
    }
