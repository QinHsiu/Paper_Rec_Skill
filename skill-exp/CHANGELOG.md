# Changelog — exp-sandbox

## [1.2.0] — 2026-07-17

### Added

- Wiki 实验模块联动：`wiki_bridge sync-exp` → `content/exp` + `pages/_exp`
- End-to-end loop docs: `/query_*` → 人工阅读标记 → `/exp_*` → sync-exp
- Regression script `scripts/regress_exp_wiki.py`

## [1.1.0] — 2026-07-17

### Added

- `reference/` agent-facing stubs adapted from Predict-then-Verify / pairwise preference ideas
- Modules: data_report, preference, tournament, predict_then_verify, badcase, mini_eval, train_monitor, orchestrator
- Prompt templates under `reference/prompts/` (adapted from paper appendix)

## [1.0.0] — 2026-07-17

### Added

- Agent skill `exp-sandbox` with four modes: `/exp_analysis`, `/exp_training`, `/exp_eval`, `/exp_loop`
- Subtypes `/exp_analysis train|eval` and aliases `/analysis train|eval`
- Context fields: `target_score`, `tool/function`, `analysis_tool`, `other_source_model`
- Badcase cluster → special question → multi-plan → mini-validation → train/eval loop
- Output templates and examples
- Acknowledgement of Predict-then-Verify ideas from zjunlp/predict-before-execute
