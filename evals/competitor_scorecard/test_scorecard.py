from __future__ import annotations

import json
from pathlib import Path

from schema import CLOSED_COMPETITORS, DIMENSIONS, OSS_COMPETITORS
from validate import validate_scorecard

HERE = Path(__file__).resolve().parent


def test_dimension_count_and_axes():
    assert len(DIMENSIONS) >= 18
    axes = {d["axis"] for d in DIMENSIONS}
    assert axes == {"A", "B", "C"}


def test_competitor_pool_sizes():
    assert len(OSS_COMPETITORS) == 18
    assert len(CLOSED_COMPETITORS) >= 5


def test_data_json_validates_complete():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    errors = validate_scorecard(data)
    assert errors == [], errors


def test_render_contains_axes_and_closed_tag():
    from render import render_scorecard

    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    md = render_scorecard(data)
    assert "Axis A" in md or "轴 A" in md or "## A" in md
    assert "Elicit" in md
    assert "public-docs" in md
    assert "落后" in md  # W0 must surface real gaps
