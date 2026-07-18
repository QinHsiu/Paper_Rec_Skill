"""Lightweight pre-ranking between multi-source recall and LLM fine-rank.

Pure Python — no heavy deps. BM25-ish lexical score + recency + optional citations.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from typing import Any

_TOKEN = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "") if len(t) > 1]


def _year_of(item: dict[str, Any]) -> int | None:
    for key in ("year", "date", "published", "published_at"):
        v = item.get(key)
        if v is None:
            continue
        s = str(v)
        m = re.search(r"(20\d{2}|19\d{2})", s)
        if m:
            return int(m.group(1))
    return None


def _doc_text(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("title") or ""),
        str(item.get("summary") or item.get("abstract") or ""),
        " ".join(str(t) for t in (item.get("tags") or [])),
        str(item.get("venue") or ""),
    ]
    return " ".join(parts)


def bm25_scores(
    query: str,
    docs: list[str],
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    """Classic BM25 over a small in-memory collection."""
    q_tokens = tokenize(query)
    if not q_tokens or not docs:
        return [0.0] * len(docs)
    tokenized = [tokenize(d) for d in docs]
    N = len(tokenized)
    avgdl = sum(len(t) for t in tokenized) / max(N, 1)
    df: Counter[str] = Counter()
    for toks in tokenized:
        df.update(set(toks))
    scores: list[float] = []
    for toks in tokenized:
        tf = Counter(toks)
        dl = len(toks) or 1
        s = 0.0
        for term in q_tokens:
            n_qi = df.get(term, 0)
            if n_qi == 0:
                continue
            idf = math.log(1 + (N - n_qi + 0.5) / (n_qi + 0.5))
            freq = tf.get(term, 0)
            s += idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * dl / avgdl))
        scores.append(s)
    return scores


def recency_boost(year: int | None, *, now_year: int | None = None) -> float:
    """Additive boost: papers within last 3 years get up to +2.0."""
    if year is None:
        return 0.0
    y = now_year or datetime.now().year
    age = y - year
    if age <= 0:
        return 2.0
    if age == 1:
        return 1.5
    if age == 2:
        return 1.0
    if age == 3:
        return 0.5
    return 0.0


def citation_boost(item: dict[str, Any]) -> float:
    """Optional weak signal — never dominate lexical match."""
    for key in ("citationCount", "citations", "cited_by", "n_citations"):
        v = item.get(key)
        if v is None:
            continue
        try:
            n = float(v)
        except (TypeError, ValueError):
            continue
        if n <= 0:
            return 0.0
        return min(1.5, math.log10(1 + n) * 0.5)
    return 0.0


def prerank(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    top_k: int = 30,
    use_citations: bool = True,
    now_year: int | None = None,
) -> dict[str, Any]:
    """Score candidates and keep Top-K for LLM fine-rank.

    Each candidate should have at least ``title``; optional ``summary``/``year``/citations.
    """
    if not candidates:
        return {
            "prerank": "on",
            "query": query,
            "input_n": 0,
            "kept_n": 0,
            "items": [],
        }
    docs = [_doc_text(c) for c in candidates]
    lexical = bm25_scores(query, docs)
    scored: list[dict[str, Any]] = []
    for i, c in enumerate(candidates):
        year = _year_of(c)
        lex = lexical[i]
        rec = recency_boost(year, now_year=now_year)
        cite = citation_boost(c) if use_citations else 0.0
        total = lex + rec + cite
        row = dict(c)
        row["prerank_score"] = round(total, 4)
        row["prerank_lexical"] = round(lex, 4)
        row["prerank_recency"] = round(rec, 4)
        row["prerank_cite"] = round(cite, 4)
        scored.append(row)
    scored.sort(key=lambda r: r["prerank_score"], reverse=True)
    kept = scored[: max(1, top_k)]
    return {
        "prerank": "on",
        "query": query,
        "input_n": len(candidates),
        "kept_n": len(kept),
        "top_k": top_k,
        "items": kept,
        "dropped_n": max(0, len(candidates) - len(kept)),
    }


def prerank_from_json(
    payload: dict[str, Any] | list[dict[str, Any]],
    *,
    query: str = "",
    top_k: int = 30,
    use_citations: bool = True,
) -> dict[str, Any]:
    if isinstance(payload, list):
        cands = payload
        q = query
    else:
        cands = list(payload.get("papers") or payload.get("candidates") or [])
        q = query or str(payload.get("query") or payload.get("original_query") or "")
    return prerank(q, cands, top_k=top_k, use_citations=use_citations)
