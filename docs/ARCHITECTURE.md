# Architecture / 架构

## Modules

```mermaid
flowchart TB
  subgraph agent [Agent Runtime]
    Skill[skill-paper-rec]
  end
  subgraph bridge [wiki-bridge]
    Conv[Page Conventions]
    Sync[Report to Wiki Sync]
    Stats[Stats Generator]
  end
  subgraph wiki [Self-hosted Wiki]
    API[wiki-api FastAPI :8787]
    Web[wiki-web Vue3 :5173]
    MD[content/wiki/pages Git Markdown]
  end
  User -->|query_commands| Skill
  Skill -->|structured report| Sync
  Sync --> Conv
  Sync --> MD
  Stats --> MD
  User --> Web
  Web --> API
  API --> MD
```

| Module | Path | Owns | Does not own |
|--------|------|------|--------------|
| **skill-paper-rec** | `skill/` | Query rewrite, retrieval, scoring, `/wiki` | Long-term notes UI |
| **wiki-api** | `apps/wiki-api/` | Markdown CRUD, search, graph, weekly, upload | Retrieval algorithms |
| **wiki-web** | `apps/wiki-web/` | Vue SPA | Persistence format |
| **wiki-bridge** | `packages/wiki-bridge/` | Page naming, report write, index/dashboard | Replacing Skill |
| **content** | `content/` | Git Markdown store | UI |

Skill runs on any agent that can load `skill/SKILL.md` (Claude Code, Codex, OpenClaw, etc.).

## Data conventions

| Path | Purpose |
|------|---------|
| `content/wiki/pages/<keyword>/<year>/<slug>/README.md` | One editable file per paper |
| `content/wiki/pages/<keyword>/README.md` | `/query_*` log for that keyword |
| `content/wiki/deleted.json` | Delete blacklist (sync skips these) |
| `content/wiki/pages/_meta/Reading_Index.md` | Auto index |
| `content/wiki/pages/_meta/Dashboard.md` | Auto stats |
| `content/weekly/` | Weekly digests (optional) |
| `content/uploads/` | Images / attachments |

## Runtime

1. **Retrieve**: Agent → `skill/SKILL.md` → Input → Retrieval → Output.
2. **Persist** (optional): `wiki_bridge` CLI → `content/wiki/pages/`.
3. **View**: `apps/start-wiki.ps1` or API `:8787` + Web `:5173`.
