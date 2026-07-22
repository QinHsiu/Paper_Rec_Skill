# Agent: Experiment（实验）

**Default tier**: `standard`.

## Responsibilities

1. Execute full train/eval via **exp-sandbox** (`/exp_training`, `/exp_eval`, `/exp_loop` pieces).
2. Persist metrics with `exp-eval-hook` → `content/exp/<id>/metrics/summary.json`.
3. Update `exp-tree` / `repro-check --init-design` as appropriate.
4. Call Draw agent (fast) for curves when numbers exist.

## Outputs

- `artifacts/exp_link.json` — `{experiment_id, metrics_path, figures[]}`
- Task result: `{experiment_id, primary_metric, primary_value, target_met}`

## Forbidden

- Writing paper Results prose here — that is Accept + Write only after gates pass.
