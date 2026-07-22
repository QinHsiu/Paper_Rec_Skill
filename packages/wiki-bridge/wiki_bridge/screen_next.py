"""Active screening: next batch from accept/skip labels (cheap hybrid querier)."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

_TOKEN = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "") if len(t) > 1]


def _doc(item: dict[str, Any]) -> str:
    return " ".join(
        str(item.get(k) or "")
        for k in ("title", "abstract", "summary", "venue")
    )


def _key(item: dict[str, Any]) -> str:
    return str(
        item.get("rrf_key")
        or item.get("doi")
        or item.get("paper_path")
        or item.get("id")
        or item.get("title")
        or id(item)
    )


def build_label_map(feedback_events: list[dict[str, Any]]) -> dict[str, int]:
    """Map path/title → 1 (accept/pin) or 0 (skip)."""
    labels: dict[str, int] = {}
    for ev in feedback_events or []:
        if not isinstance(ev, dict):
            continue
        action = str(ev.get("action") or ev.get("type") or "").lower()
        path = str(ev.get("path") or ev.get("paper_path") or ev.get("target") or "").strip()
        if not path:
            continue
        if action in {"accept", "pin", "relevant", "include"}:
            labels[path] = 1
        elif action in {"skip", "reject", "irrelevant", "exclude"}:
            labels[path] = 0
    return labels


def _tfidf_weights(docs: list[list[str]]) -> Counter[str]:
    """Very small IDF-weighted centroid for labeled classes."""
    df: Counter[str] = Counter()
    for toks in docs:
        df.update(set(toks))
    n = max(1, len(docs))
    w: Counter[str] = Counter()
    for toks in docs:
        tf = Counter(toks)
        for t, c in tf.items():
            idf = math.log(1 + n / (1 + df[t]))
            w[t] += (1 + math.log(1 + c)) * idf
    return w


def _score_vs(centroid: Counter[str], toks: list[str]) -> float:
    if not centroid or not toks:
        return 0.0
    s = sum(centroid.get(t, 0) for t in set(toks))
    return s / (1.0 + math.log1p(len(toks)))


def screen_next(
    candidates: list[dict[str, Any]],
    labels: dict[str, int],
    *,
    batch_size: int = 10,
    strategy: str = "hybrid",
    consecutive_irrelevant_stop: int = 10,
) -> dict[str, Any]:
    """Rank unlabeled candidates; hybrid = mix high-rel + uncertain."""
    pos_docs = []
    neg_docs = []
    labeled_keys: set[str] = set()
    for item in candidates or []:
        if not isinstance(item, dict):
            continue
        k = _key(item)
        path = str(item.get("paper_path") or item.get("path") or "")
        lab = labels.get(k)
        if lab is None and path:
            lab = labels.get(path)
        if lab is None:
            # fuzzy: any label key substring of title
            title = str(item.get("title") or "")
            for lk, lv in labels.items():
                if lk and (lk in path or lk in title or path.endswith(lk)):
                    lab = lv
                    break
        if lab is None:
            continue
        labeled_keys.add(k)
        toks = tokenize(_doc(item))
        (pos_docs if lab == 1 else neg_docs).append(toks)

    consec = 0
    # walk labels in insertion order of events if provided as list values — use last N skips
    # approximate: if more skips than accepts recently — caller passes consecutive via labels meta
    consecutive_skips = sum(1 for v in labels.values() if v == 0)
    consecutive_accepts = sum(1 for v in labels.values() if v == 1)
    stop = consecutive_skips >= consecutive_irrelevant_stop and consecutive_accepts == 0

    pos_c = _tfidf_weights(pos_docs)
    neg_c = _tfidf_weights(neg_docs)

    unscored: list[tuple[float, float, dict[str, Any]]] = []
    for item in candidates or []:
        if not isinstance(item, dict):
            continue
        k = _key(item)
        if k in labeled_keys:
            continue
        toks = tokenize(_doc(item))
        pos_s = _score_vs(pos_c, toks)
        neg_s = _score_vs(neg_c, toks)
        rel = pos_s - 0.5 * neg_s
        # uncertainty: close scores
        unc = 1.0 / (1.0 + abs(pos_s - neg_s))
        unscored.append((rel, unc, item))

    if not pos_docs and not neg_docs:
        # cold start: return first batch as-is
        batch = [dict(c) for c in (candidates or [])[:batch_size] if isinstance(c, dict)]
        return {
            "strategy": strategy,
            "batch": batch,
            "batch_n": len(batch),
            "labeled_n": 0,
            "unlabeled_n": len(candidates or []),
            "stopped": False,
            "stop_reason": None,
            "cold_start": True,
        }

    if stop:
        return {
            "strategy": strategy,
            "batch": [],
            "batch_n": 0,
            "labeled_n": len(labeled_keys),
            "unlabeled_n": len(unscored),
            "stopped": True,
            "stop_reason": "n_consecutive_irrelevant",
            "cold_start": False,
        }

    strategy = (strategy or "hybrid").lower()
    if strategy == "max":
        unscored.sort(key=lambda x: x[0], reverse=True)
        chosen = [x[2] for x in unscored[:batch_size]]
    elif strategy == "uncertainty":
        unscored.sort(key=lambda x: x[1], reverse=True)
        chosen = [x[2] for x in unscored[:batch_size]]
    else:
        # hybrid: half max, half uncertainty
        by_rel = sorted(unscored, key=lambda x: x[0], reverse=True)
        by_unc = sorted(unscored, key=lambda x: x[1], reverse=True)
        half = max(1, batch_size // 2)
        seen: set[int] = set()
        chosen = []
        for pool in (by_rel[:half], by_unc):
            for _, _, item in pool:
                i = id(item)
                if i in seen:
                    continue
                seen.add(i)
                chosen.append(item)
                if len(chosen) >= batch_size:
                    break
            if len(chosen) >= batch_size:
                break

    return {
        "strategy": strategy,
        "batch": chosen,
        "batch_n": len(chosen),
        "labeled_n": len(labeled_keys),
        "unlabeled_n": len(unscored),
        "stopped": False,
        "stop_reason": None,
        "cold_start": False,
        "pos_n": len(pos_docs),
        "neg_n": len(neg_docs),
    }
