"""Lightweight experiment tree (draft → improve → ablation) for /exp_loop.

Persists ``content/exp/<id>/trace/exp_tree.json``. Not a full code-search
agent — tracks plan nodes, metrics, buggy flags, and stage readiness.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Stage = Literal["draft", "improve", "ablation", "debug"]


@dataclass
class ExpNode:
    id: str
    parent: str | None = None
    stage: Stage = "draft"
    plan_id: str = ""
    metric: float | None = None
    metric_name: str = ""
    buggy: bool = False
    notes: str = ""
    children: list[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class ExpTree:
    experiment_id: str
    nodes: dict[str, ExpNode] = field(default_factory=dict)
    root_id: str | None = None
    stage: Stage = "draft"
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "root_id": self.root_id,
            "stage": self.stage,
            "updated_at": self.updated_at,
            "nodes": {k: asdict(v) for k, v in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpTree":
        nodes = {
            nid: ExpNode(**{**nd, "children": list(nd.get("children") or [])})
            for nid, nd in (data.get("nodes") or {}).items()
        }
        return cls(
            experiment_id=str(data.get("experiment_id") or ""),
            nodes=nodes,
            root_id=data.get("root_id"),
            stage=data.get("stage") or "draft",  # type: ignore[arg-type]
            updated_at=str(data.get("updated_at") or ""),
        )


def tree_path(content_root: str | Path, experiment_id: str) -> Path:
    return Path(content_root) / experiment_id / "trace" / "exp_tree.json"


def load_tree(content_root: str | Path, experiment_id: str) -> ExpTree:
    path = tree_path(content_root, experiment_id)
    if not path.is_file():
        return ExpTree(experiment_id=experiment_id)
    return ExpTree.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_tree(tree: ExpTree, content_root: str | Path) -> Path:
    path = tree_path(content_root, tree.experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.updated_at = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(tree.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _new_id(tree: ExpTree, prefix: str) -> str:
    n = len(tree.nodes) + 1
    while f"{prefix}{n}" in tree.nodes:
        n += 1
    return f"{prefix}{n}"


def add_node(
    tree: ExpTree,
    *,
    plan_id: str,
    metric: float | None = None,
    metric_name: str = "",
    stage: Stage | None = None,
    parent: str | None = None,
    buggy: bool = False,
    notes: str = "",
) -> ExpNode:
    stage = stage or tree.stage
    parent = parent if parent is not None else tree.root_id
    nid = _new_id(tree, "N")
    node = ExpNode(
        id=nid,
        parent=parent,
        stage=stage,
        plan_id=plan_id,
        metric=metric,
        metric_name=metric_name,
        buggy=buggy,
        notes=notes,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    tree.nodes[nid] = node
    if tree.root_id is None:
        tree.root_id = nid
    elif parent and parent in tree.nodes:
        kids = tree.nodes[parent].children
        if nid not in kids:
            kids.append(nid)
    return node


def mark_buggy(tree: ExpTree, node_id: str, notes: str = "") -> ExpNode:
    node = tree.nodes[node_id]
    node.buggy = True
    if notes:
        node.notes = (node.notes + "; " if node.notes else "") + notes
    return node


def best_non_buggy(tree: ExpTree, *, maximize: bool = True) -> ExpNode | None:
    cands = [n for n in tree.nodes.values() if not n.buggy and n.metric is not None]
    if not cands:
        return None
    return max(cands, key=lambda n: n.metric if maximize else -(n.metric or 0.0))  # type: ignore[operator]


def expand_from_best(
    tree: ExpTree,
    *,
    plan_id: str,
    metric: float | None = None,
    metric_name: str = "",
    as_ablation: bool = False,
    maximize: bool = True,
) -> ExpNode:
    """Attach a child under the best non-buggy node (or create root)."""
    parent_node = best_non_buggy(tree, maximize=maximize)
    parent = parent_node.id if parent_node else None
    stage: Stage = "ablation" if as_ablation else ("improve" if parent else "draft")
    if as_ablation:
        tree.stage = "ablation"
    elif parent:
        tree.stage = "improve"
    return add_node(
        tree,
        plan_id=plan_id,
        metric=metric,
        metric_name=metric_name,
        stage=stage,
        parent=parent,
    )


def ready_for_next_stage(
    tree: ExpTree,
    *,
    min_nodes: int = 2,
    require_improvement: bool = True,
    maximize: bool = True,
) -> dict[str, Any]:
    """Heuristic stage gate: enough healthy nodes and metric progress."""
    healthy = [n for n in tree.nodes.values() if not n.buggy]
    buggy_open = [n for n in tree.nodes.values() if n.buggy]
    best = best_non_buggy(tree, maximize=maximize)
    root = tree.nodes.get(tree.root_id or "") if tree.root_id else None
    improved = False
    if best and root and root.metric is not None and best.metric is not None:
        improved = (best.metric > root.metric) if maximize else (best.metric < root.metric)
    elif best and root is None:
        improved = True

    ready = len(healthy) >= min_nodes and not buggy_open and (improved if require_improvement else True)
    reason = []
    if len(healthy) < min_nodes:
        reason.append(f"need>={min_nodes}_healthy_nodes")
    if buggy_open:
        reason.append("open_buggy_nodes")
    if require_improvement and not improved:
        reason.append("no_metric_improvement_vs_root")
    if ready:
        reason = ["ok"]
    return {
        "ready": ready,
        "reason": reason,
        "healthy_n": len(healthy),
        "buggy_n": len(buggy_open),
        "best_id": best.id if best else None,
        "best_metric": best.metric if best else None,
        "stage": tree.stage,
    }


def render_tree_md(tree: ExpTree) -> str:
    lines = [f"# Experiment tree — {tree.experiment_id}", f"stage: `{tree.stage}`", ""]

    def walk(nid: str, depth: int = 0) -> None:
        n = tree.nodes[nid]
        flag = "BUG" if n.buggy else "OK"
        met = f"{n.metric:.4f}" if n.metric is not None else "—"
        pad = "  " * depth
        lines.append(f"{pad}- [{flag}] `{n.id}` [{n.stage}] plan={n.plan_id} metric={met}")
        for c in n.children:
            if c in tree.nodes:
                walk(c, depth + 1)

    if tree.root_id and tree.root_id in tree.nodes:
        walk(tree.root_id)
    else:
        for nid in tree.nodes:
            if tree.nodes[nid].parent is None:
                walk(nid)
    return "\n".join(lines) + "\n"
