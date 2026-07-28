"""Tests for smart lab notebook (labnote_loop)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SKILL_EXP = ROOT / "skill-exp"
sys.path.insert(0, str(SKILL_EXP))

from reference import labnote_loop as ln  # noqa: E402


@pytest.fixture()
def exp_dir(tmp_path: Path) -> Path:
    d = tmp_path / "demo-exp"
    d.mkdir()
    (d / "metrics").mkdir()
    (d / "metrics" / "summary.json").write_text(
        json.dumps(
            {
                "primary_metric": "F1",
                "primary_value": 0.93,
                "target_met": True,
                "threshold": 0.92,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (d / "trace").mkdir()
    return d


def test_init_append_verify_synthesize(exp_dir: Path) -> None:
    init = ln.init_labbook(
        exp_dir,
        hypothesis="rank-16 LoRA beats baseline",
        target_score={"metric": "F1", "threshold": 0.92, "eval_set": "test_v2"},
        bars=["F1 >= 0.92 on test_v2"],
    )
    assert Path(init["config"]).is_file()

    ap = ln.append_entry(
        exp_dir,
        title="LoRA r16",
        hypothesis="rank-16 LoRA beats baseline",
        plan_id="P1",
        change="model: LoRA r16",
    )
    eid = ap["entry_id"]
    assert eid.startswith("E")
    assert (exp_dir / "labbook" / "entries" / f"{eid}.md").is_file()

    rep = ln.verify_entry(exp_dir, eid)
    assert rep["verdict"] == "supported"
    assert rep["ok"] is True

    syn = ln.synthesize(exp_dir, hypothesis="rank-16 LoRA beats baseline")
    assert syn["verified"] >= 1
    assert Path(syn["index"]).is_file()
    assert (exp_dir / "findings.md").is_file()
    st = json.loads(Path(syn["state_path"]).read_text(encoding="utf-8"))
    assert st["labbook"]["verified"] >= 1


def test_mechanical_partial() -> None:
    bars = [
        {"text": "a", "met": True, "na": False},
        {"text": "b", "met": False, "na": False},
    ]
    assert ln.mechanical_verdict(bars) == "partial"


def test_status_suggests(exp_dir: Path) -> None:
    ln.init_labbook(exp_dir, hypothesis="h")
    st = ln.status(exp_dir)
    assert st["labbook_ready"] is True
    assert "append" in st["suggest_next"] or "init" in st["suggest_next"] or "verify" in st["suggest_next"]
