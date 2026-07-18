# Changelog — exp-sandbox

## [1.7.0] — 2026-07-18

### Added

- Three-pillar solution plan template: **数据侧 / 模型侧 / 训练侧** (`reference/plan_template.md` + `plan_template.py`)
- Required flow: 现象 → 可视化 → 结论 → 可执行调整（例：不均衡→调训练集比例）→ 分侧 mini-verify
- `render_plan_md` emits full pillar skeleton into `plans/P*.md`

## [1.6.0] — 2026-07-18

### Added

- Model selection in solution plans: `reference/model_leaderboards.md` + `model_select.py`
- Roles: `clean_closed` / `clean_open` / `train_base` / `distill_teacher|student` (HF Open LLM LB, Arena, SuperCLUE, …)
- Family drill-down (e.g. Qwen): ≥3 open variants + comparison table required in `plans/P*.md`
- `plans_from_clusters` attaches Model selection stubs when actions need models

## [1.5.0] — 2026-07-18

### Added

- Enriched bundled catalog from curated link digests: `data_first`, SWA, focal/multi-loss, diff_lr, domain_pt, TTA, fp16, etc.
- Still **self-contained** (no runtime path to Awesome-Tricks / WeChat)

## [1.4.0] — 2026-07-18

### Added

- Bundled symptom→action catalog: `reference/tricks_catalog.md` + `reference/tricks.py` (no external path)
- `plans_from_clusters` fills 2–3 verifiable actions with `source: tricks:…` for `plans/P*.md`
- Decision family `train_recipe` (after analysis; data/label still primary)

## [1.3.0] — 2026-07-18

### Added

- Figure pipeline via `/draw` (`skill-draw/lib`) for `/exp_analysis` · `/exp_training` · `/exp_eval`
- Default figure dir: `content/exp/<id>/figures/`

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
