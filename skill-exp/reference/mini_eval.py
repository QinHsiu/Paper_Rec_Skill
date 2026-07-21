"""
Mini-evaluation cycle before full training.

Purpose: verify that a *solution plan* (not the whole pipeline) yields a
**clear metric gain on the plan's target subset / probe**.

Example: plan =「用 Qwen 清洗 OCR 难例标签」→ probe = handwritten_pinyin
subset → measure F1 before/after cleaning on that subset; promote only if
subset gain is clearly positive (and global does not collapse).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .types import Plan, TargetScore


ApplyPlanFn = Callable[[Plan], dict[str, Any]]  # apply plan on probe data / return artifacts
# Metrics dict convention (agent wires real eval):
#   - primary key = target.metric  → score on the plan's target subset (required)
#   - optional "{metric}_global"   → same metric on full eval (guardrail)
EvalSliceFn = Callable[[], dict[str, float]]


@dataclass
class MiniResult:
    plan_id: str
    before: dict[str, float]
    after: dict[str, float]
    delta: dict[str, float]
    promote_to_full_train: bool
    notes: str = ""
    target_subset: str = ""
    subset_gain: float = 0.0
    global_delta: float | None = None


def mini_validate_plan(
    plan: Plan,
    target: TargetScore,
    apply_plan: ApplyPlanFn,
    eval_slice: EvalSliceFn,
    *,
    min_delta_ratio: float = 0.25,
    default_min_clear_gain: float = 0.01,
    default_global_max_drop: float = 0.02,
) -> MiniResult:
    """
    Apply plan; require a **clear gain on the target subset** before full train.

    Promote when:
      subset_delta(primary) >= max(|expected_gain| * min_delta_ratio, min_clear_gain)
    AND (if global metric present):
      global does not drop by more than ``global_max_drop``.

    Plan.meta keys (optional):
      target_subset / probe_subset — which failing cluster / slice is under test
      min_clear_gain — absolute gain floor for「明显收益」(default 0.01)
      global_max_drop — max allowed drop on full eval (default 0.02)
      subset_metric — override metric key for subset (default target.metric)
    """
    subset = str(
        plan.meta.get("target_subset")
        or plan.meta.get("probe_subset")
        or plan.meta.get("cluster_label")
        or ""
    )
    primary = str(plan.meta.get("subset_metric") or target.metric)
    min_clear = float(plan.meta.get("min_clear_gain", default_min_clear_gain))
    max_drop = float(plan.meta.get("global_max_drop", default_global_max_drop))

    before = eval_slice()
    apply_plan(plan)
    after = eval_slice()

    b = float(before.get(primary, 0.0))
    a = float(after.get(primary, 0.0))
    delta = {
        k: float(after.get(k, 0.0)) - float(before.get(k, 0.0))
        for k in set(before) | set(after)
    }
    d_subset = a - b if target.higher_is_better else b - a
    need = max(abs(plan.expected_gain) * min_delta_ratio, min_clear, 1e-4)

    g_key = f"{primary}_global"
    g_before = before.get(g_key, before.get("global"))
    g_after = after.get(g_key, after.get("global"))
    global_delta: float | None = None
    global_ok = True
    if g_before is not None and g_after is not None:
        gb, ga = float(g_before), float(g_after)
        # signed improvement on global (positive = better)
        g_imp = ga - gb if target.higher_is_better else gb - ga
        global_delta = g_imp
        # allow small regression only up to max_drop
        global_ok = g_imp >= -abs(max_drop)

    promote = d_subset >= need and global_ok
    notes = (
        f"subset={subset or 'unspecified'} metric={primary} "
        f"subset_gain={d_subset:.5f} need>={need:.5f} "
        f"global_delta={global_delta} global_ok={global_ok}"
    )
    return MiniResult(
        plan_id=plan.plan_id,
        before=before,
        after=after,
        delta=delta,
        promote_to_full_train=promote,
        notes=notes,
        target_subset=subset,
        subset_gain=d_subset,
        global_delta=global_delta,
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
