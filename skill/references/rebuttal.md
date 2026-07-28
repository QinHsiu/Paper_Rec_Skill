# Rebuttal (`/rebuttal`)

Evidence-first author response. Absorbs venue routing + exp triage + safety gates; **wins** by binding replies to Paper_Rec Thread · claim-ledger · number-verify · `/exp_*`.

## Positioning (它无我有 · 它有我优)

| Axis | Typical competitors | This skill |
|------|---------------------|------------|
| Venue formats | Strong (omnirebuttal etc.) | Same families + **verify-current-rules** step — see [`rebuttal-venues.md`](rebuttal-venues.md) |
| Grounding | Paper text / optional search corpus | Paper + **thread claims/gaps** + **verified metrics registry** |
| New experiments | Plan or auto-run in repo | Explicit `EXPERIMENT_PLAN` → `/exp_*` → `number-verify` before citing |
| Safety | Char gates / anti-fabricate | Plus **SAFETY_GATE** + optional rehearsal vs [`neurips-review-gate.md`](neurips-review-gate.md) |
| Multi-round | Often yes | `rounds/r<n>/` delta-only replies + score tracker |

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| Reviews | Yes | Paste, path, or `review.json` |
| Draft / paper | Strongly preferred | `paper_draft/`, wiki, PDF/LaTeX |
| `venue:` / family | Recommended | Else detect or ask |
| `thread:<id>` | Recommended | Claims, gaps, evidences |
| Decision / meta-review | Optional | AE summary |
| Round | Optional | `round:1` (default) / `round:2` follow-up |

Missing reviews → ask once. Never invent reviewer text.

## Language

Match reviews (usually English). Announce: `Mode: rebuttal → {language} · family={FAMILY} · round={n}`.

## Pipeline

### 0. Venue lock

Resolve family via [`rebuttal-venues.md`](rebuttal-venues.md). If limit unknown → web-check or ask; record assumed limit as `unverified` until confirmed.

### 1. Parse → Issue Board

Atomic ids `R{k}-C{n}`. Write `ISSUE_BOARD.md` with color codes (🔴🟠🟡🟢). Split multi-issue paragraphs.

### 2. Map to ledger

Each comment → draft locus / `claim_id` / exp id / `UNMAPPED`. Prefer:

```bash
python -m wiki_bridge.cli claim-ledger --wiki-root . --thread <id> --out claim_ledger.json
```

### 3. Stance

`Agree+Revise` | `Clarify` | `Disagree+Evidence` | `Out of scope`  
Plus experiment triage when reviewer asks for numbers (next step).

### 4. Experiment triage → `EXPERIMENT_PLAN.md`

For each `needs_new_exp`:

| Decision | When | Action |
|----------|------|--------|
| `run` | Feasible in `/exp_*` sandbox | Create/update exp card; user confirms before train |
| `reanalyze` | Data exists; need table/plot | `/exp_eval` · `/draw` · then `number-verify` |
| `clarify` | Already in paper/appendix | Point to locus; no new run |
| `defer` | Too heavy / out of season | Honest timeline; **do not** fake completion |

**Hard rule:** rebuttal body may cite numbers only if they appear in draft, `metrics/`, or pass:

```bash
python -m wiki_bridge.cli number-verify --wiki-root . --thread <id> --exp-dir content/exp/<exp> --strict
```

### 5. Draft responses

Canonical `responses.md`. Then **route** to family artifacts (paste-ready / tex / letter) per venues doc.

Response pattern heuristics (no external 200k DB required):

- Misunderstood claim → quote paper sentence + section.  
- Missing baseline → add comparison **only** if runnable; else defer.  
- “Incremental” → restate delta vs closest cited work with evidence.  
- Extra ablation → offer 1 high-signal ablation, not laundry list.

### 6. Safety gate → `SAFETY_GATE.md`

Checklist (all must pass or user-waive):

- [ ] No fabricated citations / metrics / “we will run X” without `EXPERIMENT_PLAN` row  
- [ ] Every 🔴 has response  
- [ ] Char/word budget counted when family needs it  
- [ ] Promises match revision_checklist  
- [ ] Optional: hostile re-read (neurips-review-gate) on draft; label findings `rehearsal`, not fake reviewers  

### 7. Persist + verify

Paths under thread `drafts/rebuttal/` or `content/rebuttal/<slug>/`.

### Follow-up rounds (`round:n` n≥2)

- Diff new reviewer messages only → `rounds/r<n>/`.  
- Delta replies; do not resend full r1 wall of text unless asked.  
- Update score/engagement tracker table in `ISSUE_BOARD.md`.

## `comment_map.json` schema

```json
{
  "venue": "",
  "family": "THREADED_DISCUSSION",
  "paper_title": "",
  "thread_id": null,
  "round": 1,
  "budget": { "limit": null, "used": null, "unit": "chars", "status": "unverified|ok|over" },
  "comments": [
    {
      "id": "R1-C1",
      "reviewer": "R1",
      "severity": "major",
      "summary": "≤1 sentence",
      "stance": "Clarify",
      "locus": "Sec 4.2 / Table 2 / claim C3",
      "needs_new_exp": false,
      "exp_decision": null
    }
  ]
}
```

## Templates

### `responses.md` (per comment)

```markdown
### R1-C1
**Reviewer said:** …
**Severity:** 🟠 Major
**Stance:** Clarify
**Response:** …
**Revision:** None | Sec X | Table Y | …
**Evidence:** [原文] … | [registry] metrics/… | [未找到]
**Exp:** none | see EXPERIMENT_PLAN#E2
```

### Cover letter

5–8 lines: thanks, themes, global revisions, pointer to detailed responses.

## Hard rules

- Never invent reviewer quotes, citations, or metrics.  
- Prefer existing text over promising experiments.  
- `run` / `reanalyze` require user confirmation before claiming done.  
- Tone: professional, concise, non-defensive.

## Verify checklist

- [ ] Family + budget recorded  
- [ ] Issue Board covers all atoms  
- [ ] EXPERIMENT_PLAN for every needs_new_exp  
- [ ] SAFETY_GATE pass/waive  
- [ ] Family-specific paste/tex/letter emitted  
- [ ] No numeric claim without locus/registry
