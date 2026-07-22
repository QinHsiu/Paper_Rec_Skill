<div align="center">

# Multi-Agent Lab

**Brain-orchestrated experiment crew · Agent Skill**  
**多 Agent 实验实验室 · 与 exp-sandbox 同级**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](VERSION)
[![Agents](https://img.shields.io/badge/Agents-Brain%20%2B%20roles-3D5A80?style=flat)](SKILL.md)

*`/lab` · `/lab_run` · `/lab_status` · fast / standard / deep routing*

</div>

---

## Overview

**Multi-Agent Lab** sits beside [`skill-exp`](../skill-exp/) (execution sandbox), [`skill`](../skill/) (literature), and [`skill-draw`](../skill-draw/) (figures).

| Layer | Owns |
|-------|------|
| **multi-agent-lab** (this skill) | Who acts · task dispatch · model tiers · Accept/Write gates |
| **exp-sandbox** | How to analyze / mini-verify / train / eval one loop |
| **paper-rec** | Literature retrieve / thread hooks |
| **wiki-bridge** | Integrity CLI (hard-gate, stats, fig, survey, …) |

### Roster

| Agent | Tier | Job |
|-------|------|-----|
| **Brain** | deep | Dispatch + subject decisions |
| **Retrieve** | standard | Literature via paper-rec |
| **Plan** | standard | 2–3 verifiable plans |
| **Verify** | standard | Mini-verify before full train |
| **Experiment** | standard | Train/eval via exp-sandbox |
| **Accept** | deep | Hard-gate / stats / repro verdict |
| **Write** | deep | Paper draft after Accept |
| **Critique** | standard | Overclaim / review checklist |
| **Reflect** | standard | DEEPEN / BROADEN / PIVOT / CONCLUDE |
| **Draw** | fast | `/draw` curves |

Simple mechanical work (status JSON, intent strip) always prefers **fast**.

---

## Install

```bash
mkdir -p .agents/skills/multi-agent-lab
cp -r skill-agents/* .agents/skills/multi-agent-lab/
```

```text
/lab_run
title: ...
target_score: ...
models: {fast: ..., standard: ..., deep: ...}
```

---

## Run store

```text
content/lab/<run_id>/
  run.json          # stage, tasks, decisions, routing
  tasks/*.json      # TaskCards
  artifacts/        # retrieve_pool, plans, accept_report, ...
  README.md
```

---

## Docs

- [`SKILL.md`](SKILL.md) — activation & rules  
- [`agents/`](agents/) — per-role briefs  
- [`reference/model_routing.md`](reference/model_routing.md) — tier table  
- Workspace hub: [../README.md](../README.md)
