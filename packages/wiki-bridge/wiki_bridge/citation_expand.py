"""1-hop citation expansion via Semantic Scholar (optional Crossref fallback)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .conventions import parse_frontmatter
from .writer import resolve_content_root

S2_PAPER = "https://api.semanticscholar.org/graph/v1/paper/{pid}"
S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF = "https://api.crossref.org/works/{doi}"
USER_AGENT = "PaperRecSkill/2.16 (citation-expand; mailto:local)"


def _http_get(url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> dict[str, Any]:
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY") or os.environ.get("S2_API_KEY")
    if api_key and "semanticscholar.org" in url:
        req_headers["x-api-key"] = api_key
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def paper_meta(wiki_root: Path, paper_path: str) -> dict[str, Any]:
    readme = resolve_content_root(wiki_root) / paper_path.strip("/") / "README.md"
    if not readme.is_file():
        raise FileNotFoundError(f"wiki paper not found: {paper_path}")
    meta, _ = parse_frontmatter(readme.read_text(encoding="utf-8"))
    return meta


def _resolve_s2_id(meta: dict[str, Any]) -> str | None:
    doi = str(meta.get("doi") or "").strip()
    if doi:
        return f"DOI:{doi}"
    arxiv = str(meta.get("arxiv") or "").strip()
    if arxiv:
        return f"ARXIV:{arxiv}"
    s2 = str(meta.get("s2_id") or meta.get("paperId") or "").strip()
    if s2:
        return s2
    return None


def _search_s2_by_title(title: str) -> str | None:
    q = urllib.parse.urlencode({"query": title, "limit": 1, "fields": "paperId,title,year"})
    try:
        data = _http_get(f"{S2_SEARCH}?{q}")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None
    data_list = data.get("data") or []
    if not data_list:
        return None
    return str(data_list[0].get("paperId") or "") or None


def _refs_from_s2(paper_id: str, *, limit: int = 10) -> list[dict[str, Any]]:
    fields = "title,year,citationCount,externalIds,url,abstract"
    # references of this paper
    url = (
        S2_PAPER.format(pid=urllib.parse.quote(paper_id, safe=":"))
        + f"/references?limit={limit}&fields={fields}"
    )
    try:
        data = _http_get(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Semantic Scholar request failed: {e}") from e
    out: list[dict[str, Any]] = []
    for row in data.get("data") or []:
        cited = row.get("citedPaper") or row
        if not cited or not cited.get("title"):
            continue
        ext = cited.get("externalIds") or {}
        out.append(
            {
                "title": cited.get("title"),
                "year": cited.get("year"),
                "citationCount": cited.get("citationCount"),
                "doi": ext.get("DOI"),
                "arxiv": ext.get("ArXiv"),
                "paperId": cited.get("paperId"),
                "url": cited.get("url"),
                "abstract": (cited.get("abstract") or "")[:400],
                "source": "semanticscholar",
            }
        )
        if len(out) >= limit:
            break
    return out


def _refs_from_crossref(doi: str, *, limit: int = 10) -> list[dict[str, Any]]:
    doi = doi.strip().removeprefix("https://doi.org/")
    try:
        data = _http_get(CROSSREF.format(doi=urllib.parse.quote(doi)))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Crossref request failed: {e}") from e
    msg = data.get("message") or {}
    refs = msg.get("reference") or []
    out: list[dict[str, Any]] = []
    for r in refs:
        title = r.get("article-title") or r.get("unstructured") or ""
        if not title:
            continue
        out.append(
            {
                "title": title[:300],
                "year": r.get("year"),
                "doi": r.get("DOI"),
                "source": "crossref",
            }
        )
        if len(out) >= limit:
            break
    return out


def expand_citations(
    wiki_root: Path,
    paper_path: str,
    *,
    top_k: int = 5,
    max_fetch: int = 10,
    persist: bool = True,
) -> dict[str, Any]:
    """Fetch 1-hop references for a wiki paper; optionally persist JSON beside the page."""
    top_k = max(1, min(int(top_k), 10))
    max_fetch = max(top_k, min(int(max_fetch), 10))
    meta = paper_meta(wiki_root, paper_path)
    warnings: list[str] = []
    refs: list[dict[str, Any]] = []
    provider = ""

    s2_id = _resolve_s2_id(meta)
    if not s2_id and meta.get("title"):
        s2_id = _search_s2_by_title(str(meta["title"]))
        if s2_id:
            warnings.append("resolved via S2 title search")

    if s2_id:
        try:
            refs = _refs_from_s2(s2_id, limit=max_fetch)
            provider = "semanticscholar"
        except RuntimeError as e:
            warnings.append(str(e))

    if not refs and meta.get("doi"):
        try:
            refs = _refs_from_crossref(str(meta["doi"]), limit=max_fetch)
            provider = "crossref"
        except RuntimeError as e:
            warnings.append(str(e))

    if not refs and not s2_id and not meta.get("doi"):
        warnings.append(
            "No DOI/arXiv/S2 id on page meta; add doi: or arxiv: frontmatter, or set title for search."
        )

    # Prefer highly cited / recent among fetched
    def _sort_key(r: dict[str, Any]) -> tuple:
        cites = r.get("citationCount")
        try:
            c = float(cites) if cites is not None else 0.0
        except (TypeError, ValueError):
            c = 0.0
        year = r.get("year") or 0
        try:
            y = int(year)
        except (TypeError, ValueError):
            y = 0
        return (c, y)

    refs_sorted = sorted(refs, key=_sort_key, reverse=True)
    selected = refs_sorted[:top_k]

    result: dict[str, Any] = {
        "paper_path": paper_path.strip("/"),
        "provider": provider or None,
        "s2_id": s2_id,
        "title": meta.get("title"),
        "fetched_n": len(refs),
        "top_k": top_k,
        "references": selected,
        "warnings": warnings,
        "note": "1-hop only; does not auto-ingest PDFs. Pick candidates then pdf-ingest manually.",
    }

    if persist and selected:
        d = resolve_content_root(wiki_root) / paper_path.strip("/")
        d.mkdir(parents=True, exist_ok=True)
        out = d / "citation_expand.json"
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["path"] = f"{paper_path.strip('/')}/citation_expand.json"

    return result
