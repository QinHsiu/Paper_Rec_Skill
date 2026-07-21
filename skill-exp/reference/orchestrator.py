"""
/exp_loop orchestrator — wires modules into:
  analysis([plan]) → clean → mini_validation → training → evaluation → next-step
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from .badcase import cluster_badcases, collect_badcases, plans_from_clusters
from .data_report import build_verified_data_report
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
) -> list[RoundLog]:
    """
    Self-loop until target_score met or rounds exhausted / no promotable plan.
    Persist under content/exp/<experiment_id>/rounds/round-NN.md (agent writes files).
    """
    ptv = ptv or PTVConfig()
    root = Path(content_root) / experiment_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "rounds").mkdir(exist_ok=True)
    (root / "plans").mkdir(exist_ok=True)

    data_report = build_verified_data_report(
        task_name, task_desc, analysis_split, tools, ask
    )
    (root / "analysis_report.md").write_text(data_report, encoding="utf-8")

    logs: list[RoundLog] = []
    for n in range(1, max_rounds + 1):
        rows = get_eval_rows()
        bad = collect_badcases(rows)
        clusters = cluster_badcases(bad, ask)
        # Analyze → clusters → symptom → 2–3 catalog actions (bundled tricks)
        seed_plans = plans_from_clusters(clusters, ask, plans_per_problem=3)

        def generate(_tn, _td, _dr, m: int) -> list[Plan]:
            # Prefer analysis-derived plans; pad/truncate to m
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
                "plan": cur,  # revised plan after mini cycles — must feed full_train_eval
                "promote_to_full_train": last.promote_to_full_train,
                "mini_history": [h.__dict__ for h in hist],
            }

        step = predict_then_verify_step(
            task_name,
            task_desc,
            data_report,
            target,
            ask,
            generate,
            mini_verify,
            full_train_eval,
            cfg=ptv,
        )

        decision = "stop" if step.target_met else "continue"
        if not step.verified:
            decision = "stop"

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
            },
            decision=decision,
        )
        logs.append(round_log)
        _write_round_md(root / "rounds" / f"round-{n:02d}.md", round_log)

        if decision == "stop":
            break

        # refresh data report lightly each round (optional)
        data_report = build_verified_data_report(
            task_name, task_desc, analysis_split, tools, ask
        )

    _write_final(root / "final_report.md", target, logs)
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


def _write_final(path: Path | str, target: TargetScore, logs: list[RoundLog]) -> None:
    path = Path(path)
    met = any(r.evaluation.get("target_met") for r in logs)
    lines = [
        f"# Final Experiment Report",
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
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
