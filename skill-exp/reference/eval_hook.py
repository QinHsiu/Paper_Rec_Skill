"""/exp_eval bundle writer + number-verify auto-hook metadata.

Writes ``metrics/summary.json`` (and optional ``eval/summary.json``) so
``wiki_bridge number-verify --exp-dir`` can whitelist Results floats.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def exp_root(content_root: str | Path, experiment_id: str) -> Path:
    return Path(content_root) / experiment_id


def write_eval_bundle(
    experiment_id: str,
    metrics: dict[str, Any],
    *,
    content_root: str | Path = "content/exp",
    target: dict[str, Any] | None = None,
    plan_id: str = "",
    run_id: str = "",
    stratified: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist eval metrics for number-verify + downstream drafting.

    Returns paths + pass/fail vs optional target.
    """
    root = exp_root(content_root, experiment_id)
    metrics_dir = root / "metrics"
    eval_dir = root / "eval"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    flat = _flatten_metrics(metrics)
    target = target or {}
    threshold = target.get("threshold")
    metric_name = str(target.get("metric") or "")
    primary = None
    if metric_name and metric_name in flat:
        primary = float(flat[metric_name])
    elif flat:
        # first numeric
        for k, v in flat.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                primary = float(v)
                metric_name = metric_name or k
                break

    passed = None
    if primary is not None and threshold is not None:
        try:
            thr = float(threshold)
            direction = str(target.get("direction") or "maximize").lower()
            passed = primary >= thr if direction != "minimize" else primary <= thr
        except (TypeError, ValueError):
            passed = None

    payload: dict[str, Any] = {
        "experiment_id": experiment_id,
        "run_id": run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "plan_id": plan_id,
        "written_at": datetime.now(timezone.utc).isoformat(),
        "metrics": flat,
        "raw_metrics": metrics,
        "target": target,
        "primary_metric": metric_name or None,
        "primary_value": primary,
        "target_met": passed,
        "stratified": stratified or {},
        "number_verify_ready": True,
    }
    if extra:
        payload["extra"] = extra

    summary_path = metrics_dir / "summary.json"
    final_path = metrics_dir / "final.json"
    eval_path = eval_dir / "summary.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    summary_path.write_text(text, encoding="utf-8")
    final_path.write_text(text, encoding="utf-8")
    eval_path.write_text(text, encoding="utf-8")

    hook_cmd = (
        f"python -m wiki_bridge.cli number-verify --exp-dir {root} "
        f"--thread <thread_id> --strict"
    )
    hint_path = metrics_dir / "number_verify_hint.txt"
    hint_path.write_text(
        "After /draft or latex-export, run number-verify against this exp dir:\n"
        f"  {hook_cmd}\n"
        "Or use: python -m wiki_bridge.cli exp-eval-hook --exp-dir ... --thread ...\n",
        encoding="utf-8",
    )

    return {
        "experiment_id": experiment_id,
        "summary_path": str(summary_path),
        "final_path": str(final_path),
        "eval_path": str(eval_path),
        "hint_path": str(hint_path),
        "primary_metric": metric_name or None,
        "primary_value": primary,
        "target_met": passed,
        "metrics": flat,
        "number_verify_cmd": hook_cmd,
    }


def _flatten_metrics(metrics: dict[str, Any], prefix: str = "") -> dict[str, float | int | str]:
    out: dict[str, float | int | str] = {}
    for k, v in (metrics or {}).items():
        key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            out[key if prefix else k] = v
        elif isinstance(v, dict):
            nested = _flatten_metrics(v, key if prefix else k)
            out.update(nested)
        elif isinstance(v, str):
            try:
                out[key if prefix else k] = float(v)
            except ValueError:
                out[key if prefix else k] = v
    return out
