"""Weekly digests + this-week papers from Skill sync (deduped)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from app.services import content_root
from app.services import pages_index
from app.services.parser import parse_frontmatter


def list_weeklies() -> list[dict]:
    root = content_root.weekly_dir()
    items = []
    for path in sorted(root.rglob("*.md"), reverse=True):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        rel = path.relative_to(root).as_posix()[:-3]
        items.append(
            {
                "path": rel,
                "title": meta.get("title") or path.stem,
                "week": meta.get("week"),
                "type": meta.get("type") or "general",
                "preview": body[:200],
            }
        )
    return items


def this_week_bundle() -> dict:
    start, end = pages_index.iso_week_bounds()
    papers = pages_index.papers_this_week()
    iso = start.isocalendar()
    return {
        "week": f"{iso.year}-W{iso.week:02d}",
        "from": start.isoformat(),
        "to": end.isoformat(),
        "count": len(papers),
        "papers": papers,
        "digests": list_weeklies(),
    }


def get_weekly(rel: str) -> dict:
    path = _safe(content_root.weekly_dir(), rel)
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    return {"path": rel, "meta": meta, "body": body}


def save_weekly(rel: str, meta: dict, body: str) -> dict:
    from app.services.parser import dump_page

    path = _safe(content_root.weekly_dir(), rel, create=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_page(meta or {}, body or ""), encoding="utf-8")
    return get_weekly(rel)


def _safe(root: Path, rel: str, create: bool = False) -> Path:
    rel = rel.replace("\\", "/").lstrip("/")
    if ".." in rel.split("/"):
        raise ValueError("invalid path")
    path = (root / f"{rel}.md").resolve()
    if not str(path).startswith(str(root.resolve())):
        raise ValueError("path escape")
    if not create and not path.is_file():
        raise FileNotFoundError(rel)
    return path
