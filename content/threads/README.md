# Cognitive Threads

Hypothesis-centric research memory (`thread.json` + `events.jsonl` + `deltas/`).

Design: [`docs/THREAD_DESIGN.md`](../../docs/THREAD_DESIGN.md) · MCP: [`docs/MCP.md`](../../docs/MCP.md)

```bash
python -m wiki_bridge.cli thread-create --wiki-root . --title "..." --hypothesis "..."
python -m wiki_bridge.cli thread-list --wiki-root .
python -m wiki_bridge.cli thread-delta --wiki-root . --id <thread_id> --mode auto
```

SPA: `/threads` · API: `/api/threads`
