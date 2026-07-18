<div align="center">

# Exp_Sandbox

**Automated Experiment Sandbox · Agent Skill**  
**自动化实验沙箱 · Agent 技能（跨平台）**

[![Version](https://img.shields.io/badge/version-1.7.0-blue.svg)](VERSION)
[![Agents](https://img.shields.io/badge/Agents-Claude%20·%20Codex%20·%20OpenClaw%20·%20more-3D5A80?style=flat)](SKILL.md)
[![SemVer](https://img.shields.io/badge/SemVer-2.0.0-green.svg)](https://semver.org/)

*Analysis · Multi-plan · Mini-verify · Train · Eval · Loop · `/draw` figures*

[English](README.en.md) · [中文](README.zh-CN.md) · [Changelog](CHANGELOG.md)

</div>

---

## Overview / 概览

**Exp_Sandbox** is an Agent Skill that orchestrates ML experiments: dataset/badcase analysis, ranked solution plans, small-scale verification, training monitors, evaluation against `target_score`, and a self-improving loop until the goal is met or plans are exhausted.

Works with Claude Code, Codex, OpenClaw, and other runtimes that load Markdown skills.

Companion to [Paper_Rec](../skill/) (literature) and the local Wiki reading notes.

---

## Commands

| Command | Mode |
|---------|------|
| `/exp_analysis` | Analysis (`train` / `eval` subtypes) |
| `/analysis train` | Alias → train-set analysis |
| `/analysis eval` | Alias → eval-set analysis |
| `/exp_training` | Launch & monitor training |
| `/exp_eval` | Metrics vs `target_score` |
| `/exp_loop` | Full iterate loop |

Loop skeleton:

```text
analysis([plan]) → clean → mini_validation → training → evaluation → next-step
```

---

## Install / 安装

```bash
mkdir -p .agents/skills/exp-sandbox
cp -r skill-exp/* .agents/skills/exp-sandbox/
# or: skills/exp-sandbox/ · platform-specific skills path
```

Workspace hub: [../README.md](../README.md)

---

## Acknowledgement / 借鉴说明

本技能在 **方案排序后再执行、小规模验证再全量训练、用预测偏好压缩执行成本** 等思路上，借鉴了浙江大学 NLP 实验室开源项目：

- **Repository**: [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute)
- **Paper**: [Can We Predict Before Executing Machine Learning Agents?](https://arxiv.org/abs/2601.05930) (FOREAGENT · Predict-then-Verify)

具体借鉴点（参考实现见 [`reference/`](reference/)，非上游代码原样搬运）：

| Idea from upstream | How Exp_Sandbox uses it |
|--------------------|-------------------------|
| Predict-then-Verify | `reference/predict_then_verify.py` + `/exp_loop` |
| Pairwise preference + confidence gate *c*=0.7 | `reference/preference.py` · `tournament.py` |
| High-volume gen *m*=10 → Top-*k*=1 verify | `reference/tournament.py` |
| Profile→Verify→Verbalize data report | `reference/data_report.py` + `prompts/` |
| Symptom→2–3 verifiable actions (bundled) | `reference/tricks_catalog.md` · `tricks.py` |
| Model select (HF/Arena/SuperCLUE + family drill-down) | `reference/model_leaderboards.md` · `model_select.py` |
| Plan template (数据侧/模型侧/训练侧) | `reference/plan_template.md` · `plan_template.py` |
| Decouple exploration from expensive execution | 分析与方案探索优先于长时训练 |

默认超参：`m_candidates=10`, `confidence_gate=0.7`, `top_k_verify=1`。

Exp_Sandbox 是独立的 Agent 指令包，**不包含**该仓库的运行时代码；实验执行依赖用户提供的 `tool/function`（训练机、数据、模型入口等）。

```bibtex
@misc{zheng2026predictexecutingmachinelearning,
  title={Can We Predict Before Executing Machine Learning Agents?},
  author={Jingsheng Zheng and Jintian Zhang and Yujie Luo and Yuren Mao and Yunjun Gao and Lun Du and Huajun Chen and Ningyu Zhang},
  year={2026},
  eprint={2601.05930},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2601.05930}
}
```

---

## Layout

```text
skill-exp/
├── SKILL.md
├── VERSION
├── CHANGELOG.md
├── output-template.md
├── examples.md
├── reference/               # Agent 可参考的伪代码 / stubs
│   ├── predict_then_verify.py
│   ├── preference.py
│   ├── tournament.py
│   ├── data_report.py
│   ├── badcase.py
│   ├── mini_eval.py
│   ├── train_monitor.py
│   ├── orchestrator.py
│   └── prompts/
├── README.md
├── README.en.md
└── README.zh-CN.md
```

---

## License

MIT — use freely in research workflows and any agent runtime that loads this skill.
