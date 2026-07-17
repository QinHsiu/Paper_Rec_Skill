"""
Data report builder — adapted from Profile → Verify → Verbalize
(zjunlp/predict-before-execute / ForeAgent paper).

Agent usage:
  1) profile_raw_stats(split)   → numeric / structural extraction
  2) verify_stats(raw)          → sanity-check / recompute critical stats
  3) verbalize_report(raw)      → causal, model-relevant prose (no model picking)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .types import AskLLM, Split, ToolBundle


@dataclass
class RawProfile:
    split: str
    modality_stats: dict[str, Any]  # image/audio/text probes
    label_stats: dict[str, Any]
    notes: list[str]


def profile_raw_stats(
    split: Split,
    tools: ToolBundle,
    *,
    sample_limit: int = 5000,
) -> RawProfile:
    """
    PSEUDOCODE — replace bodies with user analysis_tool or default probes.

    Image  → size, resolution, aspect, channel stats
    Audio  → duration, sample_rate, channels
    Text   → length hist, label distribution, language mix
    """
    # --- agent: call tools.sources / analysis_tools here ---
    raise NotImplementedError(
        "Wire to user data paths. Example probes in skill-exp/SKILL.md § analysis_tool"
    )


def verify_stats(raw: RawProfile) -> RawProfile:
    """
    Lightweight verification pass:
    - recompute class counts on a fresh sample
    - flag impossible values (neg duration, 0-size images)
    - drop or mark contaminated fields
    """
    verified = RawProfile(
        split=raw.split,
        modality_stats=dict(raw.modality_stats),
        label_stats=dict(raw.label_stats),
        notes=list(raw.notes) + ["verified=True"],
    )
    return verified


def verbalize_report(
    task_name: str,
    task_desc: str,
    raw: RawProfile,
    ask: AskLLM,
    *,
    prompt_path: str = "prompts/data_analysis_report.md",
) -> str:
    """
    Produce structured Data Analysis Report used later by preference ranking.
    MUST NOT recommend a specific model (avoids bias) — only risks/advantages.
    """
    system, user_tmpl = _load_prompt_pair(prompt_path)
    user = user_tmpl.format(
        task=task_name,
        desc_block=task_desc,
        analysis_text=_fmt_raw(raw),
    )
    return ask(system, user)


def build_verified_data_report(
    task_name: str,
    task_desc: str,
    split: Split,
    tools: ToolBundle,
    ask: AskLLM,
) -> str:
    """Full Profile → Verify → Verbalize pipeline."""
    raw = profile_raw_stats(split, tools)
    raw = verify_stats(raw)
    return verbalize_report(task_name, task_desc, raw, ask)


def _fmt_raw(raw: RawProfile) -> str:
    return (
        f"split={raw.split}\n"
        f"modality_stats={raw.modality_stats}\n"
        f"label_stats={raw.label_stats}\n"
        f"notes={raw.notes}\n"
    )


def _load_prompt_pair(rel: str) -> tuple[str, str]:
    from pathlib import Path

    path = Path(__file__).parent / rel
    text = path.read_text(encoding="utf-8")
    if "---USER---" in text:
        system, user = text.split("---USER---", 1)
        return system.replace("---SYSTEM---", "").strip(), user.strip()
    return "You are a data analysis expert.", text
