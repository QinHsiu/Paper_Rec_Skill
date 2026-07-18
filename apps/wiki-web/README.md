# Paper_Rec Wiki Web (Vue 3)

Self-hosted SPA for the reading lab: papers, **research threads**, experiments, graph, weekly.

## Stack

- Vue 3 + Vue Router + Pinia
- Markdown: marked + DOMPurify
- Editor: CodeMirror 6 (Markdown) + live preview + image paste/upload
- Graph / charts: Chart.js (scatter graph; interactive experiment curves)

## Routes

| Path | View |
|------|------|
| `/pages` · `/page/:path` | 论文库 |
| `/threads` · `/threads/:id` | 研究主线（Delta / claims） |
| `/experiments` · `/experiments/:id` | 实验（交互曲线 + 指标图） |
| `/graph` | 知识图谱（含 thread / experiment 节点） |
| `/weekly` · `/ask` · `/skills` | 一周推荐 / Ask / Skills |

## Dev

```bash
# terminal 1
cd apps/wiki-api && pip install -r requirements.txt && uvicorn app:app --reload --port 8787

# terminal 2
cd apps/wiki-web && npm install && npm run dev
```

Or from workspace root: `apps/start-wiki.ps1`

Open http://127.0.0.1:5173/ · http://127.0.0.1:5173/threads
