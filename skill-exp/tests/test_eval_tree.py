"""Tests for eval_hook + exp_tree."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reference.eval_hook import write_eval_bundle  # noqa: E402
from reference.exp_tree import (  # noqa: E402
    expand_from_best,
    load_tree,
    mark_buggy,
    ready_for_next_stage,
    save_tree,
)


def test_eval_bundle_and_tree() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        out = write_eval_bundle(
            "demo",
            {"F1": 0.81, "acc": 0.9},
            content_root=root,
            target={"metric": "F1", "threshold": 0.8, "direction": "maximize"},
            plan_id="P1",
        )
        assert Path(out["summary_path"]).is_file()
        data = json.loads(Path(out["summary_path"]).read_text(encoding="utf-8"))
        assert data["metrics"]["F1"] == 0.81
        assert data["target_met"] is True
        assert data["number_verify_ready"] is True

        tree = load_tree(root, "demo")
        n1 = expand_from_best(tree, plan_id="P1", metric=0.81, metric_name="F1")
        n2 = expand_from_best(tree, plan_id="P2", metric=0.84, metric_name="F1")
        save_tree(tree, root)
        loaded = load_tree(root, "demo")
        assert loaded.root_id == n1.id
        assert n2.id in loaded.nodes[n1.id].children
        ready = ready_for_next_stage(loaded)
        assert ready["ready"] is True
        mark_buggy(loaded, n2.id, notes="nan loss")
        save_tree(loaded, root)
        assert ready_for_next_stage(load_tree(root, "demo"))["ready"] is False


if __name__ == "__main__":
    test_eval_bundle_and_tree()
    print("OK eval_hook + exp_tree")
