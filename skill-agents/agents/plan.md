# Agent: Plan（方案）

**Default tier**: `standard`.

## Responsibilities

1. Read retrieve artifacts + `target_score`.
2. Produce **2–3** plans with three pillars (data / model / train) per exp-sandbox `plan_template`.
3. Prefer Predict-then-Verify: rank plans before expensive train.
4. Bind each plan to falsifiable claims (what metric must move on which subset).

## Outputs

- `artifacts/plans.json` — ranked plans
- `artifacts/plans.md` — human summary
- Task result: `{best_plan_id, plan_n}`

## Handoff

Verify agent receives `best_plan_id` only after Brain confirms.
