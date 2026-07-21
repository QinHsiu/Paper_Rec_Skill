"""
High-volume generation + confidence-gated pairwise selection.

ForeAgent-style defaults (paper §6.2):
  m = 10 candidates (exploration without full execution)
  confidence_gate c = 0.7
  top_k = 1 physical verification
"""
from __future__ import annotations

from typing import Callable, Optional

from .preference import gated_winner, pairwise_prefer
from .types import AskLLM, Plan


GeneratePlansFn = Callable[[str, str, str, int], list[Plan]]
# (task_name, task_desc, data_report, m) -> m plans


def generate_candidates(
    task_name: str,
    task_desc: str,
    data_report: str,
    generate: GeneratePlansFn,
    *,
    m: int = 10,
) -> list[Plan]:
    """Phase 1 — High-Volume Generation (no full train)."""
    plans = generate(task_name, task_desc, data_report, m)
    if len(plans) < 2:
        raise ValueError("Need at least 2 plans for pairwise preference")
    return plans[:m]


def pairwise_tournament(
    plans: list[Plan],
    task_name: str,
    task_desc: str,
    data_report: str,
    ask: AskLLM,
    *,
    confidence_gate: float = 0.7,
    max_retries_on_low_conf: int = 2,
) -> Plan:
    """
    Phase 2 — Confidence-Gated Pairwise Selection.

    Strategy (reference): single-elimination style.
    Low-confidence votes → retry once, else keep current champ (conservative).
    Alternative agent may implement full round-robin + Elo; keep logs either way.
    """
    champ = plans[0]
    for challenger in plans[1:]:
        winner_plan = _duel(
            champ,
            challenger,
            task_name,
            task_desc,
            data_report,
            ask,
            confidence_gate=confidence_gate,
            max_retries=max_retries_on_low_conf,
        )
        champ = winner_plan
    return champ


def _duel(
    a: Plan,
    b: Plan,
    task_name: str,
    task_desc: str,
    data_report: str,
    ask: AskLLM,
    *,
    confidence_gate: float,
    max_retries: int,
) -> Plan:
    pair = (a, b)
    for _ in range(max_retries + 1):
        vote = pairwise_prefer(task_name, task_desc, data_report, pair[0], pair[1], ask)
        idx = gated_winner(vote, confidence_gate=confidence_gate)
        # idx must be 0 or 1; gated_winner already rejects out-of-range (incl. -1)
        if idx in (0, 1):
            return pair[idx]
        # swap order to mitigate position bias on retry (paper mentions position bias)
        pair = (pair[1], pair[0])
    # conservative fallback: higher expected_gain / cost
    return max(pair, key=lambda p: (p.expected_gain / max(p.cost, 1e-6)))


def select_top_k(plans_ranked: list[Plan], k: int = 1) -> list[Plan]:
    """Phase 3 prep — only Top-k enter physical verify / mini-eval / train."""
    return plans_ranked[:k]
