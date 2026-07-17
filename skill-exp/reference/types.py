"""Shared types for Exp_Sandbox reference modules (agent-facing stubs)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class Split(str, Enum):
    TRAIN = "train"
    EVAL = "eval"


@dataclass
class TargetScore:
    task: str
    eval_set: str
    metric: str
    threshold: float
    secondary: list[dict[str, Any]] = field(default_factory=list)
    higher_is_better: bool = True

    def met(self, value: float) -> bool:
        return value >= self.threshold if self.higher_is_better else value <= self.threshold


@dataclass
class ToolBundle:
    """User-provided tool/function context — never invent secrets."""

    closed_models: list[dict[str, Any]] = field(default_factory=list)
    open_models: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    train_infra: list[dict[str, Any]] = field(default_factory=list)
    analysis_tools: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""


@dataclass
class Plan:
    plan_id: str
    hypothesis: str
    actions: list[str]  # data_clean / label_clean steps
    expected_gain: float  # predicted metric delta
    cost: float  # relative cost 0..1
    risk: str = ""
    special_questions: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreferenceVote:
    winner_index: int  # 0 or 1 in pairwise
    confidence: float  # 0..1
    reasoning: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Cluster:
    cluster_id: str
    label: str  # e.g. "handwritten_pinyin_ocr_weak"
    count: int
    share: float
    example_ids: list[str]
    special_question: str


@dataclass
class RoundLog:
    round_idx: int
    analysis_summary: str
    plans: list[Plan]
    chosen: Optional[Plan]
    mini_validation: dict[str, Any]
    training: dict[str, Any]
    evaluation: dict[str, Any]
    decision: str  # continue | stop


# Hooks the agent wires to real infra / model calls
AskLLM = Callable[[str, str], str]  # (system, user) -> text
RunCmd = Callable[[str], str]  # shell / remote train command
