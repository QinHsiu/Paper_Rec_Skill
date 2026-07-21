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
```

## Post-draft audit (short)

- [ ] Every claim sentence cites or is MATERIAL GAP
- [ ] Limitations section present
- [ ] Repro: seed / data / code filter noted
- [ ] Stats: metric + split named (no bare “SOTA”)
