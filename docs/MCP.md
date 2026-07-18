# MCP — Thread Memory

Paper_Rec ships a **Thread Memory MCP** (`packages/thread-mcp`) so Cursor / Claude Desktop / other MCP clients can read and update Cognitive Threads without owning the whole Wiki UI.

## Why not another search MCP?

[article-mcp](https://github.com/fangfuzha/article-mcp) already covers multi-source literature search. Paper_Rec MCP focuses on **what only we have**: hypothesis, claims, evidence gaps, ledger gates, lit↔exp membership, and Watch/Delta.

Recommended composition:

1. article-mcp (or Skill `/query_*`) → candidate papers  
2. `thread_score_papers` / `thread_search_context` → Thread-conditioned judgment  
3. `thread_link_*` after human/agent gate  

## Quick config

See [`packages/thread-mcp/README.md`](../packages/thread-mcp/README.md).

Environment:

| Var | Meaning |
|-----|---------|
| `PAPER_REC_ROOT` | Workspace root containing `content/threads/` |

## Tools summary

`thread_list` · `thread_get` · `thread_search_context` · `thread_score_papers` · `thread_link_paper` · `thread_link_exp` · `thread_delta` · `thread_claim_suggest` · `thread_claim_accept`
