"""
Symptom → curated verifiable actions (bundled catalog).

Used AFTER analysis names a symptom. No external repo paths.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .types import Cluster, Plan


@dataclass(frozen=True)
class TrickAction:
    family: str  # data_clean | label_clean | train_recipe | eval_recipe
    summary: str
    mini_verify: str
    source: str


# Mirror of tricks_catalog.md (keep in sync).
CATALOG: dict[str, list[TrickAction]] = {
    "data_first": [
        TrickAction(
            "data_clean",
            "inspect: visualize labels + class/size distribution",
            "dist table + N-sample audit clean",
            "tricks:data_first#know_data",
        ),
        TrickAction(
            "train_recipe",
            "overfit_tiny: tiny subset, fixed seed, no random aug",
            "train error → ~0 (pipeline learnable)",
            "tricks:data_first#overfit_tiny",
        ),
        TrickAction(
            "data_clean",
            "unit_test_loader: batch=1 numeric check",
            "matches hand / reference values",
            "tricks:data_first#test_loader",
        ),
        TrickAction(
            "data_clean",
            "missing_impute: fill by type (const/mean·median·mode/ffill·bfill/KNN/regress); log columns",
            "no target leak; probe ≥ drop-row baseline or documented tradeoff",
            "tricks:data_first#missing_impute",
        ),
        TrickAction(
            "data_clean",
            "feature_corr: corr/MI vs label; drop near-dup or leaky columns",
            "val ↑ or same with fewer features; leakage checklist empty",
            "tricks:data_first#feature_corr",
        ),
    ],
    "overfitting": [
        TrickAction(
            "train_recipe",
            "regularize: dropout / weight-decay / early-stop on val",
            "train–val gap shrinks; best val ↑ or holds",
            "tricks:overfitting#reg",
        ),
        TrickAction(
            "data_clean",
            "increase: Flip/Cutout/Mixup or text synonym/back-translation",
            "probe ↑; global drop ≤ ε",
            "tricks:overfitting#aug",
        ),
        TrickAction(
            "train_recipe",
            "swa: stochastic weight averaging near end",
            "val more stable or ↑ at same budget",
            "tricks:overfitting#swa",
        ),
    ],
    "long_tail": [
        TrickAction(
            "data_clean",
            "increase: oversample / hard-neg mine rare buckets",
            "rare recall ↑; head Δ ≤ ε",
            "tricks:long_tail#resample",
        ),
        TrickAction(
            "train_recipe",
            "loss: focal / weighted CE / class-balanced",
            "macro or rare-class F1 ↑",
            "tricks:long_tail#loss",
        ),
        TrickAction(
            "train_recipe",
            "multi_loss: weighted mix; watch scale balance",
            "components descend without one dominating; probe ↑",
            "tricks:long_tail#multi_loss",
        ),
    ],
    "hard_subset": [
        TrickAction(
            "data_clean",
            "increase: add/synthesize samples for failing subset",
            "subset ↑; global not ↓ > ε",
            "tricks:hard_subset#focus_data",
        ),
        TrickAction(
            "train_recipe",
            "diff_lr: smaller LR backbone, larger head; freeze early if small data",
            "stabler converge; subset ↑",
            "tricks:hard_subset#diff_lr",
        ),
        TrickAction(
            "train_recipe",
            "domain_pt: domain MLM / similarity continued pretrain then finetune",
            "subset probe ↑",
            "tricks:hard_subset#domain_pt",
        ),
        TrickAction(
            "data_clean",
            "sim_hardneg: mine hard negs by cosine/KL/Wasserstein in emb space",
            "subset or ranking metric ↑; train loss still descends",
            "tricks:hard_subset#sim_hardneg",
        ),
    ],
    "underfit": [
        TrickAction(
            "train_recipe",
            "capacity_first: prove tiny-set overfit before deeper models",
            "tiny-set train error → ~0",
            "tricks:underfit#capacity_first",
        ),
        TrickAction(
            "train_recipe",
            "lr_sched: warmup; plateau×0.5 or cosine; scale LR with batch",
            "train loss ↓ and val ↑",
            "tricks:underfit#lr_sched",
        ),
        TrickAction(
            "train_recipe",
            "pretrain: load pretrained; avoid tiny final LR (~1e-5 floor)",
            "beats from-scratch on probe",
            "tricks:underfit#pretrain",
        ),
    ],
    "label_noise": [
        TrickAction(
            "data_clean",
            "remove: drop high-entropy / low-agreement samples",
            "cleaner subset ≥ noisy full on probe",
            "tricks:label_noise#noise_drop",
        ),
        TrickAction(
            "label_clean",
            "consensus: multi-model CV; change only if agree & conf≥τ",
            "flip log; probe ↑",
            "tricks:label_noise#relabel_cv",
        ),
        TrickAction(
            "train_recipe",
            "label_smooth: if residual noise remains",
            "calibration/gen improves without mushy labels",
            "tricks:label_noise#label_smooth",
        ),
    ],
    "train_unstable": [
        TrickAction(
            "train_recipe",
            "seed_repro: fix seed; disable random aug while debugging",
            "two short runs ≈ same loss",
            "tricks:train_unstable#seed",
        ),
        TrickAction(
            "train_recipe",
            "bn_nan: BN update on; locate NaN forward vs backward",
            "train↓ and eval not fake-converged",
            "tricks:train_unstable#bn_nan",
        ),
        TrickAction(
            "train_recipe",
            "dead_relu: LeakyReLU/ELU/GELU/Swish; clean outliers before grad clip",
            "train error moves again; no explode",
            "tricks:train_unstable#dead_relu",
        ),
    ],
    "oom": [
        TrickAction(
            "train_recipe",
            "fp16_accum: amp fp16; grad accum; DDP no_sync when accumulating",
            "1 epoch completes; metric ≈ fp32",
            "tricks:oom#fp16",
        ),
        TrickAction(
            "data_clean",
            "modify: shorter max length / smaller image side",
            "fits GPU; metric Δ logged",
            "tricks:oom#resize",
        ),
    ],
    "seq_aug": [
        TrickAction(
            "data_clean",
            "seq_mask_crop: random mask token-id; drop items or contiguous crop",
            "NDCG/Hit/seq-F1 ↑ or holds; length histogram sane",
            "tricks:seq_aug#mask_crop",
        ),
        TrickAction(
            "data_clean",
            "seq_reorder: shuffle a contiguous window (keep ends if causal)",
            "metric ↑ without collapsing to bag-of-items",
            "tricks:seq_aug#reorder",
        ),
        TrickAction(
            "data_clean",
            "seq_sub_insert: substitute/insert via item-sim dict (not uniform vocab)",
            "rare-item recall ↑; no train–test leakage in sim_dict",
            "tricks:seq_aug#sub_insert",
        ),
    ],
    "ranking_contrast": [
        TrickAction(
            "train_recipe",
            "bpr_pairwise: BPR / MarginRanking on (pos,neg); mine hard negs",
            "AUC/NDCG/MRR ↑ vs CE-only",
            "tricks:ranking_contrast#bpr",
        ),
        TrickAction(
            "train_recipe",
            "triplet_margin: TripletMargin with margin schedule",
            "embedding separation ↑; retrieval@K ↑ on probe",
            "tricks:ranking_contrast#triplet",
        ),
        TrickAction(
            "train_recipe",
            "infonce_kl: InfoNCE (in-batch/memory) and/or KL soft-label align",
            "contrastive loss ↓ with retrieval metric ↑; temperature logged",
            "tricks:ranking_contrast#infonce",
        ),
    ],
    "eval_boost": [
        TrickAction(
            "eval_recipe",
            "tta: multi-view test-time aug fusion",
            "same ckpt metric ↑; latency logged",
            "tricks:eval_boost#tta",
        ),
        TrickAction(
            "eval_recipe",
            "ensemble: fuse few models if latency allows",
            "ensemble > best single; cost logged",
            "tricks:eval_boost#ensemble",
        ),
    ],
}

_KEYWORD_MAP: list[tuple[str, tuple[str, ...]]] = [
    ("data_first", ("熟悉数据", "data_first", "pipeline", "新任务", "dataloader", "未摸清", "missing", "缺失", "impute", "特征相关")),
    ("overfitting", ("overfit", "过拟合", "train>>val", "train ≫ val", "memorize")),
    ("long_tail", ("long_tail", "long-tail", "长尾", "imbalance", "不平衡", "rare class", "focal")),
    # ranking / seq before generic hard_subset
    ("ranking_contrast", ("bpr", "infonce", "info-nce", "triplet", "margin ranking", "对比学习", "metric learning", "检索", "ndcg", "mrr")),
    ("seq_aug", ("seq_aug", "sequence", "session", "序列推荐", "会话", "mask item", "reorder", "history crop")),
    # label_noise before hard_subset (more specific label-noise cues first)
    ("label_noise", ("label_noise", "noisy label", "标噪", "错标", "mislabel", "cleanlab", "relabel")),
    ("hard_subset", ("handwriting", "手写", "hard_subset", "domain gap", "拼音", "style gap", "难例子集", "hard neg", "难负")),
    ("underfit", ("underfit", "欠拟合", "high loss", "not converge", "不收敛", "warmup")),
    ("train_unstable", ("nan", "不稳定", "spike", "explode", "dead relu", "死神经元", "gelu", "swish")),
    ("oom", ("oom", "out of memory", "显存", "cuda memory", "fp16")),
    ("eval_boost", ("tta", "test-time", "ensemble", "融合", "推理增强")),
]


def infer_symptom(text: str, *, fallback: str = "hard_subset") -> str:
    t = (text or "").lower()
    for sid, keys in _KEYWORD_MAP:
        if any(k.lower() in t for k in keys):
            return sid
    return fallback


def actions_for_symptom(symptom: str, *, n: int = 3) -> list[TrickAction]:
    acts = CATALOG.get(symptom) or CATALOG["hard_subset"]
    return list(acts[: max(1, min(n, len(acts)))])


def plans_from_symptom(
    symptom: str,
    *,
    cluster: Optional[Cluster] = None,
    plan_id_start: int = 1,
    n_actions: int = 3,
) -> list[Plan]:
    acts = actions_for_symptom(symptom, n=n_actions)
    plans: list[Plan] = []
    for i, a in enumerate(acts):
        pid = plan_id_start + i
        focus = f"focus_cluster={cluster.cluster_id}" if cluster else f"symptom={symptom}"
        plans.append(
            Plan(
                plan_id=f"P{pid}",
                hypothesis=f"[{symptom}] {a.summary}",
                actions=[focus, f"{a.family}: {a.summary}", f"mini_verify: {a.mini_verify}"],
                expected_gain=0.02 + (0.01 if a.family.startswith("data") or a.family.startswith("label") else 0.005),
                cost=0.25 + 0.1 * i + (0.05 if a.family == "eval_recipe" else 0.0),
                risk="verify on probe before full train",
                special_questions=[cluster.special_question] if cluster else [symptom],
                meta={
                    "symptom": symptom,
                    "source": a.source,
                    "family": a.family,
                    "cluster_id": cluster.cluster_id if cluster else None,
                },
            )
        )
    return plans


def render_plan_md(plan: Plan) -> str:
    """Full three-pillar template (data / model / train). See plan_template.md."""
    from .plan_template import render_full_plan_md

    return render_full_plan_md(plan)


def enrich_cluster_plans(
    clusters: list[Cluster],
    *,
    actions_per_cluster: int = 3,
) -> list[Plan]:
    if not clusters:
        return []
    ordered = sorted(clusters, key=lambda c: c.share, reverse=True)
    if len(ordered) >= 2:
        ordered = ordered[:-1] + [min(clusters, key=lambda c: c.share)]

    plans: list[Plan] = []
    next_id = 1
    for c in ordered:
        text = f"{c.label} {c.special_question}"
        symptom = infer_symptom(text)
        chunk = plans_from_symptom(
            symptom, cluster=c, plan_id_start=next_id, n_actions=actions_per_cluster
        )
        plans.extend(chunk)
        next_id += len(chunk)
    return plans


def plan_filename(plan: Plan) -> str:
    return f"{plan.plan_id}.md"
