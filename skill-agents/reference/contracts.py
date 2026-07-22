"""Task cards + run ledger for the multi-agent lab."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .model_routing import ModelTier, RoutingTable, recommend_tier


class AgentRole(str, Enum):
    BRAIN = "brain"
    RETRIEVE = "retrieve"
    PLAN = "plan"
    VERIFY = "verify"
    EXPERIMENT = "experiment"
    ACCEPT = "accept"
    WRITE = "write"
    CRITIQUE = "critique"
    REFLECT = "reflect"
    DRAW = "draw"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class TaskCard:
    """Unit of work issued by Brain to a role agent."""

    role: str
    task: str
    goal: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs_expected: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    model_tier: str = "standard"
    status: str = TaskStatus.PENDING.value
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LabRun:
    run_id: str
    title: str
    hypothesis: str = ""
    target_score: dict[str, Any] = field(default_factory=dict)
    thread_id: str = ""
    stage: str = "init"  # init|retrieve|plan|verify|experiment|accept|write|done|blocked
    tasks: list[TaskCard] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    routing: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "title": self.title,
            "hypothesis": self.hypothesis,
            "target_score": self.target_score,
            "thread_id": self.thread_id,
            "stage": self.stage,
            "tasks": [t.to_dict() for t in self.tasks],
            "decisions": self.decisions,
            "routing": self.routing,
            "created_at": self.created_at,
        }


def lab_root(content_root: Path) -> Path:
    return Path(content_root) / "lab"


def run_dir(content_root: Path, run_id: str) -> Path:
    return lab_root(content_root) / run_id


def create_run(
    content_root: Path,
    *,
    title: str,
    hypothesis: str = "",
    target_score: dict[str, Any] | None = None,
    thread_id: str = "",
    routing: RoutingTable | None = None,
) -> LabRun:
    rid = uuid.uuid4().hex[:12]
    run = LabRun(
        run_id=rid,
        title=title,
        hypothesis=hypothesis,
        target_score=target_score or {},
        thread_id=thread_id,
        routing=(routing or RoutingTable()).to_dict(),
    )
    d = run_dir(content_root, rid)
    d.mkdir(parents=True, exist_ok=True)
    (d / "tasks").mkdir(exist_ok=True)
    (d / "artifacts").mkdir(exist_ok=True)
    save_run(content_root, run)
    (d / "README.md").write_text(
        f"# Lab run `{rid}`\n\n**{title}**\n\nHypothesis: {hypothesis or '_(tbd)_'}\n",
        encoding="utf-8",
    )
    return run


def save_run(content_root: Path, run: LabRun) -> Path:
    path = run_dir(content_root, run.run_id) / "run.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_run(content_root: Path, run_id: str) -> LabRun:
    data = json.loads((run_dir(content_root, run_id) / "run.json").read_text(encoding="utf-8"))
    tasks = [TaskCard(**t) for t in data.get("tasks") or []]
    return LabRun(
        run_id=data["run_id"],
        title=data.get("title") or "",
        hypothesis=data.get("hypothesis") or "",
        target_score=data.get("target_score") or {},
        thread_id=data.get("thread_id") or "",
        stage=data.get("stage") or "init",
        tasks=tasks,
        decisions=list(data.get("decisions") or []),
        routing=data.get("routing") or {},
        created_at=float(data.get("created_at") or time.time()),
    )


def issue_task(
    run: LabRun,
    *,
    role: str,
    task: str,
    goal: str,
    inputs: dict[str, Any] | None = None,
    outputs_expected: list[str] | None = None,
    depends_on: list[str] | None = None,
    routing: RoutingTable | None = None,
) -> TaskCard:
    table = routing or RoutingTable()
    tier = table.resolve(role=role, task=task)
    card = TaskCard(
        role=role,
        task=task,
        goal=goal,
        inputs=inputs or {},
        outputs_expected=outputs_expected or [],
        depends_on=depends_on or [],
        model_tier=tier.value,
    )
    run.tasks.append(card)
    run.decisions.append(
        {
            "type": "dispatch",
            "task_id": card.task_id,
            "role": role,
            "task": task,
            "model_tier": tier.value,
            "routing_hint": recommend_tier(role=role, task=task).get("hint"),
            "at": time.time(),
        }
    )
    return card


# Default pipeline stages Brain should walk (can skip/reorder)
DEFAULT_PIPELINE: list[dict[str, str]] = [
    {"stage": "retrieve", "role": "retrieve", "task": "query_rewrite", "goal": "Gather grounded literature for the hypothesis"},
    {"stage": "plan", "role": "plan", "task": "draft_plans", "goal": "Propose 2–3 verifiable experiment plans"},
    {"stage": "verify", "role": "verify", "task": "mini_verify_judge", "goal": "Mini-verify best plan on target subset"},
    {"stage": "experiment", "role": "experiment", "task": "launch_train", "goal": "Run full train/eval via exp-sandbox protocols"},
    {"stage": "accept", "role": "accept", "task": "accept_or_reject", "goal": "Hard-gate metrics, repro, stats, claims"},
    {"stage": "write", "role": "write", "task": "paper_section", "goal": "Draft paper sections only from accepted evidence"},
    {"stage": "reflect", "role": "reflect", "task": "brain_dispatch", "goal": "Outer-loop DEEPEN/BROADEN/PIVOT/CONCLUDE"},
]


def bootstrap_pipeline(run: LabRun, routing: RoutingTable | None = None) -> list[TaskCard]:
    """Issue the default stage cards (Brain may later cancel/skip)."""
    cards = []
    prev_id = None
    for step in DEFAULT_PIPELINE:
        deps = [prev_id] if prev_id else []
        card = issue_task(
            run,
            role=step["role"],
            task=step["task"],
            goal=step["goal"],
            inputs={"stage": step["stage"], "run_id": run.run_id},
            depends_on=deps,
            routing=routing,
        )
        prev_id = card.task_id
        cards.append(card)
    run.stage = "retrieve"
    return cards
