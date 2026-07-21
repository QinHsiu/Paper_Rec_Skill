"""Code-availability filter for ranked paper candidates (PaperPilot-inspired).

Modes: ``any`` (default, no filter), ``required`` (must have code URL),
``none`` (theory-only / no code link).
"""
from __future__ import annotations

import re
from typing import Any

CODE_RE = re.compile(
    r"https?://(?:www\.)?(github\.com|gitlab\.com|huggingface\.co)/[^\s)\]}>\"']+",
    re.I,
)


def extract_code_urls(*texts: str) -> list[str]:
    found: list[str] = []
    for text in texts:
        if not text:
            continue
        for m in CODE_RE.finditer(str(text)):
            url = m.group(0).rstrip(".,;:")
            if url not in found:
                found.append(url)
    return found


def annotate_code(item: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy with ``code_url`` / ``has_code`` filled when possible."""
    row = dict(item)
    existing = (
        str(row.get("code_url") or row.get("github_url") or row.get("repo_url") or "").strip()
    )
    hay = " ".join(
        str(row.get(k) or "")
        for k in ("abstract", "summary", "url", "pdf_url", "venue", "title", "note")
    )
    urls = extract_code_urls(existing, hay)
    if existing and existing not in urls:
        urls.insert(0, existing)
    if urls:
        row["code_url"] = urls[0]
        row["code_urls"] = urls
        row["has_code"] = True
    else:
        row.setdefault("has_code", bool(row.get("has_code")))
        if not row.get("has_code"):
            row["has_code"] = False
    return row


def matches_code_filter(item: dict[str, Any], mode: str) -> bool:
    mode = (mode or "any").strip().lower()
    annotated = annotate_code(item)
    has_code = bool(annotated.get("has_code")) or bool(annotated.get("code_url"))
    if mode == "required":
        return has_code
    if mode == "none":
        return not has_code
    return True  # any


def filter_by_code(
    items: list[dict[str, Any]],
    mode: str = "any",
) -> dict[str, Any]:
    """Filter candidates; always annotate ``code_url`` / ``has_code`` on kept rows."""
    mode = (mode or "any").strip().lower()
    if mode not in {"any", "required", "none"}:
        mode = "any"
    kept: list[dict[str, Any]] = []
    dropped = 0
    for raw in items or []:
        if not isinstance(raw, dict):
            continue
        ann = annotate_code(raw)
        if matches_code_filter(ann, mode):
            kept.append(ann)
        else:
            dropped += 1
    return {
        "code_filter": mode,
        "input_n": len(items or []),
        "kept_n": len(kept),
        "dropped_n": dropped,
        "documents": kept,
    }
