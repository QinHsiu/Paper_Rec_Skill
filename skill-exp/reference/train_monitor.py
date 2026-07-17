"""
Training process monitor — loss / val metrics / multi-curve summaries.

Agent should attach real log parsers (tensorboard, wandb, CSV, stdout regex).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional


@dataclass
class CurvePoint:
    step: int
    value: float


@dataclass
class TrainMonitorState:
    run_id: str
    train_loss: list[CurvePoint] = field(default_factory=list)
    val_metrics: dict[str, list[CurvePoint]] = field(default_factory=dict)
    best_checkpoint: Optional[str] = None
    anomalies: list[str] = field(default_factory=list)


def parse_log_lines(lines: Iterable[str]) -> TrainMonitorState:
    """
    PSEUDOCODE parser examples:
      loss=0.42 step=100
      val_f1=0.81 epoch=3
    Replace with user log format.
    """
    state = TrainMonitorState(run_id="unknown")
    for line in lines:
        # agent: regex extract → append CurvePoint
        if "loss=" in line and "step=" in line:
            pass
        if "val_" in line:
            pass
        if "nan" in line.lower() or "overflow" in line.lower():
            state.anomalies.append(line.strip())
    return state


def ascii_sparkline(values: list[float], width: int = 24) -> str:
    if not values:
        return "(empty)"
    blocks = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    idxs = [int((v - lo) / span * (len(blocks) - 1)) for v in values[-width:]]
    return "".join(blocks[i] for i in idxs)


def summarize_curves(state: TrainMonitorState) -> str:
    parts = [f"run_id={state.run_id}"]
    if state.train_loss:
        parts.append("train_loss: " + ascii_sparkline([p.value for p in state.train_loss]))
    for name, pts in state.val_metrics.items():
        parts.append(f"{name}: " + ascii_sparkline([p.value for p in pts]))
    if state.best_checkpoint:
        parts.append(f"best_ckpt={state.best_checkpoint}")
    if state.anomalies:
        parts.append("anomalies=" + "; ".join(state.anomalies[:5]))
    return "\n".join(parts)


def should_early_stop(
    primary_curve: list[CurvePoint],
    *,
    patience: int = 5,
    higher_is_better: bool = True,
) -> bool:
    if len(primary_curve) < patience + 1:
        return False
    recent = primary_curve[-(patience + 1) :]
    best = recent[0].value
    for p in recent[1:]:
        improved = p.value > best if higher_is_better else p.value < best
        if improved:
            best = p.value
            return False
    return True
