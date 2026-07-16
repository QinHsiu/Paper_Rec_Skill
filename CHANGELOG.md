# Changelog

All notable changes to the **Paper_Rec Workspace** follow [Semantic Versioning](https://semver.org/).

Skill-specific history remains in [`skill/CHANGELOG.md`](skill/CHANGELOG.md).

---

## [2.3.0] — 2026-07-17

### Added

- One paper = one directory `…/<slug>/README.md` (N query hits → N editable READMEs)
- Delete API + SPA button; blacklist `content/wiki/deleted.json` (sync skips deleted)

### Changed

- Paper path layout migrated from flat `slug.md` to `slug/README.md`

---

## [2.2.0] — 2026-07-17

### Removed

- `services/otter-wiki/` (entire Otter Wiki service, seed, app-data)
- Root `docker-compose.yml` (Otter image)
- Package name `otter_bridge` → renamed to `wiki_bridge`

### Changed

- Docs / Skill / README no longer reference Otter; bridge CLI is `python -m wiki_bridge.cli`

---

## [2.1.1] — 2026-07-17

### Added

- Papers list: summary, retrieval score, `added_at`, inline personal rating
- Graph: keyword-labeled nodes, hover keyword + added_at, click → page / Shift+click → edit
- Weekly: ISO-week Skill-synced papers with arXiv/title dedupe
- Skill `/wiki` + `apps/start-wiki.ps1` one-click launch

---

## [2.1.0] — 2026-07-17

### Added

- Self-hosted Wiki per `projects/wiki.txt`: `apps/wiki-api` (FastAPI) + `apps/wiki-web` (Vue3)
- Git Markdown store: `content/wiki/pages/<keyword>/<year>/`, `content/weekly/`, `content/uploads/`
- SPA: pages list, Markdown editor, search, graph, weekly, ask, skills

### Changed

- wiki-bridge writes to `content/wiki/pages`
- Skill Module 4 + ARCHITECTURE / root README point at the self-hosted stack

---

## Prior

See git history / older entries for 2.0.x Otter-based workspace (removed in 2.2.0). Skill history: [`skill/CHANGELOG.md`](skill/CHANGELOG.md).
