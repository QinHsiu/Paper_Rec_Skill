from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.screening_stop import StopRules, history_from_events, should_stop, validate_rules
from wiki_bridge.screen_next import screen_next


def test_consecutive_irrelevant_stops():
    r = StopRules(n_consecutive_irrelevant=3, min_labels_before_stop=3)
    out = should_stop([1, 0, 0, 0], r)
    assert out["stopped"] is True
    assert out["reason"] == "n_consecutive_irrelevant"


def test_consecutive_not_reached_when_relevant_breaks_run():
    r = StopRules(n_consecutive_irrelevant=3, min_labels_before_stop=1)
    assert should_stop([0, 0, 1, 0, 0], r)["stopped"] is False


def test_min_labels_guard():
    r = StopRules(n_consecutive_irrelevant=2, min_labels_before_stop=5)
    assert should_stop([0, 0], r)["stopped"] is False


def test_max_labels_stops():
    r = StopRules(n_consecutive_irrelevant=None, max_labels=4, min_labels_before_stop=1)
    out = should_stop([1, 0, 1, 0], r)
    assert out["stopped"] and out["reason"] == "max_labels"


def test_saturation_window_stops():
    r = StopRules(n_consecutive_irrelevant=None, saturation_window=4, saturation_max_relevant=0, min_labels_before_stop=1)
    out = should_stop([1, 1, 0, 0, 0, 0], r)
    assert out["stopped"] and out["reason"] == "saturation"


def test_saturation_window_allows_relevant():
    r = StopRules(n_consecutive_irrelevant=None, saturation_window=4, saturation_max_relevant=0, min_labels_before_stop=1)
    assert should_stop([0, 0, 1, 0], r)["stopped"] is False


@pytest.mark.parametrize(
    "rules",
    [
        StopRules(n_consecutive_irrelevant=0),
        StopRules(saturation_window=0),
        StopRules(saturation_window=3, saturation_max_relevant=4),
        StopRules(max_labels=-1),
        StopRules(min_labels_before_stop=-2),
    ],
)
def test_invalid_rules_raise(rules):
    with pytest.raises(ValueError):
        validate_rules(rules)


def test_history_from_events_order():
    evs = [
        {"action": "skip", "path": "a"},
        {"action": "accept", "path": "b"},
        {"action": "read", "path": "c"},
        {"action": "reject", "path": "d"},
    ]
    assert history_from_events(evs) == [0, 1, 0]


def test_screen_next_uses_ordered_history():
    cands = [{"title": f"p{i}", "abstract": "x", "paper_path": f"p{i}"} for i in range(6)]
    labels = {"p0": 0, "p1": 0, "p2": 0}
    out = screen_next(
        cands,
        labels,
        batch_size=2,
        stop_rules=StopRules(n_consecutive_irrelevant=3, min_labels_before_stop=3),
        history=[0, 0, 0],
    )
    assert out["stopped"] is True
    assert out["stop_meta"]["mode"] == "ordered"
    assert out["stop_meta"]["reason"] == "n_consecutive_irrelevant"


def test_screen_next_aggregate_fallback_reports_mode():
    cands = [{"title": f"p{i}", "abstract": "x", "paper_path": f"p{i}"} for i in range(6)]
    labels = {"p0": 0, "p1": 1}
    out = screen_next(cands, labels, batch_size=2)
    assert out["stopped"] is False
    assert out["stop_meta"]["mode"] == "aggregate"
