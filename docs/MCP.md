# MCP — Thread Memory

Paper_Rec ships a **Thread Memory MCP** (`packages/thread-mcp`) so Cursor / Claude Desktop / other MCP clients can read and update Cognitive Threads without owning the whole Wiki UI.

## Why not another search MCP?

[article-mcp](https://github.com/fangfuzha/article-mcp) already covers multi-source literature search. Paper_Rec MCP focuses on **what only we have**: hypothesis, claims, Claim–Evidence Map, evidence gaps, ledger gates, lit↔exp membership, and Watch/Delta.

Recommended composition:

1. article-mcp (or Skill `/query_*`) → candidate papers  
2. `thread_query_hint` / `thread_search_context` / `thread_score_papers` → Thread-conditioned judgment  
3. `thread_link_*` + `thread_add_evidence` after human/agent gate  

### Session pattern (gptr-mcp inspired)

Prefer a stable **`thread_id` / research_id** for the turn:

1. `thread_show` / create → bind session  
2. **quick** path: `thread_search_context` + score (shallow)  
3. **deep** path: multi-path `/query_*` + evidence adds + `claim-ledger`  
4. Always expose **sources** (`paper_paths` / cite keys) before claiming context is grounded  

Do not invent a second research MCP; chain Thread tools with Skill retrieval.

## Quick config (2.16+)

**推荐**：安装后先 dry-run，再 `--apply` 写入。

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File scripts/configure-mcp.ps1
powershell -ExecutionPolicy Bypass -File scripts/configure-mcp.ps1 -Apply
```

```bash
# macOS / Linux
chmod +x scripts/configure-mcp.sh
./scripts/configure-mcp.sh
./scripts/configure-mcp.sh --apply
# after pip install -e packages/thread-mcp:
paper-rec-configure --apply
```

- 默认目标：`docs/mcp.example.json` + 项目 `.cursor/mcp.json`
- 全局 Cursor / Claude Desktop：`--target cursor-user` / `--target claude-desktop`（建议加 `--force`，会写 `.bak`）
- VS Code Continue：见下方提示，手动合并同一 `mcpServers` 块

**No PYTHONPATH required.** Set `PAPER_REC_ROOT` to the workspace root; the server auto-adds `packages/wiki-bridge`.

```json
{
  "mcpServers": {
    "paper-rec-threads": {
      "command": "python",
      "args": ["-m", "thread_mcp.server"],
      "env": {
        "PAPER_REC_ROOT": "/path/to/Paper_Rec_Skill"
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
| `thread_score_papers` / `prerank_papers` | Score vs thread / BM25 pre-rank |
| `thread_link_paper` / `thread_link_exp` | Membership |
| `thread_add_evidence` / `evidence_coverage` | Claim–Evidence Map + confidence UX + CEBM-lite |
| `thread_graph` / `bibtex_export` / `related_work` / `section_outline` / `paper_draft` | Graph + writing frames |
| `citation_expand` | 1-hop refs (S2/Crossref) |
| `thread_delta` / `thread_claim_*` | Watch + claim gates |
| `wiki_list_papers` | Local wiki cards |
| `exp_list` / `exp_get_metrics` | Local experiment metrics |

## Compose with search MCPs

Paper_Rec MCP = **memory**. For multi-source search / OA PDF download chains, also install:

- [scholar-mcp](https://github.com/Liyux3/scholar-mcp) (`uvx scholar-mcp`) — RRF search + PDF tools  
- or [PaperSeek](https://github.com/MingfengHong/paperseek) (`paperseek-mcp`) — iterative literature agent  

Then: search MCP → candidates → `rrf_fuse` / `prerank_papers` / `thread_score_papers` → `thread_link_*` / `pdf_fetch` / `thread_add_evidence`.

Local OA fetch (no Sci-Hub): Wiki「获取全文」or `wiki_bridge pdf-fetch`.

## Related

- Chat bots (Feishu / Telegram / WeCom / QQ): [BOTS.md](BOTS.md)
- One-way Delta push: [WEBHOOK.md](WEBHOOK.md)
