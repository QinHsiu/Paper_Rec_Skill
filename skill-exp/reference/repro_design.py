"""Control vs experimental partitions + double-exec reproducibility gate."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Partition:
    name: str
    factor: str
    values: list[Any] = field(default_factory=list)


@dataclass
class ExpDesign:
    control: dict[str, Any] = field(default_factory=dict)
    experimental: dict[str, Any] = field(default_factory=dict)
    partitions: list[Partition] = field(default_factory=list)
    seeds: list[int] = field(default_factory=lambda: [0, 1])
    metric: str = "primary"
    max_rel_diff: float = 0.02  # relative tolerance for double-exec

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpDesign":
        parts = [
            Partition(**p) if isinstance(p, dict) else p
            for p in (data.get("partitions") or [])
        ]
        return cls(
            control=dict(data.get("control") or {}),
            experimental=dict(data.get("experimental") or {}),
            partitions=parts,
            seeds=list(data.get("seeds") or [0, 1]),
            metric=str(data.get("metric") or "primary"),
            max_rel_diff=float(data.get("max_rel_diff") or 0.02),
        )


def default_design(metric: str = "F1") -> ExpDesign:
    return ExpDesign(
        control={"name": "baseline", "script": "", "seeds": [0, 1]},
        experimental={"name": "treatment", "script": "", "seeds": [0, 1]},
        partitions=[Partition(name="p1", factor="lr", values=[1e-3, 1e-4])],
        seeds=[0, 1],
        metric=metric,
    )


def save_design(path: Path, design: ExpDesign) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(design.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_design(path: Path) -> ExpDesign:
    return ExpDesign.from_dict(json.loads(path.read_text(encoding="utf-8")))


def validate_design(design: ExpDesign) -> dict[str, Any]:
    issues: list[str] = []
    if not design.control:
        issues.append("missing_control")
    if not design.experimental:
        issues.append("missing_experimental")
    if len(design.seeds) < 2:
        issues.append("need_at_least_2_seeds_for_repro")
    return {"ok": not issues, "issues": issues, "design": design.to_dict()}


def double_exec_check(
    run_a: dict[str, float],
    run_b: dict[str, float],
    *,
    metric: str,
    max_rel_diff: float = 0.02,
) -> dict[str, Any]:
    """Compare two independent eval dicts; fail if relative gap too large."""
    a = float(run_a.get(metric, run_a.get("primary", float("nan"))))
    b = float(run_b.get(metric, run_b.get("primary", float("nan"))))
    if not math.isfinite(a) or not math.isfinite(b):
        return {"ok": False, "reason": "non_finite_metric", "a": a, "b": b, "metric": metric}
    denom = max(abs(a), abs(b), 1e-8)
    rel = abs(a - b) / denom
    return {
        "ok": rel <= max_rel_diff,
        "metric": metric,
        "a": a,
        "b": b,
        "rel_diff": round(rel, 6),
        "max_rel_diff": max_rel_diff,
        "reason": "ok" if rel <= max_rel_diff else "repro_mismatch",
    }


def write_repro_report(exp_dir: Path, report: dict[str, Any]) -> Path:
    path = Path(exp_dir) / "trace" / "repro_check.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
