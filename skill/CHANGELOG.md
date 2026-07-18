# Changelog

All notable changes to **Paper_Rec_Skill** follow [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

---

## [1.11.0] — 2026-07-18

### Added

- Thread-Bench ops; Delta `--notify` webhook (see `docs/WEBHOOK.md`)

---

## [1.10.0] — 2026-07-18

### Added

- Module 2.3.5: RRF fuse before prerank; `pdf-fetch` OA fulltext; report `RRF:` header
- `/wiki` feedback / csl-json / fetch-pdf ops

---

## [1.9.0] — 2026-07-18

### Added

- Module **2.3.5** prerank (BM25 + recency); `/query_* auto` includes prerank
- `/draft` · `/wiki thread draft` → multi-chapter Markdown paper draft pack
- `/wiki cite-expand`; evidence-coverage guidance

---

## [1.8.0] — 2026-07-18

### Added

- `/query_* auto` end-to-end Thread retrieval; scholarly API routing table (S2/OpenAlex/Crossref/PubMed)
- Writing assist hooks; evidence confidence guidance

---

## [1.7.0] — 2026-07-18

### Added

- Modules 2a/2b: default 1 refine wave when single active thread; `no-iterative` opt-out
- `/wiki` pdf / claim-suggest / related-work / bibtex / thread-graph ops

---

## [1.6.0] — 2026-07-18

### Added

- Modules **2a/2b**: Thread-conditioned multi-path queries + capped iterative refine; retrieval trace in output template
- Persist via `query-trace` / `retrieval_trace` → `query_iter` events

---

## [1.5.1] — 2026-07-18

### Added

- Module 2.5: suggest Claim–Evidence stubs (`thread-evidence-add` / Wiki「挂到主线」) when candidates map to `claim_id`

---

## [1.5.0] — 2026-07-18

### Added

- Cognitive Thread hooks: Module **1.5** (context inject) · Module **2.5** (thread-aware rerank + rationale)
- `/wiki thread` · `/wiki thread <id>` · `/wiki thread create`
- `sync-report --thread` / optional `--auto-link` guidance
- Contract: `../docs/THREAD_DESIGN.md`

---

## [1.4.0] — 2026-07-18

### Added

- Pack A sources: Connected Papers, AMiner, Google Scholar; JMLR / NeurIPS proceedings hubs
- Venue planning meta: CCF AI list, ccfddl, aideadlin.es, myhuiban（投稿档期，非正文检索）
- Pack M: DART-Europe theses portal
- Excluded: Sci-Hub, Scholar/PDF mirrors, SCIRP-as-sole-source (vetted from Awesome-Resources/Research)

## [1.3.0] — 2026-07-17

### Added

- **`/wiki`** command (Module 5): list library papers, this-week papers, one-click start Wiki UI (`apps/start-wiki.ps1`)
- Wiki library fields: `summary`, `score`, `added_at`, personal `rating`
- SPA: papers table with summary/scores/rating; keyword graph hover + click; weekly = this week's Skill papers (deduped)

---

## [1.2.1] — 2026-07-16

### Fixed

- Ranking under **最新 / latest** intent: citation-heavy older papers (e.g. Qwen2.5 TR) no longer outrank newer same-family releases (Qwen3 / 3.5 / 3.6 / 3.7)
- Split **Recency** out of Importance; new weights Sim 30 / Rel 30 / Imp 20 / Rec 20
- Added latest-intent hard rules + model-family version order; official blogs allowed when arXiv TR missing

---

## [1.2.0] — 2026-07-16

### Added

- **Pack A-CN**: Chinese LLM labs from awesome-LLMs-In-China
  - Discovery: awesome indexes, ModelScope, BAAI hub
  - Tier-1: DeepSeek, Qwen, THUDM, InternLM, BAAI, OpenBMB, Yi, Moonshot, Baichuan, Hunyuan, ByteDance, IDEA
  - Tier-2 + academic labs; named-model force triggers
- Domain `cn_llm_survey` routing
- CN industry portals under Pack B

### Changed

- `ai_cs` routing may attach A-CN when CN LLM keywords appear
- Importance scoring recognizes CN Tier-1 lab tech reports

---

## [1.1.0] — 2026-07-16

### Added

- Domain-aware retrieval routing (`Domain ID` → Pack A–N)
- Multi-field source packs: AI/CS, chemistry, materials, biomed, education, humanities/SS, economics, engineering/energy, patents, theses, OA hubs, CN sci-tech
- Explicit exclusion list (shadow libraries, pirate sites, bookmark hubs)
- Module-2 domain announcement checklist in `SKILL.md`

### Changed

- `sources-reference.md` restructured from flat AI-only list to pack-based taxonomy
- Retrieval module now activates ≤3 packs per query based on rewritten keywords

---

## [1.0.0] — 2026-07-15

### Added

- Core skill workflow: **Input → Retrieval → Output**
- Input module: summarize, keyword extraction, query rewriting
- Retrieval module: multi-source search, 3D scoring, Top-50 ranking
- Output module: structured report (≤2 sentences per field)
- Language modes: `/query_english`, `/query_chinese`, `/query_other`
- Reference docs: `sources-reference.md`, `output-template.md`, `examples.md`
- Bilingual documentation: `README.en.md`, `README.zh-CN.md`
- Version tracking: `VERSION`, `CHANGELOG.md`

### Sources

- Primary: arXiv, Hugging Face Papers, GitHub, Papers With Code, CCF venues
- Supplementary: industry labs, forums, domain influencers

---

## Version Policy / 版本策略

| Bump | When |
|------|------|
| **MAJOR** | Breaking changes to skill interface, command syntax, or report schema |
| **MINOR** | New sources, scoring rules, language modes, or templates |
| **PATCH** | Documentation fixes, typo corrections, minor wording improvements |

Current version is stored in [`VERSION`](VERSION).
