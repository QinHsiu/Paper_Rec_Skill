"""Markdown + YAML frontmatter + [[wikilink]] helpers."""
from __future__ import annotations

import re
from typing import Any

import yaml

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    body = parts[2].lstrip("\n")
    return meta, body


def dump_page(meta: dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    body = body.lstrip("\n")
    return f"---\n{fm}\n---\n\n{body}\n"


def extract_wikilinks(body: str) -> list[str]:
    return list(dict.fromkeys(WIKILINK_RE.findall(body)))


def slugify(title: str) -> str:
    s = re.sub(r"[^\w\s\-\u4e00-\u9fff]+", "", title, flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "-", s.strip()).strip("-").lower()
    return s or "page"
