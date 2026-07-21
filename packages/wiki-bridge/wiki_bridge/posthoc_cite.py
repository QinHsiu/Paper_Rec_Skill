"""Post-hoc attribution: bind uncited claim sentences to evidence pool."""
from __future__ import annotations

import re
from typing import Any

from .claim_ledger import extract_citations
from .evidence_ground import abstract_supports_claim

_SENT_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")


def _looks_like_claim(sentence: str) -> bool:
    s = sentence.strip()
    if len(s) < 40:
        return False
    if s.startswith("#") or s.startswith("|"):
        return False
    low = s.lower()
    return any(
        w in low
        for w in (
            "show",
            "propose",
            "achieve",
            "outperform",
            "demonstrate",
            "we ",
            "our ",
            "表明",
            "提出",
            "优于",
        )
    ) or bool(re.search(r"\d", s))


def posthoc_attribute(
    markdown: str,
    evidences: list[dict[str, Any]],
    *,
    max_sentences: int = 20,
    min_overlap: int = 3,
) -> dict[str, Any]:
    """For claim-like sentences without cites, try Yes-overlap against evidence abstracts."""
    body = re.sub(r"```[\s\S]*?```", " ", markdown or "")
    suggestions: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    n = 0
    for para in re.split(r"\n\s*\n", body):
        for sent in _SENT_SPLIT.split(para.strip()):
            sent = sent.strip()
            if not _looks_like_claim(sent):
                continue
            n += 1
            if n > max_sentences:
                break
            if extract_citations(sent):
                continue
            best = None
            best_score = 0
            for i, ev in enumerate(evidences or [], start=1):
                if not isinstance(ev, dict):
                    continue
                abs_ = str(
                    ev.get("abstract")
                    or ev.get("summary")
                    or ev.get("quote")
                    or ev.get("text")
                    or ""
                )
                r = abstract_supports_claim(sent, abs_, min_overlap=min_overlap)
                score = int(r.get("overlap_n") or 0)
                if r.get("supported") and score > best_score:
                    best_score = score
                    eid = str(ev.get("eid") or ev.get("id") or f"E{i}")
                    best = {
                        "sentence": sent[:400],
                        "suggested_cite": eid,
                        "overlap_n": score,
                        "paper_path": ev.get("paper_path") or ev.get("title"),
                    }
            if best:
                suggestions.append(best)
            else:
                gaps.append({"sentence": sent[:400], "status": "needs_attribution"})
        if n > max_sentences:
            break

    return {
        "scanned_claims": n,
        "attributed": suggestions,
        "attributed_n": len(suggestions),
        "needs_attribution": gaps,
        "needs_attribution_n": len(gaps),
    }
