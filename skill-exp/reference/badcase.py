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
    plans_per_problem: int = 3,
) -> list[Plan]:
    """
    After clusters exist: map symptom → 2–3 verifiable actions from bundled
    `tricks.py` / `tricks_catalog.md` (data_clean / label_clean / train_recipe).
    Rank later via preference.pairwise / tournament.
    """
    from .tricks import enrich_cluster_plans, render_plan_md

    _ = ask  # refine wording via LLM before tournament if needed
    plans = enrich_cluster_plans(clusters, actions_per_cluster=plans_per_problem)
    # Attach rendered markdown for agent to write content/exp/.../plans/P*.md
    for p in plans:
        p.meta["plan_md"] = render_plan_md(p)
    return plans
