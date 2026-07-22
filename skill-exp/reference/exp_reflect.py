"""Outer-loop reflection: synthesize findings.md from rounds / exp_tree / dead_ends."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def collect_exp_signals(exp_dir: Path) -> dict[str, Any]:
    exp_dir = Path(exp_dir)
    signals: dict[str, Any] = {
        "rounds": [],
        "dead_ends": "",
        "tree": None,
        "metrics": None,
        "repro": None,
    }
    rounds = exp_dir / "rounds"
    if rounds.is_dir():
        for p in sorted(rounds.glob("round-*.md")):
            signals["rounds"].append({"path": str(p), "text": p.read_text(encoding="utf-8")[:2000]})
    de = exp_dir / "trace" / "dead_ends.md"
    if de.is_file():
        signals["dead_ends"] = de.read_text(encoding="utf-8")[:4000]
    tree = exp_dir / "trace" / "exp_tree.json"
    if tree.is_file():
        signals["tree"] = json.loads(tree.read_text(encoding="utf-8"))
    metrics = exp_dir / "metrics" / "summary.json"
    if metrics.is_file():
        signals["metrics"] = json.loads(metrics.read_text(encoding="utf-8"))
    repro = exp_dir / "trace" / "repro_check.json"
    if repro.is_file():
        signals["repro"] = json.loads(repro.read_text(encoding="utf-8"))
    return signals


def build_findings(exp_dir: Path, *, hypothesis: str = "") -> dict[str, Any]:
    sig = collect_exp_signals(exp_dir)
    lines = [
        f"# Findings — {Path(exp_dir).name}",
        "",
        f"_Updated: {datetime.now(timezone.utc).isoformat()}_",
        "",
        "## Hypothesis",
        "",
        hypothesis or "_(fill from thread)_",
        "",
        "## What worked",
        "",
    ]
    met = (sig.get("metrics") or {}).get("target_met")
    primary = (sig.get("metrics") or {}).get("primary_value")
    metric = (sig.get("metrics") or {}).get("primary_metric")
    if met:
        lines.append(f"- Target met: `{metric}={primary}`")
    elif primary is not None:
        lines.append(f"- Best so far: `{metric}={primary}` (target not met)")
    else:
        lines.append("- _(no metrics/summary.json yet)_")

    tree = sig.get("tree") or {}
    nodes = tree.get("nodes") or {}
    healthy = [n for n in nodes.values() if not n.get("buggy")]
    buggy = [n for n in nodes.values() if n.get("buggy")]
    lines.extend(["", "## Experiment tree", ""])
    lines.append(f"- healthy nodes: {len(healthy)}; buggy: {len(buggy)}; stage: `{tree.get('stage')}`")

    lines.extend(["", "## Dead ends (do not retry blindly)", ""])
    if sig.get("dead_ends"):
        lines.append(sig["dead_ends"][:1500])
    else:
        lines.append("- _(none logged)_")

    lines.extend(["", "## Reproducibility", ""])
    repro = sig.get("repro")
    if repro:
        lines.append(f"- double-exec: `ok={repro.get('ok')}` reason=`{repro.get('reason')}`")
    else:
        lines.append("- _(no repro_check.json — run double-exec gate)_")

    lines.extend(
        [
            "",
            "## Next outer-loop moves",
            "",
            "1. If target unmet: prefer ablation child on best healthy node, not a new unrelated plan.",
            "2. Convert working plan into a paper claim only after number-verify + stats-rigor pass.",
            "3. Update thread evidence_gaps with unresolved questions from dead ends.",
            "",
        ]
    )
    md = "\n".join(lines)
    out_path = Path(exp_dir) / "findings.md"
    out_path.write_text(md, encoding="utf-8")
    state = {
        "experiment_id": Path(exp_dir).name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "outer_loop": {
            "findings_path": str(out_path),
            "target_met": met,
            "healthy_nodes": len(healthy),
            "buggy_nodes": len(buggy),
        },
    }
    state_path = Path(exp_dir) / "trace" / "research-state.yaml"
    # write JSON-compatible YAML-lite
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"findings_path": str(out_path), "state_path": str(state_path), "markdown": md, "state": state}
