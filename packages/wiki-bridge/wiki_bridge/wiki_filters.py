"""Parse wiki/library query filters: +term -term dt>=YYYY file:pdf."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .conventions import parse_frontmatter
from .writer import resolve_content_root

_PLUS = re.compile(r"(?<!\S)\+(\S+)")
_MINUS = re.compile(r"(?<!\S)-(\S+)")
_DT = re.compile(r"(?<!\S)dt(>=|<=|>|<|=)(\d{4}(?:-\d{2}(?:-\d{2})?)?)")
_FILE = re.compile(r"(?<!\S)file:(\w+)", re.I)


@dataclass
class WikiQueryFilters:
    must: list[str] = field(default_factory=list)
    must_not: list[str] = field(default_factory=list)
    dt_op: str | None = None
    dt_value: str | None = None
    file_type: str | None = None
    free_text: str = ""
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_wiki_query(query: str) -> WikiQueryFilters:
    raw = query or ""
    work = raw
    must = [m.group(1) for m in _PLUS.finditer(work)]
    must_not = [m.group(1) for m in _MINUS.finditer(work)]
    dt_op = dt_value = None
    mdt = _DT.search(work)
    if mdt:
        dt_op, dt_value = mdt.group(1), mdt.group(2)
    file_type = None
    mf = _FILE.search(work)
    if mf:
        file_type = mf.group(1).lower()
    work = _PLUS.sub(" ", work)
    work = _MINUS.sub(" ", work)
    work = _DT.sub(" ", work)
    work = _FILE.sub(" ", work)
    free = re.sub(r"\s+", " ", work).strip()
    return WikiQueryFilters(
        must=must,
        must_not=must_not,
        dt_op=dt_op,
        dt_value=dt_value,
        file_type=file_type,
        free_text=free,
        raw=raw,
    )


def match_meta(meta: dict[str, Any], filters: WikiQueryFilters, *, has_fulltext: bool = False, has_pdf: bool = False) -> bool:
    blob = " ".join(
        str(meta.get(k) or "")
        for k in ("title", "authors", "venue", "abstract", "summary", "tags", "keyword")
    ).lower()
    year = str(meta.get("year") or "")[:10]
    for t in filters.must:
        if t.lower() not in blob:
            return False
    for t in filters.must_not:
        # whole-word-ish: avoid substring false positives for short tokens
        if len(t) <= 2:
            if re.search(rf"(?<!\w){re.escape(t)}(?!\w)", blob, re.I):
                return False
        elif t.lower() in blob:
            return False
    if filters.dt_value:
        if not year:
            return False
        y = year[:4]
        v = filters.dt_value[:4]
        op = filters.dt_op or ">="
        if op == ">=" and y < v:
            return False
        if op == ">" and y <= v:
            return False
        if op == "<=" and y > v:
            return False
        if op == "<" and y >= v:
            return False
        if op == "=" and y != v:
            return False
    if filters.file_type:
        ft = filters.file_type
        if ft in {"pdf"} and not has_pdf:
            return False
        if ft in {"fulltext", "md"} and not has_fulltext:
            return False
    if filters.free_text:
        for tok in filters.free_text.lower().split():
            if tok not in blob:
                return False
    return True


def iter_wiki_pages(wiki_root: Path) -> Iterator[dict[str, Any]]:
    """Yield {path, meta, body, has_pdf} for every keyword/year/slug/README.md page."""
    pages = resolve_content_root(Path(wiki_root))
    if not pages.is_dir():
        return
    for readme in sorted(pages.rglob("README.md")):
        rel = readme.relative_to(pages).parts
        if len(rel) < 4 or any(p.startswith("_") for p in rel):
            continue
        try:
            text = readme.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            meta, body = parse_frontmatter(text)
        except Exception:  # noqa: BLE001 - malformed frontmatter → body-only page
            meta, body = {}, text
        yield {
            "path": "/".join(rel[:-1]),
            "meta": meta if isinstance(meta, dict) else {},
            "body": body or "",
            "has_pdf": any(readme.parent.glob("*.pdf")),
        }


def match_reasons(meta: dict[str, Any], filters: WikiQueryFilters, *, body: str = "", fulltext: bool = False) -> list[str]:
    """Which clauses this page satisfied (only meaningful when match_meta already passed)."""
    reasons: list[str] = []
    for t in filters.must:
        reasons.append(f"must:{t}")
    for t in filters.must_not:
        reasons.append(f"not:{t}")
    if filters.dt_value:
        reasons.append(f"dt{filters.dt_op or '>='}{filters.dt_value}")
    if filters.file_type:
        reasons.append(f"file:{filters.file_type}")
    if filters.free_text:
        reasons.append(f"text:{filters.free_text}")
    if fulltext and body:
        reasons.append("scope:fulltext")
    return reasons


def _page_matches(page: dict[str, Any], filters: WikiQueryFilters, *, fulltext: bool) -> bool:
    meta = dict(page["meta"])
    if fulltext and page["body"]:
        meta["abstract"] = (str(meta.get("abstract") or "") + " " + page["body"]).strip()
    return match_meta(meta, filters, has_fulltext=fulltext and bool(page["body"]), has_pdf=bool(page["has_pdf"]))


def _year_int(raw: Any) -> int:
    try:
        return int(str(raw or "")[:4])
    except (TypeError, ValueError):
        return 0


def apply_filters(wiki_root: Path, query: str, *, fulltext: bool = False, limit: int = 50) -> dict[str, Any]:
    filters = parse_wiki_query(query)
    scanned = 0
    matched: list[dict[str, Any]] = []
    for page in iter_wiki_pages(wiki_root):
        scanned += 1
        if not _page_matches(page, filters, fulltext=fulltext):
            continue
        meta = page["meta"]
        matched.append(
            {
                "path": page["path"],
                "title": str(meta.get("title") or page["path"].split("/")[-1]),
                "year": _year_int(meta.get("year")),
                "keyword": str(meta.get("keyword") or page["path"].split("/")[0]),
                "reasons": match_reasons(meta, filters, body=page["body"], fulltext=fulltext),
            }
        )
    matched.sort(key=lambda m: (-m["year"], m["title"].lower()))
    lim = max(0, int(limit))
    return {
        "query": query,
        "filters": filters.to_dict(),
        "scanned_n": scanned,
        "matched_n": len(matched),
        "matched": matched[:lim] if lim else matched,
        "truncated": bool(lim) and len(matched) > lim,
    }
