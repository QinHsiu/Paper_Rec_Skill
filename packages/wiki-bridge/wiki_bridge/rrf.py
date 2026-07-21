"""Reciprocal Rank Fusion across retrieval lanes / sources."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


def _norm_title(title: str) -> str:
    t = (title or "").lower()
    t = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _doc_key(item: dict[str, Any]) -> str:
    """Stable merge key: OpenAlex → DOI → arXiv → normalized title."""
    oa = ""
    for key in ("openalex_id", "openalex"):
        v = item.get(key)
        if v:
            oa = str(v).strip()
            break
    ids = item.get("ids")
    if not oa and isinstance(ids, dict):
        oa = str(ids.get("openalex") or "").strip()
    if not oa:
        oid = item.get("id")
        if isinstance(oid, str) and (
            "openalex.org" in oid.lower() or oid.upper().startswith("W")
        ):
            oa = oid.strip()
    if oa:
        token = oa.rstrip("/").split("/")[-1]
        if token.upper().startswith("W"):
            return f"openalex:{token.upper()}"

    doi = str(item.get("doi") or "").strip().lower()
    if not doi:
        ext = item.get("external_ids") or item.get("externalIds") or {}
        if isinstance(ext, dict):
            doi = str(ext.get("DOI") or ext.get("doi") or "").strip().lower()
    if doi:
        doi = doi.removeprefix("https://doi.org/")
        return f"doi:{doi}"
    arxiv = str(item.get("arxiv") or item.get("arxiv_id") or "").strip().lower()
    if arxiv:
        return f"arxiv:{arxiv}"
    nt = _norm_title(str(item.get("title") or ""))
    if nt:
        return f"title:{nt}"
    return f"id:{item.get('id') or item.get('paperId') or id(item)}"


def rrf_fuse(
    lanes: dict[str, list[dict[str, Any]]],
    *,
    k: int = 60,
    top_n: int = 200,
    lane_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Fuse ranked lists with RRF. ``lanes`` maps lane/source name → ordered candidates."""
    weights = lane_weights or {}
    scores: dict[str, float] = defaultdict(float)
    meta: dict[str, dict[str, Any]] = {}
    lane_hits: dict[str, int] = {}
    contrib: dict[str, dict[str, int]] = defaultdict(dict)

    for lane, items in (lanes or {}).items():
        if not items:
            lane_hits[lane] = 0
            continue
        lane_hits[lane] = len(items)
        w = float(weights.get(lane, 1.0))
        for rank, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            key = _doc_key(item)
            scores[key] += w * (1.0 / (k + rank))
            contrib[key][lane] = rank
            if key not in meta:
                meta[key] = dict(item)
                meta[key]["_lanes"] = [lane]
            else:
                # enrich abstract/cites
                cur = meta[key]
                if len(str(item.get("abstract") or item.get("summary") or "")) > len(
                    str(cur.get("abstract") or cur.get("summary") or "")
                ):
                    if item.get("abstract"):
                        cur["abstract"] = item["abstract"]
                    if item.get("summary"):
                        cur["summary"] = item["summary"]
                cites = item.get("citationCount") or item.get("citations") or item.get("n_citations")
                if cites is not None:
                    try:
                        c = float(cites)
                        prev = cur.get("citationCount") or cur.get("citations") or 0
                        if c > float(prev or 0):
                            cur["citationCount"] = c
                    except (TypeError, ValueError):
                        pass
                lanes_list = list(cur.get("_lanes") or [])
                if lane not in lanes_list:
                    lanes_list.append(lane)
                cur["_lanes"] = lanes_list

    ranked_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    documents: list[dict[str, Any]] = []
    for key in ranked_keys[: max(1, top_n)]:
        row = dict(meta[key])
        row["rrf_score"] = round(scores[key], 6)
        row["rrf_key"] = key
        row["rrf_ranks"] = dict(contrib.get(key) or {})
        documents.append(row)

    return {
        "rrf": "on",
        "k": k,
        "top_n": top_n,
        "lane_hits": lane_hits,
        "input_n": sum(lane_hits.values()),
        "kept_n": len(documents),
        "documents": documents,
    }


def rrf_fuse_from_payload(payload: dict[str, Any] | list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    """Accept {lanes:{...}} | {sources:{...}} | flat list with ``source`` field."""
    if isinstance(payload, list):
        lanes: dict[str, list[dict[str, Any]]] = {}
        for i, item in enumerate(payload):
            src = str((item or {}).get("source") or (item or {}).get("path_id") or "default")
            lanes.setdefault(src, []).append(item)
        return rrf_fuse(lanes, **kwargs)

    lanes = payload.get("lanes") or payload.get("sources") or {}
    if lanes:
        return rrf_fuse({str(k): list(v or []) for k, v in lanes.items()}, **kwargs)

    # flat papers with source
    papers = list(payload.get("papers") or payload.get("candidates") or [])
    by_src: dict[str, list[dict[str, Any]]] = {}
    for p in papers:
        src = str(p.get("source") or p.get("path_id") or "default")
        by_src.setdefault(src, []).append(p)
    if not by_src and papers:
        by_src["default"] = papers
    return rrf_fuse(by_src, **kwargs)
