---
name: paper-rec
version: 1.0.0
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

Search across multiple sources, score candidates, and keep **top 50** overall.

### 2.1 Primary Sources / 主要来源

| Source | Search focus | URL pattern |
|--------|-------------|-------------|
| **arXiv** | Preprints, latest methods | arxiv.org |
| **Hugging Face Papers** | ML papers with community traction | huggingface.co/papers |
| **GitHub** | Implementations, trending repos | github.com search |
| **Papers With Code** | SOTA benchmarks, leaderboards | paperswithcode.com |
| **CCF venues** | Top Chinese-tier conferences | See [sources-reference.md](sources-reference.md) |

Search each source with at least the **Specific** and **Keyword** queries from Module 1.

### 2.2 Supplementary Sources / 补充来源

Use when primary sources yield <30 strong hits or domain is fast-moving:

- Major tech company official accounts / blogs (Google Research, Meta AI, Microsoft Research, OpenAI, DeepMind, etc.)
- Company research forum homepages
- Domain influencers' latest papers (e.g., CV → Kaiming He; NLP → follow field leaders the user names)
- Conference open-access proceedings pages (NeurIPS, ICML, ICLR, CVPR, ACL, etc.)

Details and venue lists: [sources-reference.md](sources-reference.md)

### 2.3 Scoring / 打分

Score each candidate on three dimensions (0–10 each):

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| **Similarity** | 35% | Semantic match to rewritten query / summary |
| **Relevance** | 35% | Task, method, and domain alignment with user intent |
| **Importance** | 30% | Venue tier, author/team reputation, citations/traction, recency, code/data availability |

**Importance signals** (non-exhaustive):
- Tier-1 venue (CCF-A, NeurIPS, ICML, ICLR, CVPR, ACL, etc.) → +2–3
- Industry lab or well-known research group → +1–2
- Recent (within user-specified or default 2 years) → +1
- Has official code / HF model / reproducible results → +1

**Final score** = 0.35×Similarity + 0.35×Relevance + 0.30×Importance

### 2.4 Ranking & Filtering / 排序

1. Deduplicate by title / arXiv ID / DOI across sources
2. Sort by final score descending
3. Keep **top 50** unique papers
4. Ensure source diversity: if one source dominates (>70%), backfill from underrepresented sources

**Retrieval artifact** (internal; summarize for user):

```markdown
## Top 50 Candidate List
| Rank | Title | Source | Sim | Rel | Imp | Final | Link |
|------|-------|--------|-----|-----|-----|-------|------|
| 1 | ... | arXiv | 9 | 9 | 8 | 8.7 | ... |
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
