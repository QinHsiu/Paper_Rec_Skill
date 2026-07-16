"""Shared helpers for wiki page list / summary / dedupe."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

from app.services import content_root
from app.services import deleted_store
from app.services import paths as pathutil
from app.services.parser import parse_frontmatter

CORE_IDEA_RE = re.compile(
    r"##\s*Core Idea[^\n]*\n+(.*?)(?=\n##\s|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def iter_page_files() -> list[Path]:
    root = content_root.wiki_pages_dir()
    out = []
    for path in sorted(root.rglob("*.md")):
        if not pathutil.is_paper_md(path, root):
            continue
        out.append(path)
    return out


def extract_summary(meta: dict, body: str) -> str:
    for key in ("summary", "abstract", "core_idea"):
        val = meta.get(key)
        if val and str(val).strip():
            return str(val).strip()
    m = CORE_IDEA_RE.search(body or "")
    if m:
        text = re.sub(r"\s+", " ", m.group(1)).strip(" ….")
        if text and text != "…":
            return text[:280]
    for line in (body or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("-"):
            continue
        return s[:280]
    return ""


def ensure_added_at(meta: dict, path: Path) -> str:
    for key in ("added_at", "started_at"):
        val = meta.get(key)
        if val:
            return str(val)[:10]
    try:
        ts = datetime.fromtimestamp(path.stat().st_mtime)
        return ts.date().isoformat()
    except OSError:
        return date.today().isoformat()


def page_card(path: Path) -> dict:
    root = content_root.wiki_pages_dir()
    rel = pathutil.file_to_page_path(path, root)
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return {
        "path": rel,
        "title": meta.get("title") or Path(rel).name,
        "status": meta.get("status") or "todo",
        "year": meta.get("year"),
        "tags": tags,
        "keyword": meta.get("keyword") or rel.split("/")[0],
        "authors": meta.get("authors") or "",
        "venue": meta.get("venue") or "",
        "packs": meta.get("packs") or "",
        "score": meta.get("score") or "",
        "rating": meta.get("rating") or "",
        "summary": extract_summary(meta, body),
        "added_at": ensure_added_at(meta, path),
        "arxiv": meta.get("arxiv") or "",
        "url": meta.get("url") or "",
        "query_ref": meta.get("query_ref") or "",
        "meta": meta,
        "body": body,
    }


def dedupe_key(card: dict) -> str:
    return deleted_store.make_key(
        arxiv=card.get("arxiv") or "",
        title=card.get("title") or "",
        path=card.get("path") or "",
    )


def iso_week_bounds(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end


def parse_day(s: str) -> date | None:
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def papers_this_week() -> list[dict]:
    start, end = iso_week_bounds()
    seen: set[str] = set()
    items: list[dict] = []
    for path in iter_page_files():
        card = page_card(path)
        if deleted_store.is_deleted(
            arxiv=card.get("arxiv") or "",
            title=card.get("title") or "",
            path=card.get("path") or "",
        ):
            continue
        day = parse_day(card["added_at"])
        if not day or day < start or day > end:
            continue
        key = dedupe_key(card)
        if key in seen:
            continue
        seen.add(key)
        items.append({k: v for k, v in card.items() if k not in ("meta", "body")})
    items.sort(key=lambda x: x.get("added_at") or "", reverse=True)
    return items


def list_all_papers() -> list[dict]:
    items = []
    for path in iter_page_files():
        card = page_card(path)
        if deleted_store.is_deleted(
            arxiv=card.get("arxiv") or "",
            title=card.get("title") or "",
            path=card.get("path") or "",
        ):
            continue
        items.append({k: v for k, v in card.items() if k not in ("meta", "body")})
    return items
