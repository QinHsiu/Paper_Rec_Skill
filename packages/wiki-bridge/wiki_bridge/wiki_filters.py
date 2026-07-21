"""Parse wiki/library query filters: +term -term dt>=YYYY file:pdf."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

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
    if filters.dt_value and year:
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
