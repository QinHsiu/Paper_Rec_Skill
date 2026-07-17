"""Exp_Sandbox reference algorithms (Predict-then-Verify style stubs)."""

from .badcase import cluster_badcases, collect_badcases, plans_from_clusters
from .data_report import build_verified_data_report
from .mini_eval import cycle_until_stable, mini_validate_plan
from .orchestrator import run_exp_loop
from .predict_then_verify import PTVConfig, predict_then_verify_step
from .preference import gated_winner, pairwise_prefer, parse_preference_response
from .tournament import generate_candidates, pairwise_tournament
from .train_monitor import ascii_sparkline, summarize_curves
from .types import Plan, TargetScore, ToolBundle

__all__ = [
    "Plan",
    "TargetScore",
    "ToolBundle",
    "PTVConfig",
    "build_verified_data_report",
    "pairwise_prefer",
    "parse_preference_response",
    "gated_winner",
    "generate_candidates",
    "pairwise_tournament",
    "predict_then_verify_step",
    "collect_badcases",
    "cluster_badcases",
    "plans_from_clusters",
    "mini_validate_plan",
    "cycle_until_stable",
    "ascii_sparkline",
    "summarize_curves",
    "run_exp_loop",
]
