# Exp_Sandbox (English)

An **Agent Skill** for an automated ML experiment sandbox: analyze data/badcases → propose multiple plans → mini-verify → train with monitors → evaluate against `target_score` → self-loop until done.

Works with Claude Code, Codex, OpenClaw, and other Markdown-skill runtimes. Attach finished runs with `wiki_bridge sync-exp --thread <id>`.

---

## Commands

| Command | Role |
|---------|------|
| `/exp_analysis` | Analysis mode |
| `/exp_analysis train` or `/analysis train` | Training-set analysis |
| `/exp_analysis eval` or `/analysis eval` | Eval/test-set analysis |
| `/exp_training` | Launch training; monitor loss, val metrics, curves |
| `/exp_eval` | Evaluation metrics vs `target_score` |
| `/exp_loop` | Self-loop: `analysis([plan])_clean_validation_training_evaluation_next-step` |

---

## Run context

- **target_score**: task + eval set + metric threshold  
- **tool/function**: closed/open models, data access, train servers, resource notes  
- **analysis_tool?**: if absent, use default stats/visualization (image size/resolution, audio duration/sample rate, text length/label distribution, …)  
- **other_source_model**: Papers With Code, Hugging Face results, Wiki paper notes  

---

## Pipeline (short)

1. Badcases → diverse clusters → named problems → multi-plans  
2. Record plan → data/label clean → mini-evaluation cycle  
3. Training monitors (loss + metrics + curves)  
4. On success or exhausted plans → final report + future options  

See [SKILL.md](SKILL.md), reference stubs [`reference/`](reference/), [output-template.md](output-template.md), [examples.md](examples.md).

---

## Install

```bash
mkdir -p .agents/skills/exp-sandbox
cp -r ./* .agents/skills/exp-sandbox/
```

---

## Acknowledgement

Ideas adapted from [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute) (Predict-then-Verify / FOREAGENT): rank and mini-verify plans before full training to reduce wasted execution. This skill is an independent instruction pack and does **not** ship that repository’s code. Full attribution and citation: [README.md § Acknowledgement](README.md#acknowledgement--借鉴说明).
