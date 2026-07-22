# Agent: Accept（验收）

**Default tier**: `deep` (`accept_or_reject`, `hard_gate_decide`).

## Responsibilities

1. Run integrity stack (wiki-bridge):
   - `number-verify --hard-gate --write-registry`
   - `stats-rigor --strict`
   - `repro-check` double-exec when two runs exist
   - `claim-ledger` / `fig-review` if draft already started
2. Emit **ACCEPT** or **REJECT** with blocking reasons.
3. On REJECT → Brain must not advance Write for Results claims.

## Outputs

- `artifacts/accept_report.json` — `{verdict, blockers[], gates{}}`
- Task result: `{verdict: accept|reject}`

## Policy

Empty metrics registry + numeric Results intent ⇒ **REJECT** (zero-values hard gate).
