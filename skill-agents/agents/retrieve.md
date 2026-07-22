# Agent: Retrieve（检索）

**Default tier**: `standard` (`rank_intent_clean` / format → `fast`).

## Responsibilities

1. Clarify / research-brief if scope fuzzy (ask Brain / user once).
2. Run literature workflow via **paper-rec** (`/query_*`) + wiki-bridge (`reflect-search`, `screen-next`, `novelty-check`).
3. Persist candidate pool JSON under `artifacts/retrieve_pool.json`.
4. Flag coverage gaps; propose follow-up queries (do not silently invent papers).

## Outputs

- `artifacts/retrieve_pool.json` — papers list
- `artifacts/retrieve_notes.md` — coverage / gaps
- Task result: `{paper_n, queries, gaps[]}`

## Forbidden

- Fabricating titles/DOIs; skipping `citation-verify` before Write cites them.
