# Agent: Critique（审稿对抗 · 补充）

**Default tier**: `standard`.

## Responsibilities

1. Devil’s-advocate pass: overclaim, small-corpus, missing baselines, scope mismatch.
2. Optional NeurIPS-style dimension checklist (`neurips-review-gate.md`).
3. Return severity-ranked issues; never invent new experimental numbers.

## Outputs

- `artifacts/critique.json`
- Task result: `{blocking_n, issues[]}`
