---
name: paper-rec
version: 1.2.1
description: >-
  Retrieves and recommends academic papers via query rewriting, multi-source
  search, scoring, and structured reports. Activated by /query_english,
  /query_chinese, or /query_other. Use when the user asks for paper
  recommendations, literature search, related work, arXiv/HuggingFace/GitHub
  paper discovery, or query改写/论文检索/论文推荐.
---

# Paper Recommendation Skill / 论文推荐技能

End-to-end workflow: **Input → Retrieval → Output**. Do not write application code unless the user explicitly requests implementation. Execute the workflow using web search, MCP tools, and the current model.

---

## Quick Start / 快速开始

```
Task Progress:
- [ ] Module 1: Input — summarize, extract keywords, rewrite query
- [ ] Module 2: Retrieval — search, score, rank top 50
- [ ] Module 3: Output — structured report (≤2 sentences per field)
```

**Trigger**: User provides a research topic, question, or long description and wants relevant papers.

---

## Activation & Language Modes / 启用与语言模式

After installing this skill, the user **must** prefix the query with one of three commands to set the output language mode. The command applies to the **entire** workflow (Input → Retrieval → Output) for that turn.

| Command | Mode | Output language |
|---------|------|-----------------|
| `/query_english` | English | All headings, labels, summaries, and field content in **English** |
| `/query_chinese` | Chinese | All headings, labels, summaries, and field content in **Chinese** |
| `/query_other` | Adaptive | Detect input language and match output (see rules below) |

### Usage format / 使用格式

```
/query_english Find papers on efficient LLM fine-tuning for code generation
/query_chinese 帮我找多模态大模型对齐的最新论文
/query_other 最新の物体検出モデルに関する論文を探して
```

The slash command is stripped before processing; the remaining text is the research query.

### Mode persistence / 模式持久性

- Mode is set **per message** by the slash command on that message.
- If the user omits a command, **ask** which mode to use (`/query_english`, `/query_chinese`, or `/query_other`) before proceeding.
- If the user switches command in a follow-up, apply the new mode to that turn's output.

### `/query_english` — English mode

| Stage | Rule |
|-------|------|
| Input | Summary, keywords, rewritten queries — all in English |
| Retrieval | Search queries in English; internal ranking notes in English |
| Output | Report title, section headers, field labels, and all prose in English |
| Paper titles | Keep original English title as-is |
| Missing metrics | Use "not reported" |

### `/query_chinese` — Chinese mode

| Stage | Rule |
|-------|------|
| Input | 摘要、关键词、改写 query — 全部使用中文 |
| Retrieval | 检索式以中文为主；国际源（arXiv 等）附加英文关键词以保证召回 |
| Output | 报告标题、章节、字段标签、正文 — 全部使用中文 |
| Paper titles | 保留英文原标题，括号内附中文译名（如有） |
| Missing metrics | 使用「未公开」 |

### `/query_other` — Adaptive mode

1. **Detect** the dominant language of the query text (after stripping the command).
2. **Map** to output language:

| Detected input | Output behavior |
|----------------|-----------------|
| Predominantly Chinese (≥60% CJK chars or clearly Chinese prose) | Same as `/query_chinese` |
| Predominantly English | Same as `/query_english` |
| Mixed CN + EN | Use the language of the **main research question**; if unclear, use Chinese |
| Other language (JA, KO, FR, DE, …) | Headings + prose in **that language**; retrieval queries still include **English keywords** for international sources |

3. **Announce** detected mode once at report top: `Mode: Adaptive → {language}` / `模式：自适应 → {语言}`

### Cross-mode rules / 跨模式通用规则

- Retrieval against arXiv / HF / GitHub / PwC always includes **English search terms** regardless of output mode (papers are mostly English).
- Do **not** mix languages within a single report section unless in `/query_other` with mixed input (then bilingual labels are allowed).
- Field constraint unchanged: **≤2 sentences per field** in the active output language.

Templates per mode: [output-template.md](output-template.md)

---

## Module 1: Input / 输入模块

Transform the user's raw query into retrieval-ready form through three steps.

### 1.1 Summarize / 摘要

**When**: User input exceeds ~200 words, is multi-topic, or contains background noise.

**Action**: Produce a concise summary (100–300 words) capturing:
- Core research problem
- Target domain / subfield
- Constraints (method type, dataset, application, time range if stated)

**Purpose**: Feed retrieval with a focused semantic anchor instead of raw text.

### 1.2 Extract Keywords / 抽取关键词

**Action**: Derive 5–15 keywords/phrases covering:
- Domain terms (e.g., "vision transformer", "RLHF")
- Method names, model families, datasets
- Task types (classification, generation, detection, etc.)
- Synonyms and abbreviations (e.g., "ViT", "visual transformer")

**Format**:
```
Primary: [must-match terms]
Secondary: [nice-to-have terms]
Exclude: [terms to filter out, if any]
```

**Purpose**: Improve retrieval granularity and recall across heterogeneous sources.

### 1.3 Rewrite Query / 改写 Query

**Action**: Combine summary + keywords into 2–4 retrieval queries:

| Query type | Purpose |
|------------|---------|
| **Broad** | High recall; domain + task |
| **Specific** | Method / architecture + application |
| **Keyword** | Exact-term match for APIs and site search |
| **Recent** | Add year filter terms if user wants latest work |

**Output artifact** (show to user before retrieval; language follows active mode):

English mode:
```markdown
## Rewritten Queries
- Broad: ...
- Specific: ...
- Keywords: ...
- Filters: year range, venue preference
```

Chinese mode:
```markdown
## 改写检索式
- 宽泛：...
- 精确：...
- 关键词：...
- 英文检索词（国际源）：...
- 筛选：年份范围、会议偏好
```

---

## Module 2: Retrieval / 检索模块

Search across **domain-selected** sources, score candidates, and keep **top 50** overall.

Full pack tables & venue lists: [sources-reference.md](sources-reference.md)

### 2.0 Domain routing / 领域路由（先做）

1. From Module 1 summary + keywords, assign **1–2 Domain IDs**.
2. Load matching **Packs** (max 3 packs unless user asks for exhaustive search).
3. Announce once before searching:

```
Domain: {ai_cs | chemistry | humanities_ss | ...}
Packs: {A, B, H, ...}
```

| Domain ID | Typical query | Packs |
|-----------|---------------|-------|
| `ai_cs` | LLM / CV / NLP / RL | **A, B** (+ **A-CN** if CN LLM) |
| `cn_llm_survey` | 国产/中文大模型综述 | **A, A-CN, B** |
| `math_physics` | math, physics, hep | **A, C** |
| `chemistry` | chemistry, CAS, molecule | **D, H** |
| `materials` | materials, nano | **D, E, H** |
| `biomed` | medicine, PubMed, genome | **F, H, A** |
| `education` | pedagogy, curriculum | **F, H, I** |
| `humanities_ss` | 哲学/历史/法学/社科 | **I, H** |
| `economics` | econ, finance, marketing | **K, I, H** |
| `engineering_energy` | NASA, energy, aerospace | **E, N, H** |
| `patent_ip` | patent | **L** + parent domain |
| `thesis` | 硕博论文 | **M** + parent domain |
| `general_oa` / `cross_domain` | unclear / OA | **H, A, N** |

Named CN models (Qwen / DeepSeek / GLM / InternLM / 混元 / 豆包 …) → force 2–4 matching **A-CN** labs (see sources-reference.md).

### 2.1 Pack overview / 来源包一览

| Pack | Name | Core sources |
|------|------|--------------|
| **A** | AI / CS core | arXiv, HF Papers, PwC, GitHub, Semantic Scholar, DBLP, OpenReview, ACL, CVF |
| **A-CN** | CN LLM labs | DeepSeek, Qwen, THUDM, InternLM, BAAI, OpenBMB, Yi, Moonshot, Baichuan, Hunyuan, ByteDance, IDEA + Discovery indexes |
| **B** | AI industry & trends | Global labs + CN industry portals (通义/混元/豆包/盘古/文心/星火/商汤) |
| **C** | Math / Physics | arXiv categories, Science.gov, CERN CDS |
| **D** | Chemistry / Materials | DOAJ, SciELO, OSTI, ChemBlink*(metadata only)* |
| **E** | Engineering / Energy / Aero | NTRS, OSTI, Science.gov, NSTL |
| **F** | Biomed / Education | ERIC, PubMed-class portals, SciELO, DOAJ, Bioline |
| **H** | Open Access hubs | DOAJ, OALib, Socolar, SciELO, Cambridge Repo, NAP |
| **I** | Humanities / SS | NCPSSD, CSSCI, CNKI, Wanfang, JSTOR, NTU journals |
| **J** | Newspaper archives | 人民日报 / 光明日报 / 大公报 — **only for media history** |
| **K** | Business / Econ | EconLit, EBSCO-class, SSRN, ScholarVox |
| **L** | Patents | SooPAT |
| **M** | Theses | theses.fr, CALIS, UCDRS, CNKI/Wanfang degree DBs |
| **N** | CN sci-tech hubs | NSTL, CALIS, paper.edu.cn |

**Never use** shadow libraries / pirate ebook sites as retrieval sources (see Excluded list in sources-reference.md).

### 2.2 Search execution / 执行检索

- Search each **activated pack** with at least the **Specific** and **Keyword** queries from Module 1.
- Always attach **English terms** for international packs.
- If a pack source needs login (CNKI, JSTOR, Wanfang), still collect metadata/title when possible; mark `access: paywall`.

### 2.3 Scoring / 打分

Score each candidate on **four** dimensions (0–10 each):

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| **Similarity** | 30% | Semantic match to rewritten query / summary |
| **Relevance** | 30% | Task, method, domain, **and version/family alignment** with user intent |
| **Importance** | 20% | Venue tier, team reputation, code/data availability (**not** raw citation count as primary) |
| **Recency** | 20% | Publication / release date relative to query intent |

**Final score** = 0.30×Sim + 0.30×Rel + 0.20×Imp + 0.20×Recency

#### Recency scoring (0–10)

| Age vs today | Default score | If query has 最新 / latest / recent / 今年 |
|--------------|---------------|------------------------------------------|
| ≤ 3 months | 10 | 10 |
| ≤ 6 months | 9 | 10 |
| ≤ 12 months | 7 | 8 |
| ≤ 24 months | 5 | 4 |
| > 24 months | 2 | **1** (demote hard) |

#### Latest-intent hard rules（「最新」硬约束）

When Module 1 detects **latest intent** (最新 / latest / 近期 / 刚刚发布 / newest):

1. **Do not** let citation count or historical Importance outrank a newer same-family paper.
2. Within the same model family (e.g. Qwen2.5 vs Qwen3 vs Qwen3.5/3.6/3.7), keep the **highest version + newest date** in Top-3; older generations go to Extended List unless user asks for lineage comparison.
3. Search queries **must** include the newest known version tokens (e.g. `Qwen3.7 OR Qwen3.6 OR Qwen3.5 OR Qwen3`), not only the best-known older name (`Qwen2.5`).
4. If the newest release has **no arXiv tech report yet** (product blog / GitHub / ModelScope only), still rank it Top-N with `Type: official release note` and state that a formal TR may be pending — **do not** substitute an older TR as if it were the latest.
5. Citation-heavy older papers may appear only as **baseline / prior version** with explicit label, never as the answer to「最新」.

#### Importance signals (revised)

- Tier-1 venue → +2–3
- Industry / CN Tier-1 lab official release → +1–2
- Official code / HF / ModelScope weights → +1
- **Do not** add large boosts solely for high citation count when latest-intent is active

### 2.4 Ranking & Filtering / 排序

1. Deduplicate by title / arXiv ID / DOI / normalized model-version across sources
2. Apply **latest-intent / family-version gate** (above) before sorting
3. Sort by final score descending; on ties, prefer **newer date**, then higher version number
4. Keep **top 50** unique papers
5. Ensure source diversity: if one source dominates (>70%), backfill from underrepresented sources
6. In the report header, state: `Latest-intent: on/off` and `Primary family versions considered: ...`

**Retrieval artifact** (internal; summarize for user):

```markdown
## Top 50 Candidate List
| Rank | Title | Date | Ver | Source | Sim | Rel | Imp | Rec | Final | Link |
|------|-------|------|-----|--------|-----|-----|-----|-----|-------|------|
| 1 | ... | 2026-04 | 3.6 | arXiv/blog | 9 | 9 | 8 | 10 | 9.0 | ... |
```

For the final report, deep-read the **top 10–15** papers; use metadata-only for ranks 11–50 unless user requests full coverage.

---

## Module 3: Output / 输出模块

Produce a **structured report** for retrieved papers. Each sub-field: **maximum 2 sentences**. Avoid redundancy.

Template: [output-template.md](output-template.md)

### Required fields per paper / 每篇论文必填字段

| Field | 中文 | Content |
|-------|------|---------|
| Title | 论文题目 | Official title + optional Chinese translation |
| Meta | 发表团队 & 时间 & 来源 | Authors/affiliations, date, venue/source link |
| Core idea | 论文核心观点 | Main thesis in ≤2 sentences |
| Contribution | 论文核心贡献 | Key novelty in ≤2 sentences |
| Metrics | 论文的指标 | Key benchmark numbers in ≤2 sentences |
| Reference value | 参考价值 | Why read this paper in ≤2 sentences |
| Strengths | 强项 | Top advantages in ≤2 sentences |
| Weaknesses | 不足之处 | Limitations/gaps in ≤2 sentences |

### Report structure / 报告结构

Use the template matching the active language mode (see [output-template.md](output-template.md)):

- `/query_english` → English-only template
- `/query_chinese` → Chinese-only template
- `/query_other` → template matching detected language

### Quality rules / 质量规则

- Prefer primary sources (paper PDF, arXiv abstract, official project page) over secondary summaries
- State "未找到公开指标" / "metrics not reported" when benchmarks are absent
- Do not fabricate citation counts or numbers
- Flag preprints vs peer-reviewed
- If a paper is inaccessible, note it and use available metadata only

---

## Workflow Example / 工作流示例

See [examples.md](examples.md) for a full walkthrough.

**Minimal example**:

> User: "Find papers on efficient fine-tuning of LLMs for code generation"

1. **Input**: Summarize → keywords `[LoRA, QLoRA, parameter-efficient, code LLM]` → rewrite 3 queries
2. **Retrieval**: Search arXiv, HF Papers, PwC, GitHub → score 80 candidates → top 50
3. **Output**: Structured report for top 10, compact list for 11–50

---

## Additional Resources / 附加资源

- Retrieval sources & CCF venues: [sources-reference.md](sources-reference.md)
- Output template: [output-template.md](output-template.md)
- Walkthrough examples: [examples.md](examples.md)
