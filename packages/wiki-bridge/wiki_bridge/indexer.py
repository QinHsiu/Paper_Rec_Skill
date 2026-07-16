"""Scan paper README.md files and build Reading_Index."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .conventions import parse_frontmatter
from .writer import resolve_content_root


@dataclass
class IndexedPaper:
    path: Path
    rel: str
    wiki_link: str
    meta: dict


def _is_paper_file(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    name = path.name.lower()
    if any(p.startswith("_") for p in parts):
        return False
    if name == "readme.md" and len(parts) == 1:
        return False
    if name == "readme.md" and len(parts) == 2:
        return False  # keyword README
    if name == "readme.md" and len(parts) >= 4:
        return True
    if name != "readme.md" and len(parts) >= 3:
        return True  # legacy
    return False


def iter_papers(content_root: Path) -> list[IndexedPaper]:
    root = resolve_content_root(content_root)
    out: list[IndexedPaper] = []
    for path in sorted(root.rglob("*.md")):
        if not _is_paper_file(path, root):
            continue
        text = path.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        if meta.get("type") in ("index", "weekly", "meta"):
            continue
        if path.name.lower() == "readme.md":
            wiki_link = path.relative_to(root).parent.as_posix()
        else:
            rel = path.relative_to(root).as_posix()
            wiki_link = rel[:-3] if rel.endswith(".md") else rel
        out.append(
            IndexedPaper(
                path=path,
                rel=path.relative_to(root).as_posix(),
                wiki_link=wiki_link,
                meta=meta,
            )
        )
    return out


def render_reading_index(papers: list[IndexedPaper]) -> str:
    rows = []
    for p in papers:
        m = p.meta
        status = m.get("status", "todo")
        title = m.get("title", p.path.parent.name if p.path.name.lower() == "readme.md" else p.path.stem)
        year = m.get("year", "")
        keyword = m.get("keyword", p.wiki_link.split("/")[0] if "/" in p.wiki_link else "")
        venue = m.get("venue", "")
        updated = m.get("finished_at") or m.get("started_at") or ""
        rows.append(
            f"| {status} | {title} | {keyword} | {year} | {venue} | {updated} | [[{p.wiki_link}]] |"
        )
    table = [
        "---",
        "title: Reading Index",
        "type: index",
        "status: done",
        "---",
        "",
        "# Reading Index",
        "",
        "Auto-maintained by **wiki-bridge**.",
        "",
        "| Status | Title | Keyword | Year | Venue | Updated | Page |",
        "|--------|-------|---------|------|-------|---------|------|",
    ]
    if rows:
        table.extend(rows)
    else:
        table.append("| — | *(no papers yet)* | — | — | — | — | — |")
    table.append("")
    return "\n".join(table)


def write_reading_index(content_root: Path) -> Path:
    root = resolve_content_root(content_root)
    papers = iter_papers(root)
    path = root / "_meta" / "Reading_Index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_reading_index(papers), encoding="utf-8")
    return path
