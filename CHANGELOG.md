# Changelog

All notable changes to **Paper_Rec_Skill** follow [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

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
