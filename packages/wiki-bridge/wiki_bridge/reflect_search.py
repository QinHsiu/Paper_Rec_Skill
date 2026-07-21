"""Post-retrieval coverage reflection → suggested follow-up queries."""
from __future__ import annotations

from typing import Any


def _has_code(item: dict[str, Any]) -> bool:
    return bool(
        item.get("has_code")
        or item.get("code_url")
        or item.get("github_url")
        or ("github.com" in str(item.get("abstract") or "").lower())
    )


def _has_pdf(item: dict[str, Any]) -> bool:
    return bool(item.get("pdf_url") or item.get("fulltext_path") or item.get("is_oa"))


def reflect_coverage(
    papers: list[dict[str, Any]],
    *,
    query: str = "",
    since_year: int | None = None,
    max_papers: int = 50,
    code_filter: str = "any",
) -> dict[str, Any]:
    n = len(papers or [])
    with_pdf = sum(1 for p in papers if isinstance(p, dict) and _has_pdf(p))
    with_code = sum(1 for p in papers if isinstance(p, dict) and _has_code(p))
    recent = 0
    if since_year:
        for p in papers or []:
            if not isinstance(p, dict):
                continue
            try:
                y = int(str(p.get("year") or "")[:4])
            except ValueError:
                continue
            if y >= since_year:
                recent += 1

    issues: list[str] = []
    if n < min(10, max_papers):
        issues.append("too_few_papers")
    if since_year and n and recent < max(3, n // 3):
        issues.append("too_few_recent_papers")
    if n and with_pdf / n < 0.25:
        issues.append("low_pdf_coverage")
    if code_filter == "required" and n < min(5, max_papers):
        issues.append("github_filter_too_strict")
    elif n and with_code / n < 0.2:
        issues.append("low_code_coverage")

    base = (query or "").strip() or "related work"
    improved: list[str] = []
    if issues:
        improved = [
            f"{base} survey",
            f"{base} github",
            f"{base} benchmark",
            f"{base} arxiv",
        ][:4]

    return {
        "paper_count": n,
        "papers_with_pdf_url": with_pdf,
        "papers_with_code": with_code,
        "recent_count": recent,
        "since_year": since_year,
        "code_filter": code_filter,
        "issues": issues,
        "should_retry": bool(issues and improved),
        "improved_queries": improved,
        "notes": [],
    }
