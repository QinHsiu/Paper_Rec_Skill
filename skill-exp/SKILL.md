---
name: exp-sandbox
version: 1.5.0
description: >-
  Automated experiment sandbox: dataset analysis, training, evaluation, and a
  self-improving loop (analyze → multi-plan → mini-verify → train → eval →
  iterate). Activated by /exp_analysis, /exp_training, /exp_eval, or /exp_loop.
  Use for ML experiment orchestration, badcase clustering, data/label cleaning
  plans, training monitors, target_score chasing, 实验沙箱/训练分析/评估迭代.
  Figures follow /draw (skill-draw/lib). Bundled symptom→action tricks in
  reference/tricks_catalog.md. Reference stubs under skill-exp/reference/.
---

# Experiment Sandbox Skill / 实验沙箱技能

Orchestrate **analysis → plan → mini-validation → training → evaluation → next-step** for ML experiments. Prefer planning and small-scale verification before full training runs (Predict-then-Verify style). Follow algorithms in [`reference/`](reference/) when implementing loops. Do **not** invent credentials or silently call paid/private APIs; use only tools/accounts the user provides.

**Inspiration**: Concepts adapted from [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute) (FOREAGENT / Predict-then-Verify). See skill README for attribution.

---

## Quick Start / 快速开始

```
Task Progress:
- [ ] Collect run context (target_score, tools, data access, analysis tools)
- [ ] Mode branch: analysis | training | eval | loop
- [ ] Persist plans & results under content/exp/ (or user-specified path)
- [ ] Stop when target_score met OR no better plan remains → final report
```

**Trigger**: User wants automated experiment analysis, training launch, metric evaluation, or iterative optimize-until-target loops.

---

## Activation Commands / 启用命令

| Command | Mode | Behavior |
|---------|------|----------|
| `/exp_analysis` | Analysis | Analyze data / badcases; optional subtype below |
| `/exp_analysis train` or `/analysis train` | Analysis · train set | Analyze **training** data distribution & quality |
| `/exp_analysis eval` or `/analysis eval` | Analysis · eval set | Analyze **test/eval** set & failure modes |
| `/exp_training` | Training | Launch / monitor training with loss & val curves |
| `/exp_eval` | Evaluation | Run evaluation and report metrics vs `target_score` |
| `/exp_loop` | Self-loop | Full iterate until target or exhaustion |

### Usage format / 使用格式

```
/exp_analysis train
target_score: OCR F1 >= 0.92 on test_handwriting_v2
tool/function: [train_server=..., data_path=..., open_model=...]

/exp_analysis eval
（对当前模型在测试集上的 badcase 做聚类与方案）

/exp_training
（启动训练并监控）

/exp_eval
（输出指标表与是否达标）

/exp_loop
target_score: ...
tool/function: ...
```

Strip the slash command; remaining text + structured fields are the run context.

If the user omits a command, **ask** which mode to use before proceeding.

---

## Required Context / 运行上下文

Collect (ask if missing) before heavy work:

### 1. `target_score`

Define **task + eval set + metric + threshold**, e.g.:

```text
target_score:
  task: handwriting_ocr
  eval_set: test_handwriting_v2
  metric: F1
  threshold: 0.92
  secondary: [CER <= 0.08]
```

### 2. `tool/function`

User-supplied capabilities (never invent secrets):

```text
tool/function:
  - closed_models: [{name, endpoint_or_account_hint, use_method}]
  - open_models: [{name, deploy_url_or_path, use_method}]
  - sources: [{name, how_to_access_train_test_data}]
  - train_infra: [{server, login_method, launch_cmd_or_api}]
  - notes: resource limits, GPUs, quotas
```

### 3. `analysis_tool?`

If provided, use them. If **not** provided, fall back to lightweight ML / statistical / visualization analysis, e.g.:

| Modality | Default probes |
|----------|----------------|
| Image | size, resolution, aspect ratio, channel stats, blur/noise proxies |
| Audio | duration, sample rate, channels, SNR proxies |
| Text | length, token/char histograms, label distribution, language mix |
| Labels | class imbalance, missing/noisy labels, agreement if multi-annotator |

### 4. `other_source_model` (optional supplements)

When tools are insufficient, enrich plans from:

- **Bundled** symptom→action catalog: [`reference/tricks_catalog.md`](reference/tricks_catalog.md) / `reference/tricks.py` (no external path)
- Papers With Code / Hugging Face open results & baselines
- Paper notes in local Wiki (`content/wiki/pages/…` reading notes)
- Paper_Rec recommendations (methods, datasets, metrics)

Document every borrowed method in the plan log (`source:` field).

---

## Module A — Result / Badcase Analysis

`exp_result_analysis[badcase_sets → gen_analysis_cluster → special_question → solution_plan]`

1. **badcase_sets**: Collect failures from eval (or high-loss train samples). Keep ids, inputs, preds, gold, scores.
2. **gen_analysis_cluster**: Aggregate badcases into clusters; preserve **diversity** (do not collapse everything into one bucket). Prefer coverage of modalities/error types by frequency × severity.
3. **special_question**: Name concrete sub-problems, e.g. *「OCR 对手写拼音识别效果差」*.
4. **solution_plan** (**analyze first, then catalog**):
   - Map each priority cluster → a **symptom** (`overfitting` / `long_tail` / `hard_subset` / …).
   - From the **bundled** catalog pick **2–3 verifiable actions** (not the whole cookbook).
   - Write `content/exp/<id>/plans/P*.md` with `source: tricks:<symptom>#…` (see `reference/tricks.render_plan_md`).
   - Prefer `reference.badcase.plans_from_clusters` / `tricks.enrich_cluster_plans`.
   - Rank by expected gain vs cost; high-mass clusters first (keep one long-tail).

### Self-analysis

`self_analysis: badcase_analysis` — always ground claims in examples + counts; avoid vague “model is weak”.

### Decision space / `make_decision: next_step`

Choose next actions from:

| Family | Actions |
|--------|---------|
| **data_clean** | increase / remove / modify / insert / inspect samples |
| **label_clean** | self-sampling review / multi-model consensus / relabel |
| **train_recipe** | regularize / SWA / focal·weighted loss / diff_lr / warmup·cosine / fp16 (after analysis) |
| **eval_recipe** | TTA / ensemble (optional, after train plans) |

---

## Module B — Plan Record & Mini Evaluation

`data_processing & mini_evaluation [cycle verify current method of plan]`

1. **Record the plan** (id, hypothesis, steps, expected metric delta, risks, **source**).
2. Apply data/label (or train_recipe) changes on a **small slice** (or held-out probe set).
3. Mini-eval: does the change move the needle as predicted? (use each action’s `mini_verify`.)
4. If **not**, adjust plan and re-mini-eval before full training.
5. Prefer **Predict-then-Verify**: rank multi-plans first; only fully execute **Top-1** (or Top-k if user asks) after mini-check.

---

## Module C — Training (`/exp_training`)

`get training: monitor training process [visualization, outsource tool]`

When launching/monitoring training:

- Require clear launch path from `tool/function.train_infra`.
- Track and report: **train loss**, **val metrics**, LR, epoch/step, early-stop signals.
- **Figures**: apply [`../skill-draw/SKILL.md`](../skill-draw/SKILL.md) (`/draw` → `lib.draw`) — auto chart (usually `line`), academic palette in `skill-draw/lib`; save `content/exp/<id>/figures/*.{pdf,png}`. ASCII sparklines are optional previews only.
- Sign / checkpoint: record run_id, config hash, artifact paths, seed.

Do not claim training finished without evidence from logs/metrics the user or tools provide.

---

## Module D — Evaluation (`/exp_eval`)

1. Run (or read) eval on the declared `target_score.eval_set`.
2. Table: metric → value → vs threshold → pass/fail.
3. Attach stratified / badcase summary if available.
4. If fail, propose next-step candidates (link to Module A).

---

## Module E — Self-Loop (`/exp_loop`)

Pipeline (repeat until stop):

```text
analysis → [multi plan] → clean → mini_validation → training → evaluation → next-step
```

Notation from product spec:

`analysis([plan])_clean_validation_training_evaluation_next-step`

### Loop rules

1. Start from context + latest metrics/badcases.
2. Produce **≥2** (prefer **m=10**) solution plans; score via pairwise preference with confidence gate **c=0.7** (see `reference/tournament.py`).
3. Select **Top-1** (`k=1`); mini-validate (`reference/mini_eval.py`); if fail, try next plan or revise.
4. Full train + eval; compare to `target_score`.
5. **Stop when**:
   - `target_score` met, **or**
   - no remaining plan with positive expected value / user aborts.
6. Always emit **final_eval & analysis** (see Output).
7. Prefer calling `reference.orchestrator.run_exp_loop` mental model / stubs over inventing a new control flow.

### Iteration log (append each round)

```markdown
## Round N
- analysis_summary:
- plans: [P1, P2, ...]
- chosen: Px
- mini_validation:
- training:
- evaluation:
- decision: continue | stop
```

---

## Mode Playbooks / 各模式剧本

### `/exp_analysis` (+ train | eval)

**train**: distribution, label quality, leakage risk, hard subsets, augmentation gaps.  
**eval**: metric baseline, badcase clusters, special questions, multi-plans (no full train unless asked).  
**Charts** (via `/draw` + `skill-draw/lib`): label/`bar`·`violin`, cluster `multi_bar`, confusion `heatmap` → `content/exp/<id>/figures/`.

Output: Analysis Report (template) + figure paths.

### `/exp_training`

Confirm config → launch via provided infra → monitor curves → checkpoint summary.  
Curves via `/draw` (`line` / `broken_line`). If analysis gaps block training, run a short analysis first or ask.

### `/exp_eval`

Metrics vs `target_score` + short badcase digest + next-step hints.  
Compare methods with `/draw multi_bar` or `bar_line` when multiple runs exist.

### `/exp_loop`

Execute Module E end-to-end; ask only for missing critical context or dangerous actions (delete large data, spend money, overwrite prod).

---

## Persistence / 结果落盘

Prefer workspace paths (create if needed):

```text
content/exp/<experiment_id>/
  README.md                 # goal, target_score, tools used
  rounds/round-NN.md        # loop logs
  plans/P*.md               # solution plans
  analysis/                 # cluster reports
  metrics/                  # summary.json + curves.json
  final_report.md           # stop condition report
```

**Sync into Wiki 实验模块** (required when a run finishes or user asks to publish):

```bash
python -m wiki_bridge.cli sync-exp \
  --wiki-root <workspace> \
  --report ./exp_result.json
```

This writes:
- `content/exp/<id>/` (metrics, curves, final_report)
- `content/wiki/pages/_exp/<id>/README.md` (Wiki 实验页；`_exp` 不会进入论文库索引)
- index `content/wiki/pages/_exp/README.md`

JSON payload fields: `experiment_id`, `title`, `target_score`, `target_met`, `metrics.primary`, `curves.{name:{steps,values}}`, `paper_refs`, `summary`, `future_optimizations`.

Link Wiki paper notes when methods come from reading (`content/wiki/pages/...`) via `paper_refs`.

### End-to-end research loop / 端到端闭环

```text
/query_* 获取论文
  → wiki_bridge sync-report 入库
  → 人工阅读并在 Wiki 标记 status/rating/笔记
  → /exp_analysis|/exp_loop 自动化方案验证与训练
  → wiki_bridge sync-exp 把 loss 曲线与指标写入 Wiki「实验」模块
```

---

## Output Templates / 输出模板

Use [output-template.md](output-template.md). Keep fields concise (≤3 short bullets or ≤2 sentences per subfield unless user asks for detail).

### Final report (`final_eval & analysis`) — required on loop stop

1. Whether `target_score` achieved  
2. Best metrics + run ids  
3. Plans tried and outcomes  
4. Remaining promising optimizations  
5. Risks / data debts  

---

## Safety & Hygiene

- Never fabricate metrics, curves, or “training completed” without sources.
- Never expand user secrets into logs beyond redacted form.
- Destructive data ops (mass delete) require explicit user confirmation.
- Respect train server quotas and rate limits stated in `tool/function`.

---

## Related / 相关

- Paper retrieval skill: `../skill/` (`/query_*`)
- **Plot skill**: [`../skill-draw/`](../skill-draw/) (`/draw`) — figures for analysis / train / eval
- Wiki notes: `../content/wiki/`
- **Reference code (agent stubs)**: [`reference/`](reference/) — Predict-then-Verify, preference, badcase, tricks catalog, orchestrator
- Examples: [examples.md](examples.md)
- Attribution: [README.md](README.md#acknowledgement--借鉴说明)
