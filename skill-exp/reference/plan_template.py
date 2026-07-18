"""Render full three-pillar solution plan markdown (data / model / train)."""
from __future__ import annotations

from typing import Optional

from .types import Plan

# Symptom → which pillars typically need concrete actions (hints for agent)
PILLAR_HINTS: dict[str, dict[str, str]] = {
    "long_tail": {
        "data": "可视化类分布 → 结论需调采样/比例 → 过采样或 class-balanced 规则",
        "model": "通常沿用基座；若要教师清洗再开 clean_*",
        "train": "focal / 加权 CE + 与采样一致的 sampler；盯 macro 指标",
    },
    "label_noise": {
        "data": "高熵/不一致样本清单 → 删除或隔离",
        "model": "必选 clean_closed 或 clean_open；榜单短名单+对比表",
        "train": "清洗后短训；可选 label smoothing",
    },
    "overfitting": {
        "data": "查泄漏/重复；针对性增广",
        "model": "一般不换模；容量过大再考虑更小基座",
        "train": "dropout / WD / early-stop / SWA",
    },
    "hard_subset": {
        "data": "子集增广/合成；课程或 last-k finetune 数据",
        "model": "可评估更强 clean/teacher；基座按任务榜选型",
        "train": "差分 LR / 子集 finetune",
    },
    "underfit": {
        "data": "检查预处理 bug",
        "model": "可换更大/更新开源基座（家族下钻）",
        "train": "更长训、warmup、cosine、预训练",
    },
    "data_first": {
        "data": "分布可视化 + 标注抽检 + 小子集过拟合探针",
        "model": "先证明可学再选型",
        "train": "固定 seed；先关随机增广做管线验证",
    },
}


def render_full_plan_md(
    plan: Plan,
    *,
    figures: Optional[list[str]] = None,
    experiment_id: str = "",
) -> str:
    """
    Three-pillar plan body. Agent fills TBD cells after analysis / board lookup.
    """
    symptom = str(plan.meta.get("symptom", ""))
    src = str(plan.meta.get("source", ""))
    hints = PILLAR_HINTS.get(
        symptom,
        {
            "data": "写清现象→图→结论→可执行调整",
            "model": "无换模则 N/A；否则榜单+对比",
            "train": "超参/采样/loss 等可执行 diff",
        },
    )
    figs = figures or plan.meta.get("figures") or []
    fig_line = ", ".join(f"`{f}`" for f in figs) if figs else "`TBD`（需要时用 /draw 生成）"
    sq = plan.special_questions[0] if plan.special_questions else ""
    exp = f"content/exp/{experiment_id}/" if experiment_id else "content/exp/<id>/"

    actions_md = "\n".join(f"- {a}" for a in plan.actions) or "- TBD"

    return f"""# {plan.plan_id} — {plan.hypothesis}

## 0. 诊断摘要
- symptom: `{symptom}`
- special_question: {sq or "TBD"}
- evidence: TBD（填入计数/占比/指标；禁止空口）
- figures: {fig_line}
- source: `{src}`
- expected_gain: {plan.expected_gain} · cost: {plan.cost} · risk: {plan.risk}

### Seed actions (from catalog)
{actions_md}

## 1. 数据侧（Data）
> 提示: {hints["data"]}

### 1.1 现象
- TBD

### 1.2 可视化
- chart: TBD（bar / multi_bar / violin / …）
- path: `{exp}figures/<name>.png`
- 读图结论: TBD

### 1.3 结论
- TBD（例：训练集比例需要调整 / 需剔除噪声 / …）

### 1.4 调整方案（可执行）
| 步骤 | 操作 | 对象/比例/规则 | 预期 |
|------|------|----------------|------|
| D1 | TBD | TBD | TBD |

### 1.5 Mini-verify（数据）
- probe 集: TBD
- 成功标准: {plan.actions[-1] if plan.actions else "TBD"}

## 2. 模型侧（Model）
> 提示: {hints["model"]}

### 2.1 是否需要选型
- TBD（yes → 角色 clean_closed / clean_open / train_base / distill_*）

### 2.2 榜单与短名单
- boards + date: TBD
- 对比表: 见下方或 `model_select` 块（≥3 候选）

| candidate | open/closed | size | key scores | VRAM/cost | decision |
|-----------|-------------|------|------------|-----------|----------|
| TBD | | | | | |

### 2.3 家族下钻（若已定家族）
- TBD 或 N/A

### 2.4 Mini-verify（模型）
- TBD 或 N/A

## 3. 训练侧（Train）
> 提示: {hints["train"]}

### 3.1 现象 / 动机
- TBD（如何承接数据侧·模型侧结论）

### 3.2 训练配方调整
| 步骤 | 项 | 原值 → 新值 | 理由 |
|------|----|-------------|------|
| T1 | TBD | TBD | TBD |

### 3.3 监控与出图
- `/draw line` → `{exp}figures/<curves>.png`

### 3.4 Mini-verify（训练）
- 短训设置: TBD
- 成功标准: TBD

## 4. 预期收益与风险
- vs target_score: TBD
- 回滚条件: TBD

## 5. 执行顺序
1. 数据侧 D* → mini-verify
2. 模型侧锁定（若需要）→ mini-verify
3. 训练侧 T* → mini-verify → 全量 `/exp_training`
"""


def merge_model_block(plan_md: str, model_blocks: str) -> str:
    """Insert filled model_select tables into §2 if present."""
    if not model_blocks.strip():
        return plan_md
    marker = "### 2.2 榜单与短名单"
    if marker not in plan_md:
        return plan_md.rstrip() + "\n\n" + model_blocks
    # append boards after 2.2 header section as extra material
    return plan_md.replace(
        marker,
        marker + "\n\n" + model_blocks.strip() + "\n\n#### 2.2b 自动角色模板",
        1,
    )
