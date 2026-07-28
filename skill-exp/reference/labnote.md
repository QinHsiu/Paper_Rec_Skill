# Smart Experiment Lab Notebook (`/labnote`)

Autonomous **Research → Decide → Verify → Reflect** notebook — peer of `/exp_loop`, optimized to be the strongest open **and** closed offering by binding narrative to **verified metrics + Thread + dead-ends**.

## Positioning (beat OSS + closed)

| Competitor pattern | Gap | Our edge |
|--------------------|-----|----------|
| W&B / MLflow / TB | Metrics without *why* | H→E→F cards + decision log |
| labcoat / wastebook | Needs wandb + LLM key; weak paper/thread | Local-first; Wiki/Thread/claim-ledger |
| crux | Strong bars; light training loop | Bars **+** `/exp_loop` tree + dead_ends |
| aexp | H→E→F + git; W&B-centric | Same grammar + `number-verify` hard gate |
| ResearcherSkill `.lab/` | Code optimize loop | ML research OS: papers → exp → rebuttal |
| Notion / ChatGPT notes | No gates | Mechanical verdict + registry-only numbers |

**Product rule:** Never invent metrics. Notebook prose may cite a number only if it is in `metrics/` or passes `number-verify` / verified registry.

## Commands

| Command | Mode |
|---------|------|
| `/labnote` | One-shot: init or append+verify+synthesize for current exp |
| `/labnote init` | Scaffold `labbook/` + lock pass/fail bars |
| `/labnote append` | Add H→E→F entry from latest run signals |
| `/labnote verify` | Run mechanical + registry gates |
| `/labnote synthesize` | Rebuild INDEX / findings / research-state |
| `/labnote_loop` | Autonomous multi-round Research→Decide→Verify until stop |

Triggers: 实验笔记 / lab notebook / findings diary / 智能实验笔记.

## Layout

```text
content/exp/<id>/
  labbook/
    config.md              # locked bars + target_score (immutable after lock)
    INDEX.md               # rolling digest
    log.md                 # narrative journal
    results.tsv            # one row per entry
    parking-lot.md         # deferred ideas
    entries/E####.md       # H→E→F cards
    verify/E####.json      # per-entry gate results
    git_snapshots/E####.txt
  findings.md              # outer reflect (shared with exp-reflect)
  metrics/summary.json
  trace/dead_ends.md
  trace/exp_tree.json
```

## Entry card (H→E→F)

```markdown
# E0003 — <short title>
- status: open | verified | refuted | inconclusive | deferred
- created: ISO-8601
- git: <sha> dirty=<bool>
- links: plan=P* node=N* thread_claim=C* paper_refs=[]

## Hypothesis
<falsifiable statement; locked before reading new metrics when possible>

## Pre-locked bars (crux-style)
- [ ] bar_1: <metric> <op> <threshold> on <split>
- [ ] bar_2: ...

## Experiment
- change: <data | model | train pillar>
- command_or_run: <path / cmd>
- evidence_files: [metrics/..., figures/...]

## Finding
- mechanical_verdict: supported | partial | refuted | inconclusive
- narrative: ≤5 bullets; numbers only with registry locus
- lesson: <dead_end candidate if failed>

## Next
- decision: continue | stop | park
- proposed_plans: [P…]
```

## `/labnote_loop` (自行调研 · 自行决策 · 自行验证)

Mirror `/exp_loop` control flow; **notebook-first** (may call `/exp_*` when Decide needs new runs).

```text
loop:
  RESEARCH  → gather signals (metrics, logs, tree, dead_ends, thread, git)
  DECIDE    → ≥2 note-hypotheses / next actions; tournament; lock bars BEFORE interpret
  ACT       → write/append entry; optional trigger /exp_training|/exp_eval|/exp_loop slice
  VERIFY    → mechanical bars + number-verify + repro hint; never move goalposts
  REFLECT   → update INDEX, findings, parking-lot, dead_ends; stop?
```

### Stop when

1. `target_score` met **and** at least one entry `verified` with all bars checked, **or**
2. No positive-EV next action (all candidates in dead_ends / parking), **or**
3. User abort / max_rounds (default **8** notebook rounds)

### Research phase checklist

- [ ] Read `labbook/config.md` bars (create via init if missing)  
- [ ] Read dead_ends + exp_tree + latest metrics  
- [ ] Optional: thread gaps / claim-ledger open items  
- [ ] Optional lit: only if Decide needs method ideas — `/query_*` then cite wiki path, no fake papers  

### Decide phase rules

- Emit ≥2 candidates (prefer 5–10): each = hypothesis + bars + expected pillar change.  
- Pairwise preference with confidence gate **c=0.7** (same spirit as `reference/tournament.py`).  
- **Lock bars in the entry before** treating new metrics as evidence (no post-hoc threshold edits).  
- Skip any candidate whose lesson appears in dead_ends.

### Verify phase (hard)

```bash
python -m wiki_bridge.cli labnote --exp-dir content/exp/<id> --action verify --entry E0003
python -m wiki_bridge.cli number-verify --wiki-root . --thread <id> --exp-dir content/exp/<id> --strict
```

Mechanical verdict from checkboxes only (`[x]` met / `[ ]` unmet / `[-]` n/a) → `supported|partial|refuted|inconclusive`.  
Agent **must not** override mechanical verdict with vibes.

### Reflect phase

- Append `results.tsv` row; update `log.md`; rewrite `INDEX.md`.  
- Call `exp-reflect` / labnote synthesize so `findings.md` stays canonical.  
- On failure: append dead_end leaf before next Decide.  
- Offer Thread evidence stub; do not auto-accept claims.

## CLI

```bash
python -m wiki_bridge.cli labnote --exp-dir content/exp/<id> --action init \
  --hypothesis "..." --target-json target.json
python -m wiki_bridge.cli labnote --exp-dir content/exp/<id> --action append \
  --title "..." --hypothesis "..." --plan-id P2
python -m wiki_bridge.cli labnote --exp-dir content/exp/<id> --action verify --entry E0001
python -m wiki_bridge.cli labnote --exp-dir content/exp/<id> --action synthesize
python -m wiki_bridge.cli labnote --exp-dir content/exp/<id> --action status
```

## Sync

After verified entries accumulate, `sync-exp` as usual; Wiki 实验页 should link `labbook/INDEX.md`.  
Rebuttal / paper Results may only use numbers that survive verify.

## Anti-goals

- Not a second W&B.  
- Not unconstrained LLM diary.  
- Not “auto-publish” claims without gates.
