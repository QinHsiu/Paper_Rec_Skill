# Rebuttal venue families (`/rebuttal`)

Progressive disclosure for Module 7. Confirm **current year** limits via venue site when unsure; values below are **defaults to verify**, not eternal truth.

## Families

| Family | Venues (examples) | Primary artifact | Typical constraint |
|--------|-------------------|------------------|--------------------|
| `ONE_PAGE_PDF` | CVPR, ICCV, ECCV | `rebuttal.tex` → 1-page PDF | Strict 1 page; often no new experiments in PDF body policy varies — **check kit** |
| `THREADED_DISCUSSION` | NeurIPS, ICLR, ACM MM | Per-reviewer OpenReview markdown + optional global | Char/word caps per box — **read current OR form** |
| `PER_REVIEW_TEXT` | ICML, KDD (text boxes) | `PASTE_READY_Rk.txt` per reviewer | Hard character budget |
| `JOURNAL_POINT_BY_POINT` | Nature family, IEEE/ACM journals | Response letter + change map | Polite letter; line/page change refs |
| `ROLLING_REVISION` | ARR, TMLR | Response + revision plan | Multi-round; track score deltas |

Detect from user (`venue:cvpr`, “OpenReview”, “major revision”) or ask once.

## Output routing

```
content/threads/<id>/drafts/rebuttal/   # or content/rebuttal/<slug>/
  ISSUE_BOARD.md
  comment_map.json
  EXPERIMENT_PLAN.md
  revision_checklist.md
  cover_letter.md                 # journal / general
  responses.md                    # canonical point-by-point
  PASTE_READY_R1.txt …            # PER_REVIEW / THREADED
  rebuttal.tex                    # ONE_PAGE_PDF skeleton
  SAFETY_GATE.md
  rounds/r<n>/                    # follow-ups only
```

## Character budget gate

After drafting paste-ready text:

1. Count characters (or words if venue says words).  
2. If over budget → compress: cut pleasantries, merge Clarify, move tables to “see revision”.  
3. Record `budget: {limit, used, status}` in `comment_map.json`.  
4. Never claim “under limit” without counting.

## ONE_PAGE_PDF skeleton rules

- Title + paper ID + reviewers addressed.  
- Group by theme, not by dumping all quotes.  
- Prefer pointers: “See Sec X (rev)” over long essays.  
- New numbers only from verified registry / user-approved exp — else omit.

## Strategy color codes (Issue Board)

| Color | Meaning | Default stance lean |
|-------|---------|---------------------|
| 🔴 Blocker | Acceptance-critical | Agree+Revise or Disagree+strong evidence |
| 🟠 Major | Serious method/exp | Exp plan or Clarify with locus |
| 🟡 Minor | Writing / extra ablations | Agree+Revise or Clarify |
| 🟢 Easy win | Typo / missing cite | Agree+Revise |

Champion reviewer (most positive / pivotal AC) — address early in paste order when known.
