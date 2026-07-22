"""Model tier routing for the multi-agent lab.

Simple / mechanical tasks → fast models.
Judgment & drafting → standard.
High-stakes decisions & long-form writing → deep.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelTier(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    DEEP = "deep"


# Default role → tier (override via content/lab/<id>/routing.yaml or user message)
ROLE_DEFAULT_TIER: dict[str, ModelTier] = {
    "brain": ModelTier.DEEP,
    "retrieve": ModelTier.STANDARD,
    "plan": ModelTier.STANDARD,
    "verify": ModelTier.STANDARD,
    "experiment": ModelTier.STANDARD,
    "accept": ModelTier.DEEP,
    "write": ModelTier.DEEP,
    "critique": ModelTier.STANDARD,
    "reflect": ModelTier.STANDARD,
    "draw": ModelTier.FAST,
    "router": ModelTier.FAST,
    "formatter": ModelTier.FAST,
    "status": ModelTier.FAST,
}

# Task-type overrides (more specific than role)
TASK_TIER: dict[str, ModelTier] = {
    "parse_user_goal": ModelTier.FAST,
    "emit_task_card": ModelTier.FAST,
    "format_json": ModelTier.FAST,
    "check_file_exists": ModelTier.FAST,
    "screen_label": ModelTier.FAST,
    "rank_intent_clean": ModelTier.FAST,
    "query_rewrite": ModelTier.STANDARD,
    "literature_matrix": ModelTier.STANDARD,
    "draft_plans": ModelTier.STANDARD,
    "mini_verify_judge": ModelTier.STANDARD,
    "launch_train": ModelTier.STANDARD,
    "eval_metrics": ModelTier.STANDARD,
    "hard_gate_decide": ModelTier.DEEP,
    "accept_or_reject": ModelTier.DEEP,
    "paper_section": ModelTier.DEEP,
    "brain_dispatch": ModelTier.DEEP,
    "novelty_kill": ModelTier.DEEP,
}


@dataclass
class ModelSlot:
    """User-filled endpoint for a tier — never invent API keys."""

    tier: ModelTier
    name: str = ""
    endpoint_hint: str = ""
    notes: str = ""


@dataclass
class RoutingTable:
    """Maps tiers to concrete models supplied by the user / host runtime."""

    slots: dict[str, ModelSlot] = field(default_factory=dict)
    role_overrides: dict[str, str] = field(default_factory=dict)  # role → tier name

    def resolve(self, *, role: str = "", task: str = "") -> ModelTier:
        if task and task in TASK_TIER:
            return TASK_TIER[task]
        if role and role in self.role_overrides:
            try:
                return ModelTier(self.role_overrides[role])
            except ValueError:
                pass
        if role and role in ROLE_DEFAULT_TIER:
            return ROLE_DEFAULT_TIER[role]
        return ModelTier.STANDARD

    def slot_for(self, tier: ModelTier) -> ModelSlot | None:
        return self.slots.get(tier.value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slots": {
                k: {"tier": s.tier.value, "name": s.name, "endpoint_hint": s.endpoint_hint, "notes": s.notes}
                for k, s in self.slots.items()
            },
            "role_overrides": dict(self.role_overrides),
            "role_defaults": {k: v.value for k, v in ROLE_DEFAULT_TIER.items()},
            "task_tiers": {k: v.value for k, v in TASK_TIER.items()},
        }


def default_routing_hints() -> dict[str, str]:
    """Human-readable suggestions — host maps to actual models."""
    return {
        "fast": "low-latency / cheap (status, JSON format, intent strip, screen labels)",
        "standard": "balanced reasoning (retrieve, plan, verify, critique, reflect)",
        "deep": "strongest available (brain dispatch, accept, paper write, novelty)",
    }


def recommend_tier(role: str = "", task: str = "") -> dict[str, Any]:
    table = RoutingTable()
    tier = table.resolve(role=role, task=task)
    return {
        "role": role or None,
        "task": task or None,
        "tier": tier.value,
        "hint": default_routing_hints()[tier.value],
    }
