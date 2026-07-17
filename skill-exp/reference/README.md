# Reference Code Modules / 参考代码模块

Agent-facing **reference implementations & pseudocode** for Exp_Sandbox.

These modules are **not** a vendored copy of [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute).  
They **adapt** published ideas (Predict-then-Verify, data-centric pairwise preference, Profile→Verify→Verbalize data reports, confidence gate) into stubs the agent can follow when running `/exp_*`.

| File | Role |
|------|------|
| [`types.py`](types.py) | Shared dataclasses (`Plan`, `PreferenceVote`, `TargetScore`, …) |
| [`data_report.py`](data_report.py) | Build verified verbal data reports (analysis for preference) |
| [`preference.py`](preference.py) | Pairwise solution preference + confidence parse |
| [`tournament.py`](tournament.py) | Generate *m* plans → confidence-gated pairwise → Top-*k* |
| [`predict_then_verify.py`](predict_then_verify.py) | Core Predict-then-Verify loop |
| [`badcase.py`](badcase.py) | Badcase cluster → special questions → multi-plans |
| [`mini_eval.py`](mini_eval.py) | Small-slice validation before full train |
| [`train_monitor.py`](train_monitor.py) | Loss / metric curve monitoring helpers |
| [`orchestrator.py`](orchestrator.py) | Maps `/exp_loop` to the above pipeline |
| [`prompts/`](prompts/) | Prompt templates adapted from the paper appendix |

## How the agent should use this

1. Prefer calling the **algorithms** (function names / steps) rather than inventing a new loop.
2. Replace `NotImplemented` / `ToolHook` bodies with the user’s real `tool/function` (SSH train, local scripts, APIs).
3. Always log artifacts under `content/exp/<experiment_id>/`.
4. Default hyperparameters (from ForeAgent paper defaults): `m=10`, `confidence_gate=0.7`, `top_k=1`.

## Defaults (paper-aligned)

```python
DEFAULTS = dict(m_candidates=10, confidence_gate=0.7, top_k_verify=1)
```

## Attribution

Paper: *Can We Predict Before Executing Machine Learning Agents?* ([arXiv:2601.05930](https://arxiv.org/abs/2601.05930))  
Code reference: [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute)  
Prompt wording in `prompts/` is adapted from the paper appendix (Data Analysis Report / Result Prediction / Complexity Scoring).
