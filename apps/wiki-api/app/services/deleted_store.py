"""Deleted-paper blacklist (tombstone table)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.services import content_root


def deleted_path() -> Path:
    p = content_root.content_dir() / "wiki" / "deleted.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_deleted() -> dict:
    path = deleted_path()
    if not path.is_file():
        return {"items": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"items": []}
    if not isinstance(data, dict):
        return {"items": []}
    data.setdefault("items", [])
    return data


def save_deleted(data: dict) -> None:
    path = deleted_path()
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def make_key(*, arxiv: str = "", title: str = "", path: str = "") -> str:
    arxiv = (arxiv or "").strip().lower()
    if arxiv:
        return f"arxiv:{arxiv}"
    title = (title or "").strip().lower()
    if title:
        return f"title:{title}"
    return f"path:{(path or '').strip().lower()}"


def is_deleted(*, arxiv: str = "", title: str = "", path: str = "") -> bool:
    keys = {
        make_key(arxiv=arxiv, title=title, path=path),
    }
    if arxiv:
        keys.add(make_key(arxiv=arxiv))
    if title:
        keys.add(make_key(title=title))
    if path:
        keys.add(make_key(path=path))
    for item in load_deleted().get("items") or []:
        if item.get("key") in keys:
            return True
        # also match raw fields
        if arxiv and (item.get("arxiv") or "").strip().lower() == arxiv.strip().lower():
            return True
        if title and (item.get("title") or "").strip().lower() == title.strip().lower():
            return True
    return False


def add_deleted(
    *,
    arxiv: str = "",
    title: str = "",
    path: str = "",
    reason: str = "user",
) -> dict:
    data = load_deleted()
    key = make_key(arxiv=arxiv, title=title, path=path)
    items = data.get("items") or []
    # upsert
    items = [i for i in items if i.get("key") != key]
    entry = {
        "key": key,
        "arxiv": arxiv or "",
        "title": title or "",
        "path": path or "",
        "deleted_at": date.today().isoformat(),
        "reason": reason or "user",
    }
    items.append(entry)
    data["items"] = items
    save_deleted(data)
    return entry


def list_deleted() -> list[dict]:
    return list(load_deleted().get("items") or [])


def remove_from_deleted(key: str) -> bool:
    data = load_deleted()
    items = data.get("items") or []
    new_items = [i for i in items if i.get("key") != key]
    if len(new_items) == len(items):
        return False
    data["items"] = new_items
    save_deleted(data)
    return True
