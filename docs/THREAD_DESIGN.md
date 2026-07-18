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
  evidences.jsonl  # Claim–Evidence Map (quote/metric/figure/note)
  deltas/          # Watch/Delta markdown briefs (Phase B)
```

## Phases (status)

| Phase | Scope | Status |
|-------|--------|--------|
| **A** | Model, bridge, API, Wiki UI, Skill 1.5/2.5 | done |
| **B** | Watch/Delta, graph thread/exp nodes, claim gate updates | done |
| **C** | `thread_*` MCP (memory first) | done |
| **D** | Wiki exp Chart.js viz + `/draw` venue styles | done |
| **E** | Claim–Evidence Map + MCP zero-PYTHONPATH / wiki·exp tools | done (2.9.0) |
| **F** | Iterative retrieval (`query_iter`) + multi-run exp board | done (2.10.0) |
| **G** | Cognitive map graph + timeline; PDF-lite; BibTeX; Related Work outline | done (2.12.0) |
| **H** | Install scripts; evidence confidence; PDF upload pipeline; query auto; writing recommend; MCP tools | done (2.14.0) |
| **I** | configure MCP; paper_draft; prerank; evidence UX; citation-expand | done (2.16.0) |

## Watch / Delta (Phase B)

CLI: `thread-delta --mode auto|new_digest|diff_brief|gap_focus|exp_bridge`  
API: `POST /api/threads/{id}/delta`  
Skill: `/wiki thread delta`

Claim proposals stay `gate:suggested` until `thread-claim --accept` or API `/claims/accept`.

## Claim–Evidence Map (Phase E / 2.9.0)

Evidence binds a **claim_id** to a paper quote, exp metric, figure, or note (`evidences.jsonl`). Gates: `suggested` → `accepted`.

- CLI: `thread-evidence-add|list|gate`
- API: `/api/threads/{id}/evidences`, `/evidence-map`, gate endpoint; `GET` thread includes `evidences` + `evidence_map`
- Wiki: PageView select text →「挂到主线」; ThreadDetail evidence panel
- MCP: `thread_add_evidence`

Does **not** auto-extract claims from full PDFs (human highlight + agent suggest only).

## Iterative retrieval (Phase F / 2.10.0)

Skill Modules **2a/2b**: multi-path queries + ≤1 refine wave when `thread:` or `iterative`. Ledger kind `query_iter`.

- CLI: `query-trace --thread … --json trace.json`
- API: `POST /api/threads/{id}/query-trace`
- Report: `retrieval_trace` in JSON → auto-appended on `sync-report --thread`

## Multi-run curves (Phase F / 2.10.0)

`metrics/curves.json` + `metrics/curves_<run>.json` → API `curve_runs[]`. Wiki ExpDetail: run overlay, compare exp, primary-only, 5s poll.

## Related Work outline (Phase G)

CLI: `related-work --thread` → `content/threads/<id>/drafts/related_work_outline.md`  
API: `POST /api/threads/{id}/related-work`  
Skill: `/wiki thread related-work`

## PDF-lite + BibTeX (Phase G)

- `pdf-ingest` → `fulltext.md`; `claim-suggest --apply` → suggested claims/evidences  
- `bibtex-export`; API `GET /api/wiki/bibtex?paths=`

## Cognitive graph (Phase G)

CLI: `thread-graph` · API: `GET /api/threads/{id}/graph` (nodes/edges + day-grouped timeline)

## MCP (Phase C + E)

Package: `packages/thread-mcp` — set `PAPER_REC_ROOT` only (auto-locates wiki-bridge).

Tools: `thread_list|get|search_context|query_hint|score_papers|link_*|add_evidence|delta|claim_*` · `wiki_list_papers` · `exp_list|exp_get_metrics`.

## Venue styles (Phase D)

`skill-draw/lib/venues.py` + `draw(..., venue="cvpr")` / CLI `--venue`.

## Bridge CLI

```text
thread-create | thread-list | thread-show
thread-link-paper | thread-link-exp
thread-evidence-add | thread-evidence-list | thread-evidence-gate
thread-delta | thread-claim
query-trace
sync-report --thread <id> [--auto-link]
sync-exp --thread <id>
```

## API

`/api/threads` — CRUD + link + timeline + delta + context + score + claims + evidences + evidence-map + query-trace + by-paper / by-exp.
`/api/exp/{id}` — includes `curves` + `curve_runs`.
