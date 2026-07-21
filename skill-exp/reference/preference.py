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
    """Extract final JSON: {predicted_best_index, confidence}. Never raises on bad LLM text."""
    data = _extract_preference_json(text or "")
    raw_idx = data.get("predicted_best_index", 0)
    try:
        idx = int(raw_idx)
    except (TypeError, ValueError):
        idx = 0
    try:
        conf = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    m = JSON_RE.search(text or "")
    reasoning = text[: m.start()].strip() if m else (text or "").strip()
    return PreferenceVote(winner_index=idx, confidence=conf, reasoning=reasoning, raw=data)


def gated_winner(
    vote: PreferenceVote,
    *,
    confidence_gate: float = 0.7,
) -> Optional[int]:
    """
    Confidence gate (paper default 0.7).
    Returns winner index if confident and in {0,1}, else None → regenerate / ask human / fall back.
    Out-of-range indices (e.g. 2, -1) are treated as invalid, not as Python negative indexing.
    """
    if vote.winner_index not in (0, 1):
        return None
    if vote.confidence >= confidence_gate:
        return vote.winner_index
    return None


def _extract_preference_json(text: str) -> dict[str, Any]:
    """Pull a preference dict from LLM text; tolerate nested braces and missing JSON."""
    fallback: dict[str, Any] = {"predicted_best_index": 0, "confidence": 0.0}
    if not text.strip():
        return fallback

    m = JSON_RE.search(text)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    best: dict[str, Any] | None = None
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        if "predicted_best_index" in obj:
            best = obj
        elif best is None:
            best = obj
    return best if best is not None else fallback


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
    if "---USER---" in text:
        system, user = text.split("---USER---", 1)
        return system.replace("---SYSTEM---", "").strip(), user.strip()
    return "You are an expert comparing two solution plans.", text
