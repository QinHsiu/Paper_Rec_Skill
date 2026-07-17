"""
Data-centric Solution Preference (pairwise).

Adapted from ForeAgent / predict-before-execute:
  Input:  task + verified data_report + solution_A + solution_B
  Output: winner_index ∈ {0,1}, confidence ∈ [0,1], reasoning

Paper default confidence gate: c = 0.7
Forbid pure "complexity wins" shortcuts (see prompts/complexity_heuristic.md as baseline only).
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from .types import AskLLM, Plan, PreferenceVote


JSON_RE = re.compile(r"\{[^{}]*\"predicted_best_index\"[^{}]*\}", re.DOTALL)


def pairwise_prefer(
    task_name: str,
    task_desc: str,
    data_report: str,
    plan_a: Plan,
    plan_b: Plan,
    ask: AskLLM,
    *,
    prompt_path: str = "prompts/solution_preference.md",
) -> PreferenceVote:
    system, user_tmpl = _load_prompt_pair(prompt_path)
    user = user_tmpl.format(
        task_name=task_name,
        task_desc=task_desc,
        data_analysis_report=data_report,
        code_snippet_0=_plan_as_text(plan_a),
        code_snippet_1=_plan_as_text(plan_b),
        code_0_path=plan_a.plan_id,
        code_1_path=plan_b.plan_id,
    )
    raw_text = ask(system, user)
    return parse_preference_response(raw_text)


def parse_preference_response(text: str) -> PreferenceVote:
    """Extract final JSON: {predicted_best_index, confidence}."""
    m = JSON_RE.search(text)
    blob = m.group(0) if m else text[text.rfind("{") : text.rfind("}") + 1]
    data: dict[str, Any] = json.loads(blob)
    idx = int(data["predicted_best_index"])
    conf = float(data.get("confidence", 0.0))
    conf = max(0.0, min(1.0, conf))
    reasoning = text[: m.start()].strip() if m else text
    return PreferenceVote(winner_index=idx, confidence=conf, reasoning=reasoning, raw=data)


def gated_winner(
    vote: PreferenceVote,
    *,
    confidence_gate: float = 0.7,
) -> Optional[int]:
    """
    Confidence gate (paper default 0.7).
    Returns winner index if confident, else None → regenerate / ask human / fall back.
    """
    if vote.confidence >= confidence_gate:
        return vote.winner_index
    return None


def _plan_as_text(plan: Plan) -> str:
    actions = "\n".join(f"- {a}" for a in plan.actions)
    return (
        f"hypothesis: {plan.hypothesis}\n"
        f"expected_gain: {plan.expected_gain}\n"
        f"cost: {plan.cost}\n"
        f"risk: {plan.risk}\n"
        f"actions:\n{actions}\n"
    )


def _load_prompt_pair(rel: str) -> tuple[str, str]:
    from pathlib import Path

    path = Path(__file__).parent / rel
    text = path.read_text(encoding="utf-8")
    system, user = text.split("---USER---", 1)
    return system.replace("---SYSTEM---", "").strip(), user.strip()
