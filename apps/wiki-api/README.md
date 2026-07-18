# Paper_Rec Wiki API (FastAPI)

Self-hosted wiki backend for papers, experiments, and Cognitive Threads.

## Run

```bash
cd apps/wiki-api
pip install -r requirements.txt
set PAPER_REC_ROOT=../../..   # optional; auto-detected
uvicorn app:app --reload --host 127.0.0.1 --port 8787
```

API base: http://127.0.0.1:8787/api/

| Prefix | Role |
|--------|------|
| `/api/wiki` | pages CRUD, search, graph (papers + **thread** / **experiment** nodes), upload |
| `/api/threads` | Cognitive Thread CRUD, delta, claims, context, score, by-paper/by-exp |
| `/api/exp` | experiment list/detail, metrics/curves, figure assets |
| `/api/weekly` | weekly digests |
| `/api/ask` | local wiki Q&A |
| `/api/skills` | Paper_Rec skill metadata |
| `/api/auth` | login stub |
| `/api/health` | content / exp / threads roots |
| `/uploads` | uploaded images |

Content roots: `content/wiki/pages`, `content/threads`, `content/exp`, `content/weekly`, `content/uploads`.

See [docs/THREAD_DESIGN.md](../../docs/THREAD_DESIGN.md) and [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md).
