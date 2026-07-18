"""CEBM-lite evidence levels (Oxford Centre for Evidence-Based Medicine style).

Supplement to Anaxa-parity claim→paper→citation→snippet/page→support→confidence.
Does **not** replace confidence or gate — orthogonal axis for evidence *strength of design*.
"""
from __future__ import annotations

from typing import Any

# Canonical codes (highest → lowest)
CEBM_LEVELS: tuple[str, ...] = ("1a", "1b", "2a", "2b", "3a", "3b", "4", "5")

CEBM_LABELS: dict[str, str] = {
    "1a": "Systematic review of RCTs",
    "1b": "Individual RCT",
    "2a": "Systematic review of cohort studies",
    "2b": "Individual cohort / low-quality RCT",
    "3a": "Systematic review of case-control",
    "3b": "Individual case-control",
    "4": "Case series / poor-quality studies",
    "5": "Expert opinion / mechanism / anecdote",
}

# Free-text / legacy → CEBM
_ALIASES: dict[str, str] = {
    "1a": "1a",
    "1b": "1b",
    "2a": "2a",
    "2b": "2b",
    "3a": "3a",
    "3b": "3b",
    "4": "4",
    "5": "5",
    "meta": "1a",
    "sr": "1a",
    "systematic-review": "1a",
    "systematic_review": "1a",
    "rct": "1b",
    "randomized": "1b",
    "cohort-review": "2a",
    "cohort": "2b",
    "study": "2b",
    "observational": "2b",
    "case-control-review": "3a",
    "case-control": "3b",
    "case_control": "3b",
    "case-series": "4",
    "case_series": "4",
    "case": "4",
    "expert": "5",
    "opinion": "5",
    "anecdote": "5",
    "bench": "5",
    "mechanism": "5",
}


def normalize_evidence_level(value: Any) -> str | None:
    """Return canonical CEBM code or None if empty/unknown (keep unknown as stripped text only if already code-like)."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    key = raw.lower().replace(" ", "-")
    if key in _ALIASES:
        return _ALIASES[key]
    # already like "1A"
    low = raw.lower()
    if low in CEBM_LEVELS:
        return low
    return None


def cebm_label(code: str | None) -> str:
    if not code:
        return ""
    c = normalize_evidence_level(code) or str(code).strip().lower()
    return CEBM_LABELS.get(c, str(code))


def cebm_rank(code: str | None) -> int:
    """Lower rank = stronger evidence (1a → 0). Unknown → 99."""
    c = normalize_evidence_level(code)
    if c is None:
        return 99
    try:
        return CEBM_LEVELS.index(c)
    except ValueError:
        return 99


def describe_levels() -> list[dict[str, str]]:
    return [{"code": c, "label": CEBM_LABELS[c]} for c in CEBM_LEVELS]
