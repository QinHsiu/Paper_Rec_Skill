---
name: multi-agent-lab
version: 1.0.0
description: >-
  Multi-agent experiment lab: a Brain dispatcher plus retrieve/plan/verify/
  experiment/accept/write (and critique/reflect/draw) role agents, with
  fast/standard/deep model routing. Activated by /lab, /lab_run, /lab_status.
  Use for 多agent实验, 任务分发, 模型分级, 检索-方案-验证-训练-验收-写作编排.
  Reuses paper-rec, exp-sandbox, plot-draw, and wiki-bridge integrity gates —
  does not replace them.
---

# Multi-Agent Lab Skill / 多 Agent 实验实验室

Sibling to **exp-sandbox** (`skill-exp`). Exp-sandbox owns *how* to analyze/train/eval one loop; this skill owns *who* does which stage, with **model-tier routing** so simple tasks use fast models.

```text
Brain (deep)
  ├─ Retrieve (standard)  → paper-rec / wiki-bridge
  ├─ Plan (standard)      → exp-sandbox plans
  ├─ Verify (standard)    → mini-verify
  ├─ Experiment (standard)→ /exp_training · /exp_eval
  ├─ Accept (deep)        → hard-gate · stats · repro
  ├─ Write (deep)         → writing-gates · latex-export
  ├─ Critique (standard)  → overclaim / review checklist
  ├─ Reflect (standard)   → DEEPEN|BROADEN|PIVOT|CONCLUDE
  └─ Draw (fast)          → /draw
```

---

## Quick Start

```
Task Progress:
- [ ] Collect target_score + tool/function (models for fast/standard/deep)
- [ ] /lab_run → create content/lab/<run_id>/ + default TaskCards
- [ ] Brain dispatches ready tasks with correct model_tier
- [ ] Mark tasks done/failed; Accept must pass before Write claims Results
- [ ] /lab_status until stage=done|blocked
```

### Activation

| Command | Behavior |
|---------|----------|
| `/lab` | Explain roster + routing; ask goal if missing |
| `/lab_run` | Create run + bootstrap pipeline TaskCards |
| `/lab_status` [`run_id`] | Show stage, ready tasks, recommended tiers |

```text
/lab_run
title: handwriting OCR F1 chase
hypothesis: label-clean on handwritten_pinyin raises F1 without global drop
target_score:
  metric: F1
  threshold: 0.92
  eval_set: test_handwriting_v2
thread: mm-llm-alignment
models:
  fast: <your-fast-model>
  standard: <your-mid-model>
  deep: <your-strong-model>
```

---

## Model routing (mandatory)

Before each TaskCard execution, resolve tier via [`reference/model_routing.md`](reference/model_routing.md) / `recommend_tier(role=, task=)`.

| Tier | Use for |
|------|---------|
| **fast** | status, JSON cards, intent strip, file checks, draw params, screen labels |
| **standard** | retrieve, plan, verify, experiment ops, critique, reflect |
| **deep** | Brain decisions, Accept verdict, paper writing, novelty kill |

If the host cannot switch models mid-run, **simulate tiers** by: shorter context + cheaper prompts for `fast`; fullest context for `deep`. Still record `model_tier` on every card.

---

## Role briefs

Read the matching file under [`agents/`](agents/) before acting as that role:

| Agent | File |
|-------|------|
| Brain | [`agents/brain.md`](agents/brain.md) |
| Retrieve | [`agents/retrieve.md`](agents/retrieve.md) |
| Plan | [`agents/plan.md`](agents/plan.md) |
| Verify | [`agents/verify.md`](agents/verify.md) |
| Experiment | [`agents/experiment.md`](agents/experiment.md) |
| Accept | [`agents/accept.md`](agents/accept.md) |
| Write | [`agents/write.md`](agents/write.md) |
| Critique | [`agents/critique.md`](agents/critique.md) |
| Reflect | [`agents/reflect.md`](agents/reflect.md) |
| Draw | [`agents/draw.md`](agents/draw.md) |

---

## Python helpers (offline ledger)

```powershell
cd skill-agents
python -c "from reference.orchestrator import init_lab_run, status_summary; import json; r=init_lab_run('../content', title='demo', hypothesis='h'); print(json.dumps(r, indent=2))"
```

| API | Purpose |
|-----|---------|
| `init_lab_run` | create `content/lab/<id>/` + pipeline cards |
| `status_summary` | ready tasks + tier hints |
| `mark_task` | pending→done/failed/blocked + artifacts |
| `brain_decide` | record decision / inject extra task |

Artifacts live in `content/lab/<run_id>/{run.json,tasks/,artifacts/}`.

---

## Integration rules

1. **Do not fork** paper-rec / exp-sandbox logic — call their slash commands / wiki-bridge CLI.
2. **Accept before Write** for any Results float (hard-gate).
3. Human-in-the-loop: Brain surfaces blockers; never auto-spend GPU without user tool/function.
4. Persist experiment metrics under `content/exp/` then link from lab `artifacts/exp_link.json`.

---

## Stop conditions

- `target_score` met **and** Accept=accept → Write optional → Reflect CONCLUDE
- Accept reject with no remaining plan → Reflect PIVOT or CONCLUDE
- User aborts → stage=blocked, write reason to decisions
