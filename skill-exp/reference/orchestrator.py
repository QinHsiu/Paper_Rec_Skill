"""
/exp_loop orchestrator — wires modules into:
  analysis([plan]) → clean → mini_validation → training → evaluation → next-step
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .badcase import cluster_badcases, collect_badcases, plans_from_clusters
from .data_report import build_verified_data_report
from .eval_hook import write_eval_bundle
from .exp_tree import expand_from_best, load_tree, mark_buggy, ready_for_next_stage, save_tree
from .mini_eval import cycle_until_stable
from .predict_then_verify import PTVConfig, predict_then_verify_step
from .types import AskLLM, Plan, RoundLog, Split, TargetScore, ToolBundle


EvalRowsFn = Callable[[], list[dict[str, Any]]]
ApplyPlanFn = Callable[[Plan], dict[str, Any]]
EvalSliceFn = Callable[[], dict[str, float]]
ReviseFn = Callable[[Plan, Any], Plan]
FullTrainEvalFn = Callable[[Plan], dict[str, Any]]


def run_exp_loop(
    experiment_id: str,
    task_name: str,
    task_desc: str,
    target: TargetScore,
    tools: ToolBundle,
    ask: AskLLM,
    get_eval_rows: EvalRowsFn,
    apply_plan: ApplyPlanFn,
    eval_slice: EvalSliceFn,
    revise_plan: ReviseFn,
    full_train_eval: FullTrainEvalFn,
    *,
    content_root: str | Path = "content/exp",
    max_rounds: int = 8,
    ptv: PTVConfig | None = None,
    analysis_split: Split = Split.EVAL,
    update_exp_tree: bool = True,
) -> list[RoundLog]:
    """
    Self-loop until target_score met or rounds exhausted / no promotable plan.
    Persist under content/exp/<experiment_id>/rounds/round-NN.md (agent writes files).

    After each full train/eval, writes ``metrics/summary.json`` (number-verify ready)
    and optionally updates ``trace/exp_tree.json``.
    """
    ptv = ptv or PTVConfig()
    root = Path(content_root) / experiment_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "rounds").mkdir(exist_ok=True)
    (root / "plans").mkdir(exist_ok=True)
    (root / "trace").mkdir(exist_ok=True)

    data_report = build_verified_data_report(
        task_name, task_desc, analysis_split, tools, ask
    )
    (root / "analysis_report.md").write_text(data_report, encoding="utf-8")

    tree = load_tree(content_root, experiment_id) if update_exp_tree else None
    maximize = bool(getattr(target, "higher_is_better", True))

    logs: list[RoundLog] = []
    for n in range(1, max_rounds + 1):
        rows = get_eval_rows()
        bad = collect_badcases(rows)
        clusters = cluster_badcases(bad, ask)
        seed_plans = plans_from_clusters(clusters, ask, plans_per_problem=3)

        def generate(_tn, _td, _dr, m: int) -> list[Plan]:
            plans = list(seed_plans)
            while len(plans) < m:
                plans.append(
                    Plan(
                        plan_id=f"GEN{len(plans)+1}",
                        hypothesis="LLM-generated alternative",
                        actions=["data_clean|label_clean"],
                        expected_gain=0.01,
                        cost=0.5,
                        meta={"source": "llm:pad"},
                    )
                )
            return plans[:m]

        def mini_verify(plan: Plan) -> dict[str, Any]:
            cur, hist = cycle_until_stable(
                plan, target, apply_plan, eval_slice, revise_plan
            )
            if not hist:
                return {
                    "plan_id": cur.plan_id,
                    "plan": cur,
                    "promote_to_full_train": False,
                    "mini_history": [],
                }
            last = hist[-1]
            return {
                "plan_id": cur.plan_id,
                "plan": cur,
                "promote_to_full_train": last.promote_to_full_train,
                "target_subset": getattr(last, "target_subset", "")
                or cur.meta.get("target_subset"),
                "subset_gain": getattr(last, "subset_gain", None),
                "global_delta": getattr(last, "global_delta", None),
                "mini_history": [h.__dict__ for h in hist],
            }

        def full_train_eval_wrapped(plan: Plan) -> dict[str, Any]:
            result = full_train_eval(plan) or {}
            if not isinstance(result, dict):
                result = {"metrics": {"value": result}}
            metrics = dict(result.get("metrics") or result)
            bundle = write_eval_bundle(
                experiment_id,
                metrics if isinstance(metrics, dict) else {"value": metrics},
                content_root=content_root,
                target={
                    "metric": target.metric,
                    "threshold": target.threshold,
                    "eval_set": getattr(target, "eval_set", ""),
                    "direction": "maximize" if getattr(target, "higher_is_better", True) else "minimize",
                    "higher_is_better": getattr(target, "higher_is_better", True),
                },
                plan_id=plan.plan_id,
                run_id=f"round-{n:02d}",
                stratified=result.get("stratified"),
            )
            result = dict(result)
            result["eval_bundle"] = bundle

            if tree is not None:
                primary = bundle.get("primary_value")
                as_ablation = "ablation" in " ".join(plan.actions or []).lower() or bool(
                    plan.meta.get("ablation")
                )
                node = expand_from_best(
                    tree,
                    plan_id=plan.plan_id,
                    metric=float(primary) if primary is not None else None,
                    metric_name=str(bundle.get("primary_metric") or target.metric),
                    as_ablation=as_ablation,
                    maximize=maximize,
                )
                if result.get("buggy") or result.get("failed"):
                    mark_buggy(
                        tree,
                        node.id,
                        notes=str(result.get("error") or "train/eval failed"),
                    )
                save_tree(tree, content_root)
                result["exp_tree_node"] = node.id
                result["exp_tree_ready"] = ready_for_next_stage(tree, maximize=maximize)

            return result

        step = predict_then_verify_step(
            task_name,
            task_desc,
            data_report,
            target,
            ask,
            generate,
            mini_verify,
            full_train_eval_wrapped,
            cfg=ptv,
        )

        decision = "stop" if step.target_met else "continue"
        if not step.verified:
            decision = "stop"

        tree_ready = None
        if tree is not None:
            tree_ready = ready_for_next_stage(tree, maximize=maximize)

        round_log = RoundLog(
            round_idx=n,
            analysis_summary=f"badcases={len(bad)} clusters={len(clusters)}",
            plans=step.ranked_plans,
            chosen=step.best_plan,
            mini_validation={"verified": step.verified},
            training={"best_metrics": step.best_metrics},
            evaluation={
                "target": target.__dict__,
                "target_met": step.target_met,
                "exp_tree_ready": tree_ready,
            },
            decision=decision,
        )
        logs.append(round_log)
        _write_round_md(root / "rounds" / f"round-{n:02d}.md", round_log)

        if decision == "stop":
            break

        data_report = build_verified_data_report(
            task_name, task_desc, analysis_split, tools, ask
        )

    _write_final(root / "final_report.md", target, logs, tree)
    return logs


def _write_round_md(path: Path | str, log: RoundLog) -> None:
    path = Path(path)
    chosen = log.chosen.plan_id if log.chosen else "None"
    path.write_text(
        f"## Round {log.round_idx}\n"
        f"- analysis_summary: {log.analysis_summary}\n"
        f"- plans: {[p.plan_id for p in log.plans]}\n"
        f"- chosen: {chosen}\n"
        f"- mini_validation: {log.mini_validation}\n"
        f"- training: {log.training}\n"
        f"- evaluation: {log.evaluation}\n"
        f"- decision: {log.decision}\n",
        encoding="utf-8",
    )


def _write_final(
    path: Path | str,
    target: TargetScore,
    logs: list[RoundLog],
    tree: Any = None,
) -> None:
    path = Path(path)
    met = any(r.evaluation.get("target_met") for r in logs)
    lines = [
        "# Final Experiment Report",
        f"- target_score met: {met}",
        f"- target: {target}",
        f"- rounds: {len(logs)}",
        "",
        "## Rounds",
    ]
    for r in logs:
        lines.append(
            f"- R{r.round_idx}: chosen={getattr(r.chosen, 'plan_id', None)} "
            f"met={r.evaluation.get('target_met')} decision={r.decision}"
        )
    if tree is not None:
        from .exp_tree import render_tree_md

        lines.extend(["", render_tree_md(tree)])
        lines.append(
            "\nAfter drafting Results, run number-verify against this exp dir "
            "(metrics/summary.json was written each eval)."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
