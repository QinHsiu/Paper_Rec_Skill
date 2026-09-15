"""Scientific active-learning stoppers (asreview-style) for screen-next (W1)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_POS = {"accept", "pin", "relevant", "include"}
_NEG = {"skip", "reject", "irrelevant", "exclude"}


@dataclass
class StopRules:
    n_consecutive_irrelevant: int | None = 10
    max_labels: int | None = None
    saturation_window: int | None = None
    saturation_max_relevant: int = 0
    min_labels_before_stop: int = 5


def validate_rules(rules: StopRules) -> None:
    if rules.n_consecutive_irrelevant is not None and rules.n_consecutive_irrelevant < 1:
        raise ValueError("n_consecutive_irrelevant must be >= 1 or None")
    if rules.max_labels is not None and rules.max_labels < 1:
        raise ValueError("max_labels must be >= 1 or None")
    if rules.saturation_window is not None:
        if rules.saturation_window < 1:
            raise ValueError("saturation_window must be >= 1 or None")
        if rules.saturation_max_relevant < 0 or rules.saturation_max_relevant > rules.saturation_window:
            raise ValueError("saturation_max_relevant must be within [0, saturation_window]")
    if rules.min_labels_before_stop < 0:
        raise ValueError("min_labels_before_stop must be >= 0")


def history_from_events(events: list[dict[str, Any]]) -> list[int]:
    hist: list[int] = []
    for ev in events or []:
        if not isinstance(ev, dict):
            continue
        action = str(ev.get("action") or ev.get("type") or "").lower()
        if action in _POS:
            hist.append(1)
        elif action in _NEG:
            hist.append(0)
    return hist


def should_stop(history: list[int], rules: StopRules) -> dict[str, Any]:
    validate_rules(rules)
    hist = [1 if int(x) == 1 else 0 for x in (history or [])]
    checked: list[str] = []
    n = len(hist)
    base = {"stopped": False, "reason": None, "checked": checked, "labels_n": n}
    if n < rules.min_labels_before_stop:
        checked.append("min_labels_guard")
        return base
    if rules.max_labels is not None:
        checked.append("max_labels")
        if n >= rules.max_labels:
            return {**base, "stopped": True, "reason": "max_labels"}
    if rules.n_consecutive_irrelevant is not None:
        checked.append("n_consecutive_irrelevant")
        k = rules.n_consecutive_irrelevant
        if n >= k and all(x == 0 for x in hist[-k:]):
            return {**base, "stopped": True, "reason": "n_consecutive_irrelevant"}
    if rules.saturation_window is not None:
        checked.append("saturation")
        w = rules.saturation_window
        if n >= w and sum(hist[-w:]) <= rules.saturation_max_relevant:
            return {**base, "stopped": True, "reason": "saturation"}
    return base
