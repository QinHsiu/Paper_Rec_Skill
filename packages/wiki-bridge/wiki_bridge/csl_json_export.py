"""CSL-JSON export for Zotero / citation managers."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .conventions import parse_frontmatter, slugify
from .writer import resolve_content_root


def _authors_csl(authors: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    raw = (authors or "").strip()
    if not raw:
        return [{"literal": "Unknown"}]
    parts = re.split(r"\s+and\s+|;\s*", raw)
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if "," in p:
            family, given = [x.strip() for x in p.split(",", 1)]
            out.append({"family": family, "given": given})
        else:
            bits = p.split()
            if len(bits) == 1:
                out.append({"family": bits[0]})
            else:
                out.append({"family": bits[-1], "given": " ".join(bits[:-1])})
    return out or [{"literal": "Unknown"}]


def meta_to_csl(meta: dict[str, Any], path: str) -> dict[str, Any]:
    title = str(meta.get("title") or path)
    year = str(meta.get("year") or "").strip()[:4]
    item: dict[str, Any] = {
        "id": slugify(title, max_len=32) or path.replace("/", "-"),
        "type": "article-journal" if meta.get("venue") or meta.get("doi") else "article",
        "title": title,
        "author": _authors_csl(str(meta.get("authors") or "")),
        "note": f"wiki:{path}",
    }
    if year:
        item["issued"] = {"date-parts": [[int(year) if year.isdigit() else year]]}
    if meta.get("venue"):
        item["container-title"] = str(meta["venue"])
    if meta.get("doi"):
        item["DOI"] = str(meta["doi"]).removeprefix("https://doi.org/")
    if meta.get("url"):
        item["URL"] = str(meta["url"])
    elif meta.get("arxiv"):
        item["URL"] = f"https://arxiv.org/abs/{meta['arxiv']}"
    return item


def export_csl_json(wiki_root: Path, paths: list[str]) -> dict[str, Any]:
    pages = resolve_content_root(wiki_root)
    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    for raw in paths:
        path = raw.strip("/")
        readme = pages / path / "README.md"
        if not readme.is_file():
            warnings.append(f"missing: {path}")
            continue
        meta, _ = parse_frontmatter(readme.read_text(encoding="utf-8"))
        items.append(meta_to_csl(meta, path))
    return {
        "items": items,
        "csl_json": json.dumps(items, ensure_ascii=False, indent=2) + ("\n" if items else ""),
        "count": len(items),
        "warnings": warnings,
    }
