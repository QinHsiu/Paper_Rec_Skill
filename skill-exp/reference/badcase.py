"""
Badcase analysis → diverse clusters → special questions → multi-plans.

Maps to Exp_Sandbox:
  exp_result_analysis[badcase_sets → gen_analysis_cluster → special_question → solution_plan]
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .types import AskLLM, Cluster, Plan


def collect_badcases(eval_rows: Iterable[dict[str, Any]], *, fail_key: str = "correct") -> list[dict]:
    """eval_rows: [{id, input, pred, gold, score, correct:bool, tags?}]"""
    return [r for r in eval_rows if not r.get(fail_key, True)]


def cluster_badcases(
    badcases: list[dict],
    ask: AskLLM,
    *,
    min_clusters: int = 3,
    max_clusters: int = 12,
) -> list[Cluster]:
    """
    PSEUDOCODE clustering:
      1) heuristic tags (error type / length / modality) if present
      2) else ask LLM to assign cluster labels with diversity constraint
      3) aggregate counts; keep long-tail clusters (diversity), not only top mass
    """
    if not badcases:
        return []
    # --- heuristic fallback ---
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in badcases:
        key = row.get("error_type") or row.get("tag") or "misc"
        buckets[str(key)].append(row)

    if len(buckets) < min_clusters:
        # agent: call ask() to refine labels for diversity
        _ = ask  # placeholder — wire LLM clustering prompt in production
        pass

    total = max(sum(len(v) for v in buckets.values()), 1)
    clusters: list[Cluster] = []
    for i, (label, rows) in enumerate(sorted(buckets.items(), key=lambda x: -len(x[1]))):
        if i >= max_clusters:
            break
        clusters.append(
            Cluster(
                cluster_id=f"C{i+1}",
                label=label,
                count=len(rows),
                share=len(rows) / total,
                example_ids=[str(r.get("id")) for r in rows[:5]],
                special_question=f"Why does the model fail on '{label}'?",
            )
        )
    return clusters


def special_questions_from_clusters(clusters: list[Cluster]) -> list[str]:
    """Name concrete sub-problems (e.g. OCR weak on handwritten pinyin)."""
    return [c.special_question if c.special_question else f"Improve {c.label}" for c in clusters]


def plans_from_clusters(
    clusters: list[Cluster],
    ask: AskLLM,
    *,
    plans_per_problem: int = 2,
) -> list[Plan]:
    """
    For each priority cluster (by share), propose multiple plans:
      data_clean: increase/remove/modify/insert
      label_clean: self_sampling / use_other_model
    Rank later via preference.pairwise / tournament.
    """
    plans: list[Plan] = []
    # Priority: high share first, but keep at least one long-tail cluster
    ordered = sorted(clusters, key=lambda c: c.share, reverse=True)
    if len(ordered) >= 2:
        ordered = ordered[:-1] + [min(clusters, key=lambda c: c.share)]  # diversity inject

    pid = 0
    for c in ordered:
        for j in range(plans_per_problem):
            pid += 1
            plans.append(
                Plan(
                    plan_id=f"P{pid}",
                    hypothesis=f"Fix cluster {c.label} via strategy#{j+1}",
                    actions=[
                        f"focus_cluster={c.cluster_id}",
                        "data_clean|label_clean (choose concrete ops)",
                    ],
                    expected_gain=round(0.02 + c.share * 0.1 - j * 0.005, 4),
                    cost=0.3 + 0.1 * j,
                    risk="distribution shift / label noise",
                    special_questions=[c.special_question],
                    meta={"cluster_id": c.cluster_id, "share": c.share},
                )
            )
    # Agent should refine hypotheses via ask(LLM) before tournament
    _ = ask
    return plans
