"""Offline tests for multi-agent lab routing + orchestrator."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.model_routing import ModelTier, recommend_tier
from reference.orchestrator import brain_decide, init_lab_run, mark_task, status_summary


def test_routing_tiers():
    assert recommend_tier(role="draw")["tier"] == "fast"
    assert recommend_tier(role="brain")["tier"] == "deep"
    assert recommend_tier(task="format_json")["tier"] == "fast"
    assert recommend_tier(task="accept_or_reject")["tier"] == "deep"
    assert recommend_tier(role="retrieve", task="query_rewrite")["tier"] == "standard"


def test_init_and_pipeline(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    info = init_lab_run(content, title="t", hypothesis="h", thread_id="th1")
    assert info["task_n"] >= 6
    assert (content / "lab" / info["run_id"] / "run.json").is_file()
    st = status_summary(content, info["run_id"])
    assert st["ready"]
    assert st["ready"][0]["model_tier"] in {"fast", "standard", "deep"}
    tid = st["ready"][0]["task_id"]
    out = mark_task(content, info["run_id"], tid, status="done", result={"ok": True})
    assert out["ok"]
    st2 = status_summary(content, info["run_id"])
    assert st2["counts"].get("done", 0) >= 1
    bd = brain_decide(content, info["run_id"], decision="ADVANCE", reason="ok")
    assert bd["ok"]


def test_model_tier_enum():
    assert ModelTier.FAST.value == "fast"
