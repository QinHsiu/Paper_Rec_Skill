"""Strip journal-rank intent from queries (paper-search-pro inspired).

Fixes ``中科院一区 情绪调节`` searching *about* CAS tier-1 instead of filtering
topic ``情绪调节``. Pure regex — no network.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

_CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "1": 1, "2": 2, "3": 3, "4": 4}
_CN_NUM_CLASS = "一二三四1234"

_PLATFORM_QUARTILE_RE = re.compile(
    r"(?i)\b(jcr|sjr|scimago|wos|web of science)\b\s*[\"']?(Q?[1-4]|["
    + _CN_NUM_CLASS
    + r"]区)[\"']?"
)
_CAS_PHRASE_RE = re.compile(
    r"(?:中科院|科院分区|科院|CAS)\s*(?:分区)?\s*([" + _CN_NUM_CLASS + r"]{1,2})\s*区?"
)
_CAS_BARE_TIER_RE = re.compile(r"(?<![A-Za-z0-9])([" + _CN_NUM_CLASS + r"]{1,2})\s*区(?![A-Za-z])")
_BARE_QUARTILE_RE = re.compile(r"(?i)(?<![A-Za-z0-9])Q([1-4])(?![A-Za-z0-9])")
_TOP_RE = re.compile(r"(?i)顶刊|顶级期刊|top[- ]?(?:tier\s+)?journals?|top[- ]?venue")
_LANG_MARKERS_RE = re.compile(
    r"(?i)中文文献|英文文献|仅中文|仅英文|CSSCI|知网|都要|中英文|"
    r"\bChinese(?:\s+only)?\b|\bEnglish(?:\s+only)?\b|\bbilingual\b"
)


@dataclass
class RankIntent:
    platform: str | None = None  # cas | jcr | sjr
    tiers: list[int] = field(default_factory=list)
    quartiles: list[str] = field(default_factory=list)
    top: bool = False
    ambiguous: bool = False
    cleaned_query: str = ""
    matched: list[str] = field(default_factory=list)
    candidate_platforms: list[str] = field(default_factory=list)
    language_scope: str | None = None  # en | zh | both
    language_markers: list[str] = field(default_factory=list)

    @property
    def has_filter(self) -> bool:
        return bool(self.tiers or self.quartiles or self.top)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["has_filter"] = self.has_filter
        return d


def _tiers_from_run(run: str) -> list[int]:
    out: list[int] = []
    for ch in run:
        n = _CN_NUM.get(ch)
        if n and n not in out:
            out.append(n)
    return out


def _norm_q(tok: str) -> str | None:
    t = tok.strip().upper()
    if re.fullmatch(r"Q[1-4]", t):
        return t
    m = re.fullmatch(r"([" + _CN_NUM_CLASS + r"])区", tok.strip())
    if m:
        n = _CN_NUM.get(m.group(1))
        return f"Q{n}" if n else None
    if t in {"1", "2", "3", "4"}:
        return f"Q{t}"
    return None


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" ,;，；、")


def parse_language_scope(query: str) -> tuple[str | None, list[str], str]:
    """Return (scope, matched markers, cleaned). scope: en|zh|both|None."""
    matched: list[str] = []
    work = query
    scope: str | None = None
    for m in _LANG_MARKERS_RE.finditer(query):
        matched.append(m.group(0))
        low = m.group(0).lower()
        if any(x in low for x in ("中文", "cssci", "知网", "chinese")) and "英" not in low:
            scope = "zh" if scope != "both" else "both"
        elif any(x in low for x in ("英文", "english")) and "中" not in low:
            scope = "en" if scope != "both" else "both"
        elif any(x in low for x in ("都要", "中英文", "bilingual")):
            scope = "both"
    if matched:
        work = _LANG_MARKERS_RE.sub(" ", work)
    return scope, matched, _collapse(work)


def parse_rank_intent(query: str | None) -> RankIntent:
    intent = RankIntent(cleaned_query=(query or "").strip())
    if not query or not query.strip():
        return intent

    lang, lang_m, work0 = parse_language_scope(query)
    intent.language_scope = lang
    intent.language_markers = lang_m

    work = work0
    matched: list[str] = []
    platform: str | None = None
    tiers: list[int] = []
    quartiles: list[str] = []

    for m in list(_PLATFORM_QUARTILE_RE.finditer(work)):
        plat_raw = m.group(1).lower()
        if "sjr" in plat_raw or "scimago" in plat_raw:
            platform = platform or "sjr"
        else:
            platform = platform or "jcr"
        q = _norm_q(m.group(2))
        if q and q not in quartiles:
            quartiles.append(q)
        matched.append(m.group(0))
    work = _PLATFORM_QUARTILE_RE.sub(" ", work)

    for m in list(_CAS_PHRASE_RE.finditer(work)):
        these = _tiers_from_run(m.group(1))
        if these:
            platform = platform or "cas"
            for t in these:
                if t not in tiers:
                    tiers.append(t)
            matched.append(m.group(0))
    work = _CAS_PHRASE_RE.sub(" ", work)

    for m in list(_CAS_BARE_TIER_RE.finditer(work)):
        these = _tiers_from_run(m.group(1))
        if these:
            platform = platform or "cas"
            for t in these:
                if t not in tiers:
                    tiers.append(t)
            matched.append(m.group(0))
    work = _CAS_BARE_TIER_RE.sub(" ", work)

    for m in list(_BARE_QUARTILE_RE.finditer(work)):
        q = f"Q{m.group(1)}"
        if q not in quartiles:
            quartiles.append(q)
        matched.append(m.group(0))
    work = _BARE_QUARTILE_RE.sub(" ", work)

    top = False
    for m in list(_TOP_RE.finditer(work)):
        top = True
        matched.append(m.group(0))
    work = _TOP_RE.sub(" ", work)

    ambiguous = False
    candidates: list[str] = []
    if (quartiles or top) and not platform:
        ambiguous = True
        candidates = ["jcr", "sjr"] if quartiles else ["cas", "jcr", "sjr"]
    if tiers and not platform:
        platform = "cas"

    intent.platform = platform
    intent.tiers = tiers
    intent.quartiles = quartiles
    intent.top = top
    intent.ambiguous = ambiguous
    intent.matched = matched + lang_m
    intent.candidate_platforms = candidates
    intent.cleaned_query = _collapse(work) or _collapse(work0) or query.strip()
    return intent
