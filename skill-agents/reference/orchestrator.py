"""Brain-facing orchestrator: create run, dispatch pipeline, record results."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import (
    DEFAULT_PIPELINE,
    LabRun,
    TaskCard,
    TaskStatus,
    bootstrap_pipeline,
    create_run,
    issue_task,
    load_run,
    run_dir,
    save_run,
)
from .model_routing import RoutingTable, recommend_tier


def init_lab_run(
    content_root: Path | str,
    *,
    title: str,
    hypothesis: str = "",
    target_score: dict[str, Any] | None = None,
    thread_id: str = "",
    bootstrap: bool = True,
) -> dict[str, Any]:
    root = Path(content_root)
    run = create_run(
        root,
        title=title,
        hypothesis=hypothesis,
        target_score=target_score,
        thread_id=thread_id,
    )
    if bootstrap:
        bootstrap_pipeline(run)
        save_run(root, run)
        _write_task_files(root, run)
    return {
        "run_id": run.run_id,
        "path": str(run_dir(root, run.run_id)),
        "stage": run.stage,
        "task_n": len(run.tasks),
        "tasks": [
            {
                "task_id": t.task_id,
                "role": t.role,
                "task": t.task,
                "model_tier": t.model_tier,
                "status": t.status,
            }
            for t in run.tasks
        ],
    }


def _write_task_files(content_root: Path, run: LabRun) -> None:
    tdir = run_dir(content_root, run.run_id) / "tasks"
    for t in run.tasks:
        (tdir / f"{t.task_id}_{t.role}.json").write_text(
            json.dumps(t.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def next_ready_tasks(run: LabRun) -> list[TaskCard]:
    done = {t.task_id for t in run.tasks if t.status == TaskStatus.DONE.value}
    ready = []
    for t in run.tasks:
        if t.status != TaskStatus.PENDING.value:
            continue
        if all(d in done for d in (t.depends_on or [])):
            ready.append(t)
    return ready


def mark_task(
    content_root: Path | str,
    run_id: str,
    task_id: str,
    *,
    status: str,
    result: dict[str, Any] | None = None,
    error: str = "",
    advance_stage: bool = True,
) -> dict[str, Any]:
    root = Path(content_root)
    run = load_run(root, run_id)
    card = next((t for t in run.tasks if t.task_id == task_id), None)
    if not card:
        return {"ok": False, "error": "unknown_task_id"}
    card.status = status
    if result is not None:
        card.result = result
    if error:
        card.error = error
    run.decisions.append(
        {
            "type": "task_update",
            "task_id": task_id,
            "status": status,
            "role": card.role,
        }
    )
    if advance_stage and status == TaskStatus.DONE.value:
        # move stage to next pending role's stage hint
        ready = next_ready_tasks(run)
        if ready:
            run.stage = str((ready[0].inputs or {}).get("stage") or ready[0].role)
        elif all(t.status in {TaskStatus.DONE.value, TaskStatus.SKIPPED.value} for t in run.tasks):
            run.stage = "done"
    if status == TaskStatus.BLOCKED.value:
        run.stage = "blocked"
    save_run(root, run)
    _write_task_files(root, run)
    art = run_dir(root, run_id) / "artifacts" / f"{task_id}_result.json"
    art.write_text(json.dumps({"status": status, "result": result or {}, "error": error}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "run_id": run_id, "task_id": task_id, "status": status, "stage": run.stage}


def status_summary(content_root: Path | str, run_id: str) -> dict[str, Any]:
    run = load_run(Path(content_root), run_id)
    by_status: dict[str, int] = {}
    for t in run.tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
    ready = next_ready_tasks(run)
    return {
        "run_id": run.run_id,
        "title": run.title,
        "stage": run.stage,
        "thread_id": run.thread_id or None,
        "counts": by_status,
        "ready": [
            {
                "task_id": t.task_id,
                "role": t.role,
                "task": t.task,
                "model_tier": t.model_tier,
                "routing": recommend_tier(role=t.role, task=t.task),
            }
            for t in ready
        ],
        "path": str(run_dir(Path(content_root), run_id)),
    }


def brain_decide(
    content_root: Path | str,
    run_id: str,
    *,
    decision: str,
    reason: str = "",
    extra_task: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a Brain decision; optionally inject an extra task card."""
    root = Path(content_root)
    run = load_run(root, run_id)
    run.decisions.append({"type": "brain", "decision": decision, "reason": reason})
    issued = None
    if extra_task:
        issued = issue_task(
            run,
            role=str(extra_task.get("role") or "critique"),
            task=str(extra_task.get("task") or "brain_dispatch"),
            goal=str(extra_task.get("goal") or reason or decision),
            inputs=dict(extra_task.get("inputs") or {}),
            depends_on=list(extra_task.get("depends_on") or []),
        )
    save_run(root, run)
    if issued:
        _write_task_files(root, run)
    return {
        "ok": True,
        "decision": decision,
        "extra_task_id": issued.task_id if issued else None,
        "stage": run.stage,
    }


def pipeline_blueprint() -> list[dict[str, str]]:
    return list(DEFAULT_PIPELINE)
