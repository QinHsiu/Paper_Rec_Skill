"""Advisory discovery saturation curve for multi-wave retrieval.

Fits N(t) ≈ N_total * (1 - exp(-λ t)) on snapshots of
``papers_evaluated`` / ``highly_relevant_count``. Never hard-stops —
only warns when marginal progress is low.
"""
from __future__ import annotations

import math
from typing import Any


def compute_marginal_rates(snapshots: list[dict[str, Any]]) -> list[float]:
    if len(snapshots) < 2:
        return []
    rates: list[float] = []
    for prev, curr in zip(snapshots[:-1], snapshots[1:]):
        d_eval = int(curr.get("papers_evaluated") or 0) - int(prev.get("papers_evaluated") or 0)
        d_rel = int(curr.get("highly_relevant_count") or 0) - int(prev.get("highly_relevant_count") or 0)
        if d_eval > 0:
            rates.append(d_rel / d_eval)
    return rates


def fit_exponential(
    papers_evaluated: list[int],
    highly_relevant: list[int],
) -> tuple[float, float]:
    """Return (N_total_estimate, lambda). lambda<=0 means fit failed."""
    if len(papers_evaluated) < 3 or len(highly_relevant) < 3:
        if highly_relevant:
            return (max(1.0, highly_relevant[-1] * 1.5), 0.0)
        return (1.0, 0.0)

    current_t = papers_evaluated[-1]
    current_y = highly_relevant[-1]
    if current_t <= 0 or current_y <= 0:
        return (max(1.0, float(current_y) * 1.5), 0.0)

    cutoff = max(1, len(papers_evaluated) // 5)
    early_dt = papers_evaluated[cutoff] - papers_evaluated[0]
    early_dy = highly_relevant[cutoff] - highly_relevant[0]
    recent_dt = papers_evaluated[-1] - papers_evaluated[-cutoff - 1]
    recent_dy = highly_relevant[-1] - highly_relevant[-cutoff - 1]
    early_rate = (early_dy / early_dt) if early_dt > 0 else 0.0
    recent_rate = (recent_dy / recent_dt) if recent_dt > 0 else 0.0

    if early_rate <= 0 or recent_rate <= 0 or recent_rate >= early_rate:
        return (max(float(current_y), current_y * 1.5), 0.0)

    try:
        lambda_est = -math.log(recent_rate / early_rate) / current_t
    except (ValueError, ZeroDivisionError):
        return (max(float(current_y), current_y * 1.5), 0.0)

    if not math.isfinite(lambda_est) or lambda_est <= 0:
        return (max(float(current_y), current_y * 1.5), 0.0)

    lambda_est = max(1e-4, min(0.2, lambda_est))
    exp_factor = 1.0 - math.exp(-lambda_est * current_t)
    n_total_est = current_y / 0.5 if exp_factor <= 1e-3 else current_y / exp_factor
    n_total_est = max(float(current_y), min(current_y * 5.0, n_total_est))
    return (n_total_est, lambda_est)


def compute_coverage(current_relevant: int, n_total: float) -> tuple[float, float, float]:
    if n_total <= 0:
        return (1.0, 0.5, 1.0)
    point = min(1.0, max(0.0, current_relevant / n_total))
    lower = min(1.0, max(0.0, current_relevant / (n_total * 1.15)))
    upper = min(1.0, max(0.0, current_relevant / (n_total * 0.85)))
    if lower > upper:
        lower, upper = upper, lower
    return (point, lower, upper)


def should_warn_low_progress(
    snapshots: list[dict[str, Any]],
    *,
    min_papers: int = 30,
    recent_windows: int = 2,
    rate_threshold: float = 0.05,
) -> tuple[bool, str]:
    """Advisory only. True when recent marginal rates are low after enough eval."""
    if not snapshots:
        return False, "no_snapshots"
    last = snapshots[-1]
    evaluated = int(last.get("papers_evaluated") or 0)
    if evaluated < min_papers:
        return False, f"below_min_papers({evaluated}<{min_papers})"
    rates = compute_marginal_rates(snapshots)
    if len(rates) < recent_windows:
        return False, "need_more_waves"
    recent = rates[-recent_windows:]
    if all(r <= rate_threshold for r in recent):
        return True, f"low_marginal_rates={recent}"
    return False, "progress_ok"


def analyze_snapshots(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    ts = [int(s.get("papers_evaluated") or 0) for s in snapshots]
    ys = [int(s.get("highly_relevant_count") or 0) for s in snapshots]
    n_total, lam = fit_exponential(ts, ys)
    cov = compute_coverage(ys[-1] if ys else 0, n_total) if ys else (0.0, 0.0, 0.0)
    warn, reason = should_warn_low_progress(snapshots)
    return {
        "n_snapshots": len(snapshots),
        "papers_evaluated": ts[-1] if ts else 0,
        "highly_relevant": ys[-1] if ys else 0,
        "n_total_est": round(n_total, 2),
        "lambda": round(lam, 6),
        "coverage_point": round(cov[0], 4),
        "coverage_ci": [round(cov[1], 4), round(cov[2], 4)],
        "marginal_rates": [round(r, 4) for r in compute_marginal_rates(snapshots)],
        "warn_low_progress": warn,
        "warn_reason": reason,
        "advisory_only": True,
    }
