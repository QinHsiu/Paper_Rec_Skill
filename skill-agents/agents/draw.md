# Agent: Draw（绘图 · 补充）

**Default tier**: `fast`.

## Responsibilities

1. Call **plot-draw** `/draw` with venue preset for curves/ablation tables.
2. After figures exist, request `fig-review` (Write/Accept may own semantic VLM JSON).

## Outputs

- figure paths under `content/exp/<id>/figures/` or `artifacts/figures/`
- Task result: `{figure_paths[]}`
