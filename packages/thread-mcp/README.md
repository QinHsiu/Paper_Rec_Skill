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

## Cursor / Claude Desktop（复制即用）

只需设置 `PAPER_REC_ROOT`；**不必再配 PYTHONPATH**（server 会自动找到 `wiki-bridge`）。

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

## Tools

| Tool | Purpose |
|------|---------|
| `thread_list` / `thread_get` | List / full state + evidences |
| `thread_search_context` / `thread_query_hint` | Context + query hints for external search |
| `thread_score_papers` | Score candidates vs thread |
| `thread_link_paper` / `thread_link_exp` | Membership |
| `thread_add_evidence` | Claim–Evidence Map (+ confidence / support_status) |
| `thread_graph` | Cognitive map JSON |
| `bibtex_export` / `related_work` / `section_outline` | Export & writing frames |
| `thread_delta` / `thread_claim_*` | Watch + claim gates |
| `wiki_list_papers` / `exp_list` / `exp_get_metrics` | Local wiki/exp read |

Compose retrieval with [article-mcp](https://github.com/fangfuzha/article-mcp); this server owns **memory**.

See `docs/MCP.md` and `docs/THREAD_DESIGN.md`.
