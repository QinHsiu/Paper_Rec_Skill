# MCP Publish Checklist

Paper_Rec ships **Thread Memory MCP** (`packages/thread-mcp`) — research memory, not a second literature-search server.

Compose with [article-mcp](https://github.com/fangfuzha/article-mcp) for search.

## Single config (copy)

```json
{
  "mcpServers": {
    "paper-rec-threads": {
      "command": "python",
      "args": ["-m", "thread_mcp.server"],
      "env": {
        "PAPER_REC_ROOT": "/absolute/path/to/Paper_Rec_Skill"
      }
    }
  }
}
```

Install: `pip install -e packages/wiki-bridge -e packages/thread-mcp && pip install "mcp>=1.0"`.

## Directory / market submission

When submitting to [Glama](https://glama.ai/) or other MCP catalogs:

1. **Name**: Paper_Rec Thread Memory  
2. **One-liner**: Hypothesis / claims / evidence / lit↔exp memory for personal research threads  
3. **Not for**: Generic arXiv search (point users to article-mcp)  
4. **Tools**: list from `docs/MCP.md`  
5. **Screenshots**: Cursor MCP tool list + Thread Wiki page  
6. **Repo**: https://github.com/QinHsiu/Paper_Rec_Skill  
7. **License**: MIT  

Do **not** advertise a separate `search-mcp` product under this repo's positioning.
