"""Full-text search over wiki pages."""
from __future__ import annotations

from pathlib import Path

from app.services import content_root, deleted_store
from app.services import paths as pathutil
from app.services.parser import parse_frontmatter


def search_pages(query: str, limit: int = 50) -> list[dict]:
    q = (query or "").strip().lower()
    if not q:
        return []
    results = []
    root = content_root.wiki_pages_dir()
    for path in root.rglob("*.md"):
        if not pathutil.is_paper_md(path, root):
            continue
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        rel = pathutil.file_to_page_path(path, root)
        if deleted_store.is_deleted(
            arxiv=str(meta.get("arxiv") or ""),
            title=str(meta.get("title") or ""),
            path=rel,
        ):
            continue
        blob = f"{rel}\n{meta}\n{body}".lower()
        if q not in blob:
            continue
        results.append(
            {
                "path": rel,
                "title": meta.get("title") or Path(rel).name,
                "status": meta.get("status"),
                "snippet": _snippet(body, q),
            }
        )
        if len(results) >= limit:
            break
    return results


def _snippet(body: str, q: str, width: int = 120) -> str:
    low = body.lower()
    i = low.find(q)
    if i < 0:
        return body[:width].replace("\n", " ")
    start = max(0, i - 40)
    end = min(len(body), i + width)
    return body[start:end].replace("\n", " ")
