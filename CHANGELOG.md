# Changelog

All notable changes to **Paper_Rec_Skill** follow [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

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
