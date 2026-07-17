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

## Solution Plans (multi)
| Plan | Hypothesis | Actions (data/label) | Expected gain | Cost/Risk | Rank |
|------|------------|----------------------|---------------|-----------|------|
| P1 | | | | | 1 |

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
