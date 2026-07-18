# Cognitive Thread v2 — Design Contract

Hypothesis-centric **Research Thread** for Paper_Rec. Differentiates from Anaxa (quest→manuscript audit), PaperSeek (generic discovery), YFR (topic monitoring/survey ops), and article-mcp (search MCP) by owning **long-horizon personal research memory**: claims, gaps, evidence gates, lit↔exp links.

See also: competitor notes in workspace `projects/same.txt`. MCP: [MCP.md](MCP.md).

## Non-goals (explicit)

- Manuscript / LaTeX / citation-audit / PDF finalization (Anaxa)
- Generic “best-in-class” search agent without thread context (PaperSeek)
- Multi-tenant public survey / WeChat draft factory (YFR)
- Duplicate literature-search MCP (compose article-mcp instead)

## Layout

```text
content/threads/<thread_id>/
  thread.json      # canonical structured state
  README.md        # human notes + mirror of title/status/hypothesis
  events.jsonl     # cognitive ledger (append-only)
  deltas/          # Watch/Delta markdown briefs (Phase B)
```

## Phases (status)

| Phase | Scope | Status |
|-------|--------|--------|
| **A** | Model, bridge, API, Wiki UI, Skill 1.5/2.5 | done |
| **B** | Watch/Delta, graph thread/exp nodes, claim gate updates | done |
| **C** | `thread_*` MCP (memory first) | done |
| **D** | Wiki exp Chart.js viz + `/draw` venue styles | done |

## Watch / Delta (Phase B)

CLI: `thread-delta --mode auto|new_digest|diff_brief|gap_focus|exp_bridge`  
API: `POST /api/threads/{id}/delta`  
Skill: `/wiki thread delta`

Claim proposals stay `gate:suggested` until `thread-claim --accept` or API `/claims/accept`.

## MCP (Phase C)

Package: `packages/thread-mcp` — tools `thread_list|get|search_context|score_papers|link_*|delta|claim_*`.

## Venue styles (Phase D)

`skill-draw/lib/venues.py` + `draw(..., venue="cvpr")` / CLI `--venue`.

## Bridge CLI

```text
thread-create | thread-list | thread-show
thread-link-paper | thread-link-exp
thread-delta | thread-claim
sync-report --thread <id> [--auto-link]
sync-exp --thread <id>
```

## API

`/api/threads` — CRUD + link + timeline + delta + context + score + claims + by-paper / by-exp.
