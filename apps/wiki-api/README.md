# Paper_Rec Wiki API (FastAPI)

Self-hosted wiki backend per `projects/wiki.txt`.

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
| `/api/wiki` | pages CRUD, search, graph, upload |
| `/api/weekly` | weekly digests |
| `/api/ask` | local wiki Q&A |
| `/api/skills` | Paper_Rec skill metadata |
| `/api/auth` | login stub |
| `/uploads` | uploaded images |

Content root: `content/wiki/pages`, `content/weekly`, `content/uploads`.
