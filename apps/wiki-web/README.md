# Paper_Rec Wiki Web (Vue 3)

Self-hosted SPA per `projects/wiki.txt`.

## Stack

- Vue 3 + Vue Router + Pinia
- Markdown: marked + DOMPurify
- Editor: CodeMirror 6 (Markdown) + live preview + image paste/upload
- Graph: Chart.js scatter (wikilink / tag graph)

## Dev

```bash
# terminal 1
cd apps/wiki-api && pip install -r requirements.txt && uvicorn app:app --reload --port 8787

# terminal 2
cd apps/wiki-web && npm install && npm run dev
```

Open http://127.0.0.1:5173/
