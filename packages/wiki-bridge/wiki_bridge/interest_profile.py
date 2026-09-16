"""Feedback-driven interest profile + drift (W2 c_drift_watch)."""
from __future__ import annotations

import math
from typing import Any

from .thread_store import _tokenize

ACTION_WEIGHT = {"accept": 1.0, "pin": 1.5, "read": 0.5, "skip": -1.0}
_STOP = {"and", "the", "for", "with", "via", "from", "into", "using", "based", "toward", "towards"}


def _event_tokens(ev: dict[str, Any]) -> list[str]:
    path = str(ev.get("path") or "")
    slug = path.split("/")[-1].replace("-", " ").replace("_", " ")
    toks = _tokenize(" ".join([slug, str(ev.get("title") or ""), str(ev.get("note") or "")]))
    return [t for t in toks if len(t) > 1 and t not in _STOP and not t.isdigit()]


def build_profile(events: list[dict[str, Any]], *, half_life: int = 20, max_terms: int = 60) -> dict[str, Any]:
    fb = [e for e in events or [] if isinstance(e, dict) and e.get("kind") == "feedback" and e.get("action") in ACTION_WEIGHT]
    n = len(fb)
    terms: dict[str, float] = {}
    pos = neg = 0
    for idx, ev in enumerate(fb):
        age = n - 1 - idx  # 0 = most recent
        decay = 0.5 ** (age / max(1, half_life))
        w = ACTION_WEIGHT[str(ev["action"])] * decay
        if w > 0:
            pos += 1
        else:
            neg += 1
        for t in set(_event_tokens(ev)):
            terms[t] = terms.get(t, 0.0) + w
    top = sorted(terms.items(), key=lambda kv: -abs(kv[1]))[:max_terms]
    return {"terms": {k: round(v, 4) for k, v in top}, "n_events": n, "pos_n": pos, "neg_n": neg}


def profile_match(profile: dict[str, Any] | None, tokens: list[str]) -> float:
    """Normalized 0..1: positive-weight mass hit by tokens minus negative mass, clipped."""
    terms = (profile or {}).get("terms") or {}
    if not terms or not tokens:
        return 0.0
    pos_total = sum(v for v in terms.values() if v > 0)
    if pos_total <= 0:
        return 0.0
    bag = set(tokens)
    hit = sum(v for k, v in terms.items() if k in bag)
    return round(max(0.0, min(1.0, hit / pos_total)), 4)


def split_events_for_drift(events: list[dict[str, Any]], *, window: int = 20) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fb = [e for e in events or [] if isinstance(e, dict) and e.get("kind") == "feedback"]
    if len(fb) <= window:
        return [], fb
    return fb[:-window], fb[-window:]


def drift_report(prev: dict[str, Any], cur: dict[str, Any], *, top: int = 8) -> dict[str, Any]:
    a = {k: v for k, v in (prev.get("terms") or {}).items() if v > 0}
    b = {k: v for k, v in (cur.get("terms") or {}).items() if v > 0}
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    cos = dot / (na * nb) if na and nb else 0.0
    emerging = sorted((k for k in b if k not in a), key=lambda k: -b[k])[:top]
    fading = sorted((k for k in a if k not in b), key=lambda k: -a[k])[:top]
    return {
        "drift_score": round(1.0 - cos, 4),
        "emerging": emerging,
        "fading": fading,
        "stable_n": len(set(a) & set(b)),
    }
