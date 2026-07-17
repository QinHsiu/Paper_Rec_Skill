"""
Predict-then-Verify loop (core).

Decouple exploration (cheap LLM preference) from execution (expensive train/eval).

Pipeline per improvement step:
  generate m plans → pairwise prefer (gate c) → verify Top-k (mini_eval / train) → feedback
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from .tournament import generate_candidates, pairwise_tournament, select_top_k
from .types import AskLLM, Plan, TargetScore


MiniVerifyFn = Callable[[Plan], dict[str, Any]]
FullTrainEvalFn = Callable[[Plan], dict[str, Any]]  # returns metrics dict incl. primary
GeneratePlansFn = Callable[[str, str, str, int], list[Plan]]


@dataclass
class PTVConfig:
    m_candidates: int = 10
    confidence_gate: float = 0.7
    top_k_verify: int = 1
    prefer_mini_before_full: bool = True


@dataclass
class PTVResult:
    ranked_plans: list[Plan]
    verified: list[dict[str, Any]]
    best_plan: Optional[Plan]
    best_metrics: dict[str, Any]
    target_met: bool


def predict_then_verify_step(
    task_name: str,
    task_desc: str,
    data_report: str,
    target: TargetScore,
    ask: AskLLM,
    generate: GeneratePlansFn,
    mini_verify: MiniVerifyFn,
    full_train_eval: FullTrainEvalFn,
    cfg: PTVConfig | None = None,
) -> PTVResult:
    """
    One Predict-then-Verify improvement step.

    Agent maps:
      mini_verify  → data_processing & mini_evaluation on a slice
      full_train_eval → /exp_training + /exp_eval via tool/function
    """
    cfg = cfg or PTVConfig()
    candidates = generate_candidates(
        task_name, task_desc, data_report, generate, m=cfg.m_candidates
    )
    champ = pairwise_tournament(
        candidates,
        task_name,
        task_desc,
        data_report,
        ask,
        confidence_gate=cfg.confidence_gate,
    )
    # Rank: champ first, then others by expected_gain (lightweight)
    rest = [p for p in candidates if p.plan_id != champ.plan_id]
    rest.sort(key=lambda p: p.expected_gain, reverse=True)
    ranked = [champ] + rest
    to_run = select_top_k(ranked, k=cfg.top_k_verify)

    verified: list[dict[str, Any]] = []
    best_plan: Optional[Plan] = None
    best_metrics: dict[str, Any] = {}
    best_primary = float("-inf") if target.higher_is_better else float("inf")

    for plan in to_run:
        record: dict[str, Any] = {"plan_id": plan.plan_id}
        if cfg.prefer_mini_before_full:
            mini = mini_verify(plan)
            record["mini"] = mini
            if not mini.get("promote_to_full_train", True):
                verified.append(record)
                continue
        metrics = full_train_eval(plan)
        record["metrics"] = metrics
        verified.append(record)
        primary = float(metrics.get(target.metric, metrics.get("primary", 0.0)))
        better = (
            primary > best_primary if target.higher_is_better else primary < best_primary
        )
        if better:
            best_primary = primary
            best_plan = plan
            best_metrics = metrics

    target_met = bool(best_metrics) and target.met(
        float(best_metrics.get(target.metric, best_metrics.get("primary", 0.0)))
    )
    return PTVResult(
        ranked_plans=ranked,
        verified=verified,
        best_plan=best_plan,
        best_metrics=best_metrics,
        target_met=target_met,
    )
