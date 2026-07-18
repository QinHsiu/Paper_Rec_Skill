"""BibTeX export from Wiki paper pages."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .conventions import parse_frontmatter, slugify
from .writer import resolve_content_root


def _cite_key(meta: dict[str, Any], path: str) -> str:
    authors = str(meta.get("authors") or "").strip()
    year = str(meta.get("year") or "nodate")[:4]
    first = "anon"
    if authors:
        first = re.split(r"[,;]| and ", authors, maxsplit=1)[0].strip().split()[-1]
        first = re.sub(r"[^A-Za-z0-9]", "", first) or "anon"
    slug = slugify(str(meta.get("title") or path.split("/")[-1]), max_len=24)
    slug = re.sub(r"[^A-Za-z0-9]", "", slug) or "paper"
    return f"{first}{year}{slug[:12]}"


def meta_to_bibtex(meta: dict[str, Any], path: str, *, warnings: list[str] | None = None) -> str:
    warnings = warnings if warnings is not None else []
    title = str(meta.get("title") or path)
    authors = str(meta.get("authors") or "").strip()
    if not authors:
        warnings.append(f"{path}: missing authors")
        authors = "Unknown"
    year = str(meta.get("year") or "").strip()
    if not year:
        warnings.append(f"{path}: missing year")
    venue = str(meta.get("venue") or "").strip()
    doi = str(meta.get("doi") or "").strip()
    url = str(meta.get("url") or "").strip()
    arxiv = str(meta.get("arxiv") or "").strip()
    key = _cite_key(meta, path)
    entry_type = "article" if venue or doi else "misc"
    lines = [f"@{entry_type}{{{key},"]
    lines.append(f"  title = {{{title}}},")
    lines.append(f"  author = {{{authors}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if venue:
        lines.append(f"  journal = {{{venue}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    if url:
        lines.append(f"  url = {{{url}}},")
    elif arxiv:
        lines.append(f"  url = {{https://arxiv.org/abs/{arxiv}}},")
        lines.append(f"  eprint = {{{arxiv}}},")
        lines.append("  archivePrefix = {arXiv},")
    lines.append(f"  note = {{wiki:{path}}},")
    lines.append("}")
    return "\n".join(lines)


def export_bibtex(wiki_root: Path, paths: list[str]) -> dict[str, Any]:
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
        entries.append(meta_to_bibtex(meta, path, warnings=warnings))
    return {"bibtex": "\n\n".join(entries) + ("\n" if entries else ""), "warnings": warnings, "count": len(entries)}
