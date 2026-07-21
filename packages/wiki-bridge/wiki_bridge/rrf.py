"""Reciprocal Rank Fusion across retrieval lanes / sources."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

_ARXIV_DOI_VER_RE = re.compile(r"(10\.48550/arxiv\.\d{4}\.\d{4,5})v\d+", re.I)


def _norm_title(title: str) -> str:
    t = (title or "").lower()
    t = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def normalize_doi(doi: str | None) -> str:
    """Lowercase, strip URL prefixes, normalize arXiv DOI version suffix."""
    if not doi:
        return ""
    d = str(doi).strip().lower()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if d.startswith(prefix):
            d = d[len(prefix) :]
    if "10.48550/arxiv." in d:
        d = _ARXIV_DOI_VER_RE.sub(r"\1", d)
    return d.strip()


def normalize_arxiv_id(arxiv_id: str | None) -> str:
    if not arxiv_id:
        return ""
    s = str(arxiv_id).strip()
    s = re.sub(r"^(https?://)?arxiv\.org/(abs|pdf)/", "", s, flags=re.I)
    s = re.sub(r"\.pdf$", "", s, flags=re.I)
    s = re.sub(r"v\d+$", "", s)
    return s.lower()


def _extract_doi(item: dict[str, Any]) -> str:
    doi = normalize_doi(str(item.get("doi") or "").strip())
    if doi:
        return doi
    ext = item.get("external_ids") or item.get("externalIds") or {}
    if isinstance(ext, dict):
        doi = normalize_doi(str(ext.get("DOI") or ext.get("doi") or "").strip())
    return doi


def _extract_pmid(item: dict[str, Any]) -> str:
    for key in ("pmid", "PMID"):
        v = item.get(key)
        if v:
            return str(v).strip()
    ext = item.get("external_ids") or item.get("externalIds") or {}
    if isinstance(ext, dict):
        v = ext.get("PubMed") or ext.get("PMID") or ext.get("pmid")
        if v:
            return str(v).strip()
    return ""


def _extract_openalex(item: dict[str, Any]) -> str:
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
    if not oa:
        return ""
    token = oa.rstrip("/").split("/")[-1]
    return token.upper() if token.upper().startswith("W") else ""


def _doc_key(item: dict[str, Any]) -> str:
    """Stable merge key: DOI → arXiv → PMID → OpenAlex → title(+year).

    DOI-first (paper-search-pro): avoids OpenAlex/DOI dual keys for the same paper.
    """
    doi = _extract_doi(item)
    if doi:
        return f"doi:{doi}"

    arxiv = normalize_arxiv_id(
        str(item.get("arxiv") or item.get("arxiv_id") or item.get("ArXiv") or "")
    )
    if not arxiv:
        ext = item.get("external_ids") or item.get("externalIds") or {}
        if isinstance(ext, dict):
            arxiv = normalize_arxiv_id(str(ext.get("ArXiv") or ext.get("arxiv") or ""))
    if arxiv:
        return f"arxiv:{arxiv}"

    pmid = _extract_pmid(item)
    if pmid:
        return f"pmid:{pmid}"

    oa = _extract_openalex(item)
    if oa:
        return f"openalex:{oa}"

    nt = _norm_title(str(item.get("title") or ""))
    year = str(item.get("year") or item.get("publication_year") or "").strip()[:4]
    if nt and year.isdigit():
        return f"title:{nt}|{year}"
    if nt:
        return f"title:{nt}"
    return f"id:{item.get('id') or item.get('paperId') or id(item)}"


def same_physical_paper(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """False when both have DOI/arXiv but they differ (reject false merge)."""
    da, db = _extract_doi(a), _extract_doi(b)
    if da and db and da != db:
        return False
    aa = normalize_arxiv_id(str(a.get("arxiv") or a.get("arxiv_id") or ""))
    ab = normalize_arxiv_id(str(b.get("arxiv") or b.get("arxiv_id") or ""))
    if aa and ab and aa != ab:
        return False
    return True


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
    rejected_merges = 0

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
            if key in meta and not same_physical_paper(meta[key], item):
                # E5b: same title-year key but conflicting DOI → keep separate
                key = f"{key}#dup{rejected_merges}"
                rejected_merges += 1
            scores[key] += w * (1.0 / (k + rank))
            contrib[key][lane] = rank
            if key not in meta:
                meta[key] = dict(item)
                meta[key]["_lanes"] = [lane]
            else:
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
                if not _extract_doi(cur) and _extract_doi(item):
                    cur["doi"] = item.get("doi")
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
        "rejected_merges": rejected_merges,
        "documents": documents,
    }


def rrf_fuse_from_payload(payload: dict[str, Any] | list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    """Accept {lanes:{...}} | {sources:{...}} | flat list with ``source`` field."""
    if isinstance(payload, list):
        lanes: dict[str, list[dict[str, Any]]] = {}
        for item in payload:
            src = str((item or {}).get("source") or (item or {}).get("path_id") or "default")
            lanes.setdefault(src, []).append(item)
        return rrf_fuse(lanes, **kwargs)

    lanes = payload.get("lanes") or payload.get("sources") or {}
    if lanes:
        return rrf_fuse({str(k): list(v or []) for k, v in lanes.items()}, **kwargs)

    papers = list(payload.get("papers") or payload.get("candidates") or [])
    by_src: dict[str, list[dict[str, Any]]] = {}
    for p in papers:
        src = str(p.get("source") or p.get("path_id") or "default")
        by_src.setdefault(src, []).append(p)
    if not by_src and papers:
        by_src["default"] = papers
    return rrf_fuse(by_src, **kwargs)
