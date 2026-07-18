# Changelog

All notable changes to the **Paper_Rec Workspace** follow [Semantic Versioning](https://semver.org/).

Skill-specific history: [`skill/CHANGELOG.md`](skill/CHANGELOG.md), [`skill-exp/CHANGELOG.md`](skill-exp/CHANGELOG.md), [`skill-draw/CHANGELOG.md`](skill-draw/CHANGELOG.md).

---

## [2.12.0] — 2026-07-18

### Added

- **P0 Cognitive map**: `thread-graph` / `GET /api/threads/{id}/graph`; ThreadDetail interactive Claim–Evidence chart + day-grouped timeline
- **P1 PDF-lite**: `pdf-ingest`, `claim-suggest` (suggested only); sample extract under getting-started
- **P1 BibTeX**: `bibtex-export`, `GET /api/wiki/bibtex`, Page/Thread export buttons; [`docs/MCP_PUBLISH.md`](docs/MCP_PUBLISH.md)
- **P2 Related Work outline**: `related-work` → `drafts/related_work_outline.md` + API/UI
- **P3**: Skill default 1-round iterative when single active thread (`no-iterative` to skip)
- Plan: [`docs/OPTIMIZATION_PLAN_v4.md`](docs/OPTIMIZATION_PLAN_v4.md)

---

## [2.10.1] — 2026-07-18

### Added

- **P4 community**: [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/GOOD_FIRST_ISSUES.md`](docs/GOOD_FIRST_ISSUES.md), tutorial [`docs/tutorials/thread-research-memory.md`](docs/tutorials/thread-research-memory.md), root [`LICENSE`](LICENSE)
- README links to Discussions + contributing entry

---

## [2.10.0] — 2026-07-18

### Added

- **P2 Iterative retrieval**: Skill Modules 2a/2b; `query_iter` ledger; CLI `query-trace`; API `POST .../query-trace`; report `retrieval_trace` on sync-report
- **P3 Multi-run board**: `curve_runs` from `metrics/curves*.json`; ExpDetail run overlay / compare / primary-only / 5s poll; `curve_runs` in sync-exp writer
- Demo: `demo-ocr-handwriting-v1/metrics/curves_seed1.json`

---

## [2.9.0] — 2026-07-18

### Added

- **Claim–Evidence Map**: `evidences.jsonl`, CLI `thread-evidence-*`, API evidences / evidence-map / gate; Wiki PageView「挂到主线」+ ThreadDetail evidence panel
- **MCP UX**: zero-`PYTHONPATH` bootstrap via `PAPER_REC_ROOT`; tools `thread_add_evidence`, `thread_query_hint`, `wiki_list_papers`, `exp_list`, `exp_get_metrics`
- Docs: Phase E in [`THREAD_DESIGN.md`](docs/THREAD_DESIGN.md); status in [`OPTIMIZATION_PLAN.md`](docs/OPTIMIZATION_PLAN.md); refreshed [`MCP.md`](docs/MCP.md)

---

## [2.8.0] — 2026-07-18

### Added

- **Phase B**: Watch/Delta (`thread-delta`, `POST /api/threads/{id}/delta`, deltas/), claim suggest/accept gates, graph nodes for `thread` + `experiment`
- **Phase C**: Thread Memory MCP (`packages/thread-mcp`) + [`docs/MCP.md`](docs/MCP.md)
- **Phase D**: Wiki experiment Chart.js interactive curves/metrics; `/draw --venue` presets (cvpr/icml/neurips/acl/nature)

---

## [2.7.0] — 2026-07-18

### Added

- **Cognitive Thread v2** (`content/threads/`): hypothesis / claims / gaps + `events.jsonl` ledger
- Design contract: [`docs/THREAD_DESIGN.md`](docs/THREAD_DESIGN.md)
- `wiki_bridge` CLI: `thread-create|list|show|link-paper|link-exp`; `sync-report|sync-exp --thread` (+ optional `--auto-link`)
- Wiki API `/api/threads` + SPA `/threads` (list, detail, timeline)
- paper-rec Modules **1.5 / 2.5** and `/wiki thread*`; exp sync can attach to a thread

### Notes

- Auto-association defaults to `gate: suggested` (no silent membership pollution)
- Manuscript / citation-audit pipelines remain out of scope (complement Anaxa, do not compete)

---

## [2.6.0] — 2026-07-18

### Added

- Plot skill [`skill-draw/`](skill-draw/) (`plot-draw` v1.1.0) — `/draw` with self-contained [`lib/`](skill-draw/lib) (no external plot_demo)
- Exp sandbox (`exp-sandbox` v1.5.0): bundled symptom→action tricks; figures via `/draw`
- Wiki experiments: serve `figures/*.png` (`/api/exp/.../asset`), ExpDetailView chart section, sync-exp embeds images
- `/exp_analysis` · `/exp_training` · `/exp_eval` figure standard → `content/exp/<id>/figures/`

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
