# Changelog

All notable changes to the **Paper_Rec Workspace** follow [Semantic Versioning](https://semver.org/).

Skill-specific history: [`skill/CHANGELOG.md`](skill/CHANGELOG.md), [`skill-exp/CHANGELOG.md`](skill-exp/CHANGELOG.md).

---

## [2.5.0] — 2026-07-17

### Added

- Wiki **实验** module: `/api/exp`, SPA `/experiments`, nav entry
- `wiki_bridge sync-exp` — metrics + loss curves → `content/exp` + `pages/_exp`
- Sample `packages/wiki-bridge/examples/sample_exp_report.json`
- Regression: `scripts/regress_exp_wiki.py` (25 checks)

---

## [2.4.0] — 2026-07-17

### Added

- Experiment sandbox skill [`skill-exp/`](skill-exp/) (`exp-sandbox`; see skill CHANGELOG for 1.0.0 / 1.1.0)
- Commands: `/exp_analysis` (± train/eval), `/exp_training`, `/exp_eval`, `/exp_loop`
- Experiment logs path convention: `content/exp/<experiment_id>/`
- Agent reference stubs [`skill-exp/reference/`](skill-exp/reference/) (Predict-then-Verify style)
- Acknowledgement of Predict-then-Verify ideas from [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute)

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
