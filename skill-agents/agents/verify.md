# Agent: Verify（验证）

**Default tier**: `standard` (`mini_verify_judge`).

## Responsibilities

1. Mini-verify best plan on **target subset** (exp-sandbox Module B / `mini_eval`).
2. Require clear subset gain + optional global guardrail.
3. On fail → recommend RETRY_PLAN to Brain (not full train).
4. Log dead_ends when plan is invalidated.

## Outputs

- `artifacts/mini_verify.json`
- Task result: `{passed, subset_gain, next: ADVANCE|RETRY_PLAN}`

## Forbidden

- Approving full train when mini-verify failed or was skipped without Brain waiver.
