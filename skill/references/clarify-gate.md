# Clarify-with-user gate (open_deep_research)

Before Module 1 rewrite / retrieval, if the ask is ambiguous, emit JSON and **stop**:

```json
{
  "need_clarification": true,
  "question": "<one focused question>",
  "verification": "<what you will do after the answer>"
}
```

If clear enough:

```json
{
  "need_clarification": false,
  "question": "",
  "verification": "<one-line plan of Module 1–2>"
}
```

Triggers: missing domain, conflicting goals, bare “最新” without field, or Q1/rank intent with `ambiguous=true` from `rank-intent`.
