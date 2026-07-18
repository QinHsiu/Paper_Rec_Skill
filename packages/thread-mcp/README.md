# Paper_Rec Thread Memory MCP

Exposes **Cognitive Thread** tools (not a duplicate literature-search MCP). Compose with [article-mcp](https://github.com/fangfuzha/article-mcp) for retrieval; use this server for long-horizon research memory.

## Install

```bash
cd packages/thread-mcp
pip install -e .
# also needs wiki-bridge on PYTHONPATH / installed
pip install -e ../wiki-bridge
```

## Run

```bash
set PAPER_REC_ROOT=D:\PycharmProjects\pythonProject\projects\Paper_Rec_Skill
paper-rec-threads
# or: python -m thread_mcp.server
```

## Cursor / Claude Desktop

```json
{
  "mcpServers": {
    "paper-rec-threads": {
      "command": "python",
      "args": ["-m", "thread_mcp.server"],
      "env": {
        "PAPER_REC_ROOT": "D:/PycharmProjects/pythonProject/projects/Paper_Rec_Skill",
        "PYTHONPATH": "D:/PycharmProjects/pythonProject/projects/Paper_Rec_Skill/packages/wiki-bridge;D:/PycharmProjects/pythonProject/projects/Paper_Rec_Skill/packages/thread-mcp"
      }
    }
  }
}
```

## Tools

| Tool | Purpose |
|------|---------|
| `thread_list` | List threads |
| `thread_get` | Full state + events |
| `thread_search_context` | Hypothesis/claims/gaps/seeds for query rewrite |
| `thread_score_papers` | Score candidate papers (JSON list) |
| `thread_link_paper` / `thread_link_exp` | Accept membership |
| `thread_delta` | Watch/Delta brief |
| `thread_claim_suggest` / `thread_claim_accept` | Claim gate |

See `docs/MCP.md` and `docs/THREAD_DESIGN.md`.
