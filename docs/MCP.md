# MCP — Thread Memory

Paper_Rec ships a **Thread Memory MCP** (`packages/thread-mcp`) so Cursor / Claude Desktop / other MCP clients can read and update Cognitive Threads without owning the whole Wiki UI.

## Why not another search MCP?

[article-mcp](https://github.com/fangfuzha/article-mcp) already covers multi-source literature search. Paper_Rec MCP focuses on **what only we have**: hypothesis, claims, Claim–Evidence Map, evidence gaps, ledger gates, lit↔exp membership, and Watch/Delta.

Recommended composition:

1. article-mcp (or Skill `/query_*`) → candidate papers  
2. `thread_query_hint` / `thread_search_context` / `thread_score_papers` → Thread-conditioned judgment  
3. `thread_link_*` + `thread_add_evidence` after human/agent gate  

## Quick config (2.9.0+)

**No PYTHONPATH required.** Set `PAPER_REC_ROOT` to the workspace root; the server auto-adds `packages/wiki-bridge`.

```json
{
  "mcpServers": {
    "paper-rec-threads": {
      "command": "python",
      "args": ["-m", "thread_mcp.server"],
      "env": {
        "PAPER_REC_ROOT": "D:/PycharmProjects/pythonProject/projects/Paper_Rec_Skill"
      }
    }
  }
}
```

Install once:

```bash
pip install -e packages/wiki-bridge -e packages/thread-mcp
pip install "mcp>=1.0"
```

See [`packages/thread-mcp/README.md`](../packages/thread-mcp/README.md).

| Var | Meaning |
|-----|---------|
| `PAPER_REC_ROOT` | Workspace root containing `content/threads/` |

## Tools summary

| Tool | Role |
|------|------|
| `thread_list` / `thread_get` | List / full state + evidences |
| `thread_search_context` / `thread_query_hint` | Context + query hints for external search |
| `thread_score_papers` | Score candidates vs thread |
| `thread_link_paper` / `thread_link_exp` | Membership |
| `thread_add_evidence` | Claim–Evidence Map |
| `thread_delta` / `thread_claim_*` | Watch + claim gates |
| `wiki_list_papers` | Local wiki cards |
| `exp_list` / `exp_get_metrics` | Local experiment metrics |
