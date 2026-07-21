"""
Mini-evaluation cycle before full training.

data_processing & mini_evaluation [cycle verify current method of plan]
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .types import Plan, TargetScore


ApplyPlanFn = Callable[[Plan], dict[str, Any]]  # mutate slice / return artifact paths
EvalSliceFn = Callable[[], dict[str, float]]  # metrics on probe set


@dataclass
class MiniResult:
    plan_id: str
    before: dict[str, float]
    after: dict[str, float]
    delta: dict[str, float]
    promote_to_full_train: bool
    notes: str = ""


def mini_validate_plan(
    plan: Plan,
    target: TargetScore,
    apply_plan: ApplyPlanFn,
    eval_slice: EvalSliceFn,
    *,
    min_delta_ratio: float = 0.25,
) -> MiniResult:
    """
    Apply plan on a small slice; require a fraction of predicted gain before full train.

    promote if delta(primary) >= min_delta_ratio * plan.expected_gain
    (or any positive move if expected_gain is tiny).
    """
    before = eval_slice()
    apply_plan(plan)
    after = eval_slice()
    primary = target.metric
    b = float(before.get(primary, 0.0))
    a = float(after.get(primary, 0.0))
    delta = {k: float(after.get(k, 0.0)) - float(before.get(k, 0.0)) for k in set(before) | set(after)}
    d_primary = a - b if target.higher_is_better else b - a
    need = max(abs(plan.expected_gain) * min_delta_ratio, 1e-4)
    promote = d_primary >= need
    return MiniResult(
        plan_id=plan.plan_id,
        before=before,
        after=after,
        delta=delta,
        promote_to_full_train=promote,
        notes=f"d_primary={d_primary:.5f} need>={need:.5f}",
    )


def cycle_until_stable(
    plan: Plan,
    target: TargetScore,
    apply_plan: ApplyPlanFn,
    eval_slice: EvalSliceFn,
    revise_plan: Callable[[Plan, MiniResult], Plan],
    *,
    max_cycles: int = 3,
) -> tuple[Plan, list[MiniResult]]:
    """If mini-eval fails, revise plan and retry (bounded).

    ``max_cycles < 1`` is clamped to 1 so callers never get an empty history.
    """
    if max_cycles < 1:
        max_cycles = 1
    history: list[MiniResult] = []
    cur = plan
    for _ in range(max_cycles):
        r = mini_validate_plan(cur, target, apply_plan, eval_slice)
        history.append(r)
        if r.promote_to_full_train:
            return cur, history
        cur = revise_plan(cur, r)
    return cur, history
