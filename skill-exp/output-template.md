# Output Templates / 输出模板 — exp-sandbox

Keep each subsection short unless the user asks for depth.

---

## A. Analysis Report (`/exp_analysis`)

```markdown
# Experiment Analysis — <experiment_id>

## Context
- target_score:
- split: train | eval
- tools used:

## Data / Metric Snapshot
- size / class balance / key stats:
- current metrics (if any):

## Badcase Clusters (diversity preserved)
| Cluster | Count | Share | Example ids | Special question |
|---------|-------|-------|-------------|------------------|
| C1 | | | | |

## Priority Problems
1. …
2. …

## Solution Plans (multi) — 摘要表
| Plan | Hypothesis | 数据侧要点 | 模型侧要点 | 训练侧要点 | Gain | Rank |
|------|------------|------------|------------|------------|------|------|
| P1 | | | | | | 1 |

完整正文必须按三侧模板展开，见 [`reference/plan_template.md`](reference/plan_template.md) → `plans/P*.md`：

```text
0 诊断摘要（evidence + figures）
1 数据侧: 现象 → 可视化 → 结论 → 调整方案表 → mini-verify
2 模型侧: 是否选型 → 榜单对比 / 家族下钻 → mini-verify（或 N/A）
3 训练侧: 配方 diff → 曲线出图 → mini-verify
4 收益与风险 · 5 执行顺序
```

示例（不均衡）: 画类分布 bar → 结论「训练集比例需调整」→ D1 过采样/平衡采样规则 → T1 focal/加权 CE。

## Recommended Next Step
- chosen for mini-validation:
- why:
```

---

## B. Mini-Validation Log

```markdown
# Mini-Validation — <plan_id>

- change summary:
- probe set / slice:
- metrics before → after:
- matches plan expectation? yes/no
- decision: promote_to_full_train | revise | discard
```

---

## C. Training Monitor (`/exp_training`)

```markdown
# Training Run — <run_id>

## Config
- model / data / hyperparams / seed:
- infra:

## Curves (link paths or embed summaries)
- train_loss:
- val_<primary_metric>:
- secondary:

## Status
- step/epoch:
- best checkpoint:
- anomalies:
```

---

## D. Evaluation Report (`/exp_eval`)

```markdown
# Evaluation — <run_id>

| Metric | Value | Threshold | Pass? |
|--------|-------|-----------|-------|
| | | | |

## Stratified / notes
-

## Badcase digest
-

## Next-step candidates
-
```

---

## E. Loop Round (`/exp_loop`)

```markdown
## Round N
- analysis_summary:
- plans: [P…]
- chosen:
- mini_validation:
- training:
- evaluation vs target_score:
- decision: continue | stop
```

---

## F. Final Report (`final_eval & analysis`)

```markdown
# Final Experiment Report — <experiment_id>

## Outcome
- target_score met? yes/no
- best metrics / run:

## What we tried
| Round | Plan | Result |
|-------|------|--------|

## Analysis takeaways
-

## Future optimizations (if not met or for further gain)
1.
2.

## Artifacts
- paths:
```
