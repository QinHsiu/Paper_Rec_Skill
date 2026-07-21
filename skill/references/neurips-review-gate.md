# NeurIPS-style draft review gate (AI-Scientist)

Run after `/draft` + `claim-ledger` + `citation-verify`, before `latex-export`.

## Output format

```text
THOUGHT:
<specific notes for THIS draft — no generic praise>

REVIEW JSON:
```json
{
  "Summary": "...",
  "Strengths": ["..."],
  "Weaknesses": ["..."],
  "Originality": 1-4,
  "Quality": 1-4,
  "Clarity": 1-4,
  "Significance": 1-4,
  "Questions": ["..."],
  "Limitations": ["..."],
  "Ethical Concerns": false,
  "Soundness": 1-4,
  "Presentation": 1-4,
  "Contribution": 1-4,
  "Overall": 1-10,
  "Confidence": 1-5,
  "Decision": "Accept" | "Reject"
}
```

## Rules

- Be critical; inventing missing experiments → lower Quality/Soundness.
- `Decision` only Accept/Reject (no borderline labels).
- Persist JSON under `content/threads/<id>/drafts/paper_draft/review.json`.
- If Reject or Overall ≤ 5 → run bounded reviser (max 3) from `writing-gates.md`.
