"""
Badcase analysis → diverse clusters → special questions → multi-plans.

Maps to Exp_Sandbox:
  exp_result_analysis[badcase_sets → gen_analysis_cluster → special_question → solution_plan]
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any, Iterable

from .types import AskLLM, Cluster, Plan


_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


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
    Clustering:
      1) heuristic tags (error type / length / modality) if present
      2) if too few buckets, ask LLM to assign diverse labels
      3) aggregate counts; keep long-tail clusters (diversity), not only top mass
    """
    if not badcases:
        return []
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in badcases:
        key = row.get("error_type") or row.get("tag") or "misc"
        buckets[str(key)].append(row)

    if len(buckets) < min_clusters:
        buckets = _llm_refine_buckets(badcases, ask, buckets, min_clusters=min_clusters)

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


def _llm_refine_buckets(
    badcases: list[dict],
    ask: AskLLM,
    buckets: dict[str, list[dict]],
    *,
    min_clusters: int,
) -> dict[str, list[dict]]:
    """Ask LLM for per-id labels when heuristic diversity is too low."""
    sample = []
    for r in badcases[:40]:
        sample.append(
            {
                k: r.get(k)
                for k in ("id", "pred", "gold", "error_type", "tag", "input")
                if k in r
            }
        )
    system = (
        "You cluster evaluation failures into diverse error types. "
        f"Return JSON only: {{\"labels\": {{\"<id>\": \"<short_label>\", ...}}}} "
        f"with at least {min_clusters} distinct labels when possible."
    )
    user = "Badcases:\n" + json.dumps(sample, ensure_ascii=False)
    try:
        raw = ask(system, user)
    except Exception:
        return buckets
    labels = _parse_label_map(raw)
    if not labels:
        return buckets
    refined: dict[str, list[dict]] = defaultdict(list)
    for row in badcases:
        rid = str(row.get("id", ""))
        lab = labels.get(rid) or row.get("error_type") or row.get("tag") or "misc"
        refined[str(lab)].append(row)
    return refined if len(refined) >= len(buckets) else buckets


def _parse_label_map(text: str) -> dict[str, str]:
    if not text:
        return {}
    blob = text
    m = _JSON_OBJ_RE.search(text)
    if m:
        blob = m.group(0)
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    labels = data.get("labels", data)
    if not isinstance(labels, dict):
        return {}
    return {str(k): str(v) for k, v in labels.items()}


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
    from .model_select import (
        ModelSelectSpec,
        infer_roles_from_actions,
        needs_model_select,
        render_model_select_md,
    )
    from .plan_template import merge_model_block
    from .tricks import enrich_cluster_plans, render_plan_md

    _ = ask  # refine wording via LLM before tournament if needed
    plans = enrich_cluster_plans(clusters, actions_per_cluster=plans_per_problem)
    # Attach rendered markdown for agent to write content/exp/.../plans/P*.md
    for p in plans:
        md = render_plan_md(p)
        blob = " ".join(p.actions) + " " + p.hypothesis + " " + str(p.meta.get("symptom", ""))
        fam = str(p.meta.get("family", ""))
        if needs_model_select(blob) or fam in ("label_clean", "train_recipe"):
            roles = infer_roles_from_actions(p.actions + [fam, str(p.meta.get("symptom", ""))])
            if roles:
                blocks = "\n".join(
                    render_model_select_md(
                        ModelSelectSpec(
                            role=r,
                            task_hint=p.hypothesis,
                            family=None,  # agent fills after board + family search
                        )
                    )
                    for r in roles
                )
                md = merge_model_block(md, blocks)
                p.meta["needs_model_select"] = True
                p.meta["model_roles"] = roles
        p.meta["plan_md"] = md
    return plans
