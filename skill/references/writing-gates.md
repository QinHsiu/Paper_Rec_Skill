# Citation & writing gates (AI-Research-SKILLs inspired)

Use after `/draft` / related-work / before `latex-export`.

## Contribution gate

1. One-sentence contribution confirmed with user (or thread hypothesis).
2. Prefer **Figure 1** sketch (`/draw` or diagram note) before long abstract prose.
3. Abstract ≈ 5 sentences only after contribution + figure intent exist.

## Citation pipeline (never invent BibTeX)

```text
SEARCH → VERIFY (≥2 sources: OpenAlex/arXiv/DOI) → RETRIEVE BibTeX →
VALIDATE claim-in-source → ADD
```

If any step fails → `[CITATION NEEDED]` or `PLACEHOLDER_<key>` — then run:

```powershell
python -m wiki_bridge.cli citation-verify --bib refs.bib --write-filtered
python -m wiki_bridge.cli claim-ledger --thread <id> --strict
python -m wiki_bridge.cli number-verify --thread <id> --exp-dir content/exp/<id> --strict
python -m wiki_bridge.cli number-verify --thread <id> --exp-dir content/exp/<id> --hard-gate --write-registry
python -m wiki_bridge.cli latex-export --thread <id> --exp-dir content/exp/<id> --hard-gate
python -m wiki_bridge.cli stats-rigor --thread <id> --strict
python -m wiki_bridge.cli fig-review --draft draft.md --emit-vlm-prompts --out fig_review.json --strict
# Optional: fill VLM JSON then re-run with --vlm-json reviews.json
python -m wiki_bridge.cli posthoc-cite --thread <id> --evidences-json evs.json
python -m wiki_bridge.cli feedback-edit --question "..." --answer-file ans.md --evidences-json evs.json --candidates-json pool.json
# Grounded Q&A: score chunks first, then expand cites
python -m wiki_bridge.cli gather-evidence --question "..." --documents docs.json --out evs.json
python -m wiki_bridge.cli answer-ground --answer "..." --evidences-json evs.json --relevance-cutoff 3.0
```

## Post-draft audit (short)

- [ ] Every claim sentence cites or is MATERIAL GAP
- [ ] Limitations section present
- [ ] Repro: seed / data / code filter noted
- [ ] Stats: metric + split named (no bare “SOTA”); Results floats have ±/CI/seeds (`stats-rigor`)
- [ ] Figures have captions and body refs match (`fig-review`)

## Bounded reviewer → reviser (gpt-researcher · max 3)

After `/draft`, run a guideline-only review (no new facts):

1. Reviewer returns **accept** (`None`) or a short revision note list.
2. Reviser applies notes; re-run `claim-ledger` + `citation-verify`.
3. Cap **3** revision rounds; then stop and surface remaining gaps to the user.

Do not invent sources during revise — only restructure or mark `[CITATION NEEDED]`.

## Related-work outline merge (AutoSurvey · optional)

For large hit lists use the CLI survey writer:

```powershell
python -m wiki_bridge.cli survey-draft --json papers.json --topic "RAG" --out related_work_draft.md --strict
```

Pipeline: draft outline chunks from disjoint paper batches → merge headings → edit to drop overlapping subsections → subsection RAG paragraphs. Prefer section **description** as the retrieval query for each subsection’s local paper set.

## Idea novelty kill-switch

Before long experiments on a new idea:

```powershell
python -m wiki_bridge.cli novelty-check --idea "..." --papers-json corpus.json --strict
```

Optional `--openalex` for live literature hint (soft-fail offline).

Scored venue-style review: [`neurips-review-gate.md`](neurips-review-gate.md) (AI-Scientist).
