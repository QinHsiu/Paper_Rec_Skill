"""RIS export from Wiki paper pages (paper-search-pro / Zotero-friendly)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .conventions import parse_frontmatter
from .writer import resolve_content_root


def _ris_type(meta: dict[str, Any]) -> str:
    venue = str(meta.get("venue") or "").lower()
    arxiv = str(meta.get("arxiv") or "").strip()
    if arxiv or "arxiv" in venue or "preprint" in venue:
        return "UNPD"
    return "JOUR"


def meta_to_ris(meta: dict[str, Any], path: str, *, warnings: list[str] | None = None) -> str:
    warnings = warnings if warnings is not None else []
    title = str(meta.get("title") or path).strip()
    if not title:
        warnings.append(f"{path}: missing title")
    authors = str(meta.get("authors") or "").strip()
    year = str(meta.get("year") or "").strip()[:4]
    venue = str(meta.get("venue") or "").strip()
    doi = str(meta.get("doi") or "").strip()
    url = str(meta.get("url") or "").strip()
    arxiv = str(meta.get("arxiv") or "").strip()
    abstract = str(meta.get("abstract") or meta.get("summary") or "").strip()
    lines = [f"TY  - {_ris_type(meta)}"]
    if title:
        lines.append(f"TI  - {title}")
    if authors:
        for part in re.split(r"\s+and\s+|;", authors):
            name = part.strip().strip(",")
            if name:
                lines.append(f"AU  - {name}")
    else:
        warnings.append(f"{path}: missing authors")
    if year:
        lines.append(f"PY  - {year}")
    if venue:
        lines.append(f"JO  - {venue}")
    if doi:
        lines.append(f"DO  - {doi}")
        lines.append(f"UR  - https://doi.org/{doi.removeprefix('https://doi.org/')}")
    elif url:
        lines.append(f"UR  - {url}")
    elif arxiv:
        lines.append(f"UR  - https://arxiv.org/abs/{arxiv}")
    if abstract:
        lines.append(f"AB  - {re.sub(r'\s+', ' ', abstract)}")
    lines.append(f"N1  - wiki:{path}")
    lines.append("ER  - ")
    lines.append("")
    return "\n".join(lines)


def export_ris(wiki_root: Path, paths: list[str]) -> dict[str, Any]:
    pages = resolve_content_root(wiki_root)
    entries: list[str] = []
    warnings: list[str] = []
    for raw in paths:
        path = raw.strip("/")
        readme = pages / path / "README.md"
        if not readme.is_file():
            warnings.append(f"missing: {path}")
            continue
        meta, _ = parse_frontmatter(readme.read_text(encoding="utf-8"))
        entries.append(meta_to_ris(meta, path, warnings=warnings))
    return {
        "ris": "\n".join(entries),
        "warnings": warnings,
        "count": len(entries),
    }
