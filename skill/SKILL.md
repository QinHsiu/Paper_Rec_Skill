---
name: paper-rec
version: 1.12.2
description: >-
  Retrieves and recommends academic papers via query rewriting, multi-source
  search, scoring, and structured reports. Activated by /query_english,
  /query_chinese, /query_other, or /wiki. Use when the user asks for paper
  recommendations, literature search, related work, OpenAlex/arXiv/HuggingFace/GitHub
  paper discovery, query改写/论文检索/论文推荐, wiki library status / start wiki UI,
  or research thread / 研究主线 association.
---

# Paper Recommendation Skill / 论文推荐技能

End-to-end workflow: **Input → Retrieval → Output**. Do not write application code unless the user explicitly requests implementation. Execute the workflow using web search, MCP tools, and the current model.

---

## Quick Start / 快速开始

```
Task Progress:
- [ ] Module 1: Input — summarize, extract keywords, rewrite query
- [ ] Module 1.5 (optional): Thread context inject — hypothesis / claims / gaps
- [ ] Module 2: Retrieval — search, score, rank top 50
- [ ] Module 2a/2b (optional): multi-path + iterative refine when thread/iterative
- [ ] Module 2.5 (optional): Thread-aware rerank + rationale section
- [ ] Module 3: Output — structured report (≤2 sentences per field)
- [ ] Module 4 (optional): Persist selected papers to Wiki (`content/wiki/pages`)
- [ ] Module 5 (`/wiki`): List library papers and/or launch Wiki UI / threads
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
| `/wiki` | Wiki ops | List library papers / start Wiki UI (language follows user) |

### Usage format / 使用格式

```
/query_english Find papers on efficient LLM fine-tuning for code generation
/query_chinese 帮我找多模态大模型对齐的最新论文
/query_other 最新の物体検出モデルに関する論文を探して
/wiki
/wiki 现在库里有哪些论文
/wiki start
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

- Retrieval against OpenAlex / arXiv / HF / GitHub / PwC always includes **English search terms** regardless of output mode (papers are mostly English).
- Do **not** mix languages within a single report section unless in `/query_other` with mixed input (then bilingual labels are allowed).
- Field constraint unchanged: **≤2 sentences per field** in the active output language.

Templates per mode: [output-template.md](output-template.md)

---

## Module 0: Clarify gate / 澄清门（可选）

**When**: Ambiguous ask, conflicting goals, or `rank-intent` returns `ambiguous=true`.

**Action**: Follow [`references/clarify-gate.md`](references/clarify-gate.md) — emit `need_clarification` JSON and **wait** before Module 1 rewrite / retrieval.

After clarify (or when clear): write a **research brief** then continue:

```powershell
python -m wiki_bridge.cli research-brief --topic "..." --must-answer "q1,q2" --out content/threads/<id>/research_brief.md
```

Module 1 rewrite + packs must stay inside the brief’s must-answer / out-of-scope.

Idea seeds (no finished paper yet): [`references/idea-template.md`](references/idea-template.md).  
Library search operators: [`references/wiki-query-filters.md`](references/wiki-query-filters.md) — parse via `wiki-filter-parse`.  
Screening stop: [`references/screening-stop.md`](references/screening-stop.md) — use `screen-next` after feedback.

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

**Rules**:
- Keep short domain abbreviations (**ML, AI, CV, RL, NLP, VLM, …**) — never drop tokens solely because `len ≤ 2` / `len ≤ 3`.
- **Exclude matching must be whole-word / whole-phrase** (conceptually `\b…\b` or exact phrase). Never use bare substring checks (`"climate" in "acclimating"`, `"mri" in "Amritsar"` → false rejects).
- Normalize consistently: strip trailing punctuation from tokens; keep a stable case policy (prefer lowercase for match keys; display may keep original).

**Purpose**: Improve retrieval granularity and recall across heterogeneous sources.

### 1.3 Rewrite Query / 改写 Query

**Action**: Combine summary + keywords into 2–4 retrieval queries:

| Query type | Purpose |
|------------|---------|
| **Broad** | High recall; domain + task |
| **Specific** | Method / architecture + application |
| **Keyword** | Exact-term match for APIs and site search |
| **Recent** | Add year filter terms if user wants latest work |

**Before searching**: run `rank-intent` (or equivalent) so journal-rank / language markers never pollute the topic string:

```powershell
python -m wiki_bridge.cli rank-intent --query "中科院一区 情绪调节"
# → cleaned_query: 情绪调节 · platform=cas · tiers=[1]
```

- Strip CAS/JCR/SJR/Q1/顶刊 into **Filters** (apply after retrieval if venue/ISSN known; never as search keywords).
- Strip 中文文献/英文文献/CSSCI into **language scope** (`en`/`zh`/`both`); ask once if bare Q1 without platform (`ambiguous=true`).
- Put partition intent into Filters / report header — not into OpenAlex/S2 query text.

**Output artifact** (show to user before retrieval; language follows active mode):

English mode:
```markdown
## Rewritten Queries
- Broad: ...
- Specific: ...
- Keywords: ...
- Filters: year range, venue preference
- Code: any | required | none (papers with GitHub/GitLab/HF links)
- Protocol (optional): inclusion / exclusion / negative keywords (audit trail; not a second planner)
```

Chinese mode:
```markdown
## 改写检索式
- 宽泛：...
- 精确：...
- 关键词：...
- 英文检索词（国际源）：...
- 筛选：年份范围、会议偏好
- 代码：any | required | none（需开源实现 / 仅理论）
- 协议（可选）：纳入/排除标准、负向词（可审计；不另起规划器）
```

### 1.5 Thread Context Inject / 研究主线注入（可选）

**When**: User prefixes `thread:<id>` in the query, or exactly **one** `status:active` thread exists under `content/threads/`, or user asks to use a research thread.

**Action**:
1. Load `content/threads/<id>/thread.json` (or `wiki_bridge thread-show --wiki-root . --id <id>`).
2. Inject into rewrite: `hypothesis`, open `claims`, `evidence_gaps`, `seed_queries` / `seed_terms`, plus titles/tags of up to 15 member `paper_paths` if readable.
3. Produce **extra** rewritten queries from open questions / gaps (one path per gap when useful).
4. Announce at report top: `Thread: {title} ({id})`.

**Seed-from-papers** (AI-Researcher): if user only provides a reference-paper list (no hypothesis), create thread with hypothesis = “Synthesize gaps from seed papers”, `paper_paths` = list, and derive `seed_queries` from titles — do not require an uploaded idea doc.

If multiple active threads and no `thread:` prefix → **ask** which thread to use (or proceed without thread context).

Design contract: `../docs/THREAD_DESIGN.md`.

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
| **A** | AI / CS core | **OpenAlex**, arXiv, HF Papers, PwC, GitHub, Semantic Scholar, DBLP, OpenReview, ACL, CVF |
| **A-CN** | CN LLM labs | DeepSeek, Qwen, THUDM, InternLM, BAAI, OpenBMB, Yi, Moonshot, Baichuan, Hunyuan, ByteDance, IDEA + Discovery indexes |
| **B** | AI industry & trends | Global labs + CN industry portals (通义/混元/豆包/盘古/文心/星火/商汤) |
| **C** | Math / Physics | arXiv categories, Science.gov, CERN CDS |
| **D** | Chemistry / Materials | DOAJ, SciELO, OSTI, ChemBlink*(metadata only)* |
| **E** | Engineering / Energy / Aero | NTRS, OSTI, Science.gov, NSTL |
| **F** | Biomed / Education | ERIC, PubMed-class portals, SciELO, DOAJ, Bioline |
| **H** | Open Access hubs | **OpenAlex** (`is_oa:true`), DOAJ, OALib, Socolar, SciELO, Cambridge Repo, NAP |
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
- **OpenAlex (default API lane for Pack A/H / general_oa)**: call `https://api.openalex.org/works?search=…` with `mailto=`; add `filter=publication_year:YYYY-YYYY` when latest-intent; fetch detail via `/works/W…`. Full recipes: [sources-reference.md § OpenAlex](sources-reference.md#openalex-api-recipes--openalex-检索配方必用).
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

### 2.3.5 Pre-ranking / 预重排（召回 → LLM 精排）

**When**: `/query_* auto`, Thread-conditioned retrieval, or merged candidate pool **> 30**. Default **on** for auto; user can say `prerank:off` / `不预排` to skip.

**Action** (after multi-source / multi-path merge, **before** full 2.3 LLM-style scoring):

0. **RRF fuse** (default **on** for auto / multi-path). Group candidates by `source` or `path_id`, then:

```bash
python -m wiki_bridge.cli rrf-fuse --json lanes.json --top-n 200 --out fused.json
```

   Report: `RRF: on/off · lane_hits={...}`. User can say `rrf:off`.

1. Cap working set at ≤200 unique candidates (post-RRF).
2. Run lightweight pre-rank:

```bash
python -m wiki_bridge.cli prerank --json fused.json --query "<rewritten>" --top-k 30 --out preranked.json
```

   Score ≈ BM25(title+abstract) + recency(≤3y boost) + optional log citation signal.
3. Keep **Top-30** for Module 2.3 / 2.5 fine scoring; list dropped count in Retrieval Trace.
4. Report header: `RRF: on/off` · `Prerank: on/off · kept N/M`.

**OA fulltext** (optional, after pick): Wiki「获取全文」or:

```bash
python -m wiki_bridge.cli pdf-fetch --wiki-root . --path <keyword/year/slug>
```

Legal chain only (arXiv → S2 OA → Unpaywall → PMC…). **No Sci-Hub.**

**Do not** crawl citation networks here (that is optional PageView「引用扩展」).

#### Recency scoring (0–10)

| Age vs anchor date | Default score | If query has 最新 / latest / recent / 今年 |
|--------------------|---------------|------------------------------------------|
| ≤ 3 months | 10 | 10 |
| ≤ 6 months | 9 | 10 |
| ≤ 12 months | 7 | 8 |
| ≤ 24 months | 5 | 4 |
| > 24 months | 2 | **1** (demote hard) |

**Anchor date**: use **today** by default; if the user names a historical window or `--date` / 指定日期, use that date (not wall-clock today) for age and for any history/dedupe windows. When calling `wiki_bridge` prerank, pass `now_year` aligned to the anchor.

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

1. Deduplicate by OpenAlex ID / title / arXiv ID / DOI / normalized model-version across sources (same key order as `wiki_bridge.rrf._doc_key`)
2. When merging duplicates across sources/lanes, **preserve lane tags** (e.g. `_lanes` / all `source` values) — do not let a higher score silently drop a lane-specific keep rule
3. Apply **latest-intent / family-version gate** (above) before sorting
4. Sort by final score descending; on ties, prefer **newer date**, then higher version number
5. Keep **top 50** unique papers
6. Ensure source diversity: if one source dominates (>70%), backfill from underrepresented sources
7. In the report header, state: `Latest-intent: on/off` and `Primary family versions considered: ...`

**Retrieval artifact** (internal; summarize for user):

```markdown
## Top 50 Candidate List
| Rank | Title | Date | Ver | Source | Sim | Rel | Imp | Rec | Final | Link |
|------|-------|------|-----|--------|-----|-----|-----|-----|-------|------|
| 1 | ... | 2026-04 | 3.6 | arXiv/blog | 9 | 9 | 8 | 10 | 9.0 | ... |
```

For the final report, deep-read the **top 10–15** papers; use metadata-only for ranks 11–50 unless user requests full coverage.

### 2a Multi-path queries / 多路查询（Thread 或 iterative / auto 时）

**When**: Module 1.5 thread is active, **or** user says `iterative` / `迭代检索`, **or** `/query_* auto` / 「全自动检索」, **or** exactly one `status:active` thread exists (default **on** for that case).

**Default**: When a single active thread is injected via 1.5, enable **1** refine wave automatically. User can say `no-iterative` / `不迭代` to skip. Do **not** iterate on plain `/query_*` with zero thread context.

**`/query_* auto`**: Force Module 1.5 (ask/pick thread if needed) → 2a all paths → 2b one refine → **2.3.5 prerank** → 2.3/2.5 R → write Retrieval Trace / `query-trace`. One-shot end-to-end under Thread; **no** citation-network crawl.

**Action** (before / during 2.2):
1. Build **up to 4** query paths from rewritten + thread state:
   - **broad** — Module 1 Broad
   - **specific** — Module 1 Specific / Keyword
   - **gap** — one query per open `evidence_gaps` / open question (cap 2)
   - **claim** — paraphrase of open claims that need evidence (cap 2)
2. **OpenScholar-style fan-out** (optional): expand Keyword into **3–5 short comma-separated queries** (entities/methods only), search union, then RRF.
3. **gpt-researcher SERP-conditioned** (optional, after wave 0): rewrite 1–2 extra queries from **top-5 titles/abstracts already retrieved** (not from the raw ask alone).
4. **STORM unused-snippet gaps**: when ranking/drafting, prefer next questions from papers **retrieved but not cited** in the draft / ledger (advance coverage, avoid niche loops).
5. Search packs with these paths; tag each hit with `path_id`.
6. Merge & dedupe across paths (same rules as 2.4). Prerank uses **norm_cite** (citation / max_in_pool) by default.
7. After each wave, append a discovery snapshot `{papers_evaluated, highly_relevant_count}` and optionally:

```powershell
python -m wiki_bridge.cli discovery-curve --json snapshots.json
python -m wiki_bridge.cli reflect-search --json fused.json --query "<topic>" --since-year 2023
```

If `reflect-search.should_retry`, run **at most one** refine wave with `improved_queries` (Module 2b). Saturation warnings are **advisory only**.
8. Interactive screening after Top-N: `thread-feedback` accept|skip → `screen-next --strategy hybrid`.


### 2b Iterative refine / 自动收窄·放宽（有上限）

**When**: same as 2a. **Default max rounds = 1** refinement after the initial pass (total ≤ 2 search waves). Triggers: `thread:<id>`, explicit `iterative`, or single active thread (unless `no-iterative`).

**Action**:
1. After wave 0, if kept unique hits **&lt; 8** → widen (drop rare terms / add synonyms / sibling venues); if **&gt; 40** noisy → narrow (add claim/gap tokens, year filter).
2. Run **at most one** refine wave; stop early if already in [8, 40].
3. Record a **检索轨迹 / Retrieval trace** (round, queries, raw hits, kept). Prefer persist via:

```bash
python -m wiki_bridge.cli query-trace --wiki-root . --thread <id> --json trace.json
```

Or include `retrieval_trace: [...]` in the report JSON for Module 4 / sync-report.

Then continue to 2.4 ranking → 2.5 (if thread).

### 2.5 Thread-aware rerank / 主线关联重排（可选）

**When**: A research thread is active for this turn (see Module 1.5).

**Action** (after Top-N list exists):
1. For each candidate, estimate association **R** using thread `seed_terms` / claims / gaps / keywords (same weights as bridge MVP: term 0.30, claim 0.30, gap 0.20, member tags 0.15, keyword 0.05). Prefer calling scoring logic conceptually aligned with `wiki_bridge.thread_store.score_paper_against_thread`.
2. Attach **rationale** (hit terms, claim ids, gap refs). Do **not** silently add papers to the thread.
3. Add a report section **研究主线关联 / Thread relevance** listing strong (≥0.75), weak (0.45–0.75), and uncovered gaps.
4. When persisting (Module 4), pass `--thread <id>`; use `--auto-link` only if the user explicitly asks to auto-accept strong hits.

Default gate remains `suggested` (cognitive ledger), matching `docs/THREAD_DESIGN.md`.

When association maps to a **claim_id**, offer to create a **suggested evidence** stub (quote from abstract / core idea) via:

```bash
python -m wiki_bridge.cli thread-evidence-add \
  --wiki-root . --thread <id> --claim-id C1 \
  --path <paper_path> --quote "..." --stance supports --suggested
```

Or Wiki: open paper → select text →「挂到主线」.

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

## Module 4: Persist to Wiki / 写入阅读库（可选）

**When**: User asks to save reading records (`写入 Wiki` / `存阅读记录` / `sync to wiki`), or after a `/query_*` report when the user confirms persistence (recommended if they care about「一周推荐」).

**When not**: Do **not** auto-write every retrieval unless the user asks to save / sync / 写入周刊.

After a successful sync, **each paper** is stored as its own editable file:

`content/wiki/pages/<keyword>/<year>/<slug>/README.md`

(N papers from a `/query_*` → N README files). Papers listed in `content/wiki/deleted.json` are **skipped** on sync.

### Steps

1. Convert selected Top-N papers (default Top-5 or user picks) into wiki-bridge JSON (`papers: [...]`).
2. Run from workspace root (or ask the user to run):

```bash
python -m wiki_bridge.cli sync-report \
  --wiki-root . \
  --report /path/to/report.json \
  --query-id <slug> \
  --mode query_chinese \
  --mark-reading \
  --thread <thread_id>
```

Add `--auto-link` only when the user wants papers with R≥0.75 accepted into the thread membership list.

3. Confirm pages under `content/wiki/pages/<keyword>/<year>/<slug>.md`, plus `_meta/Reading_Index` and `_meta/Dashboard`.
4. Confirm **`content/wiki/pages/<keyword>/README.md`** lists this `/query_*` command (auto-updated by `wiki_bridge`).
5. Open the SPA at http://127.0.0.1:5173/ (API `:8787`).

Bridge package: `packages/wiki-bridge/` (`python -m wiki_bridge.cli`). Apps: `apps/wiki-api/`, `apps/wiki-web/`.

Language modes (`/query_*`) still apply to the chat report; Wiki pages may keep bilingual section headings.

When writing JSON for bridge, include: `title`, `score`, `summary` (or `core_idea`), `tags`, `keyword`, `arxiv`, `year`. Bridge sets `added_at` to today.

---

## Module 5: `/wiki` — Library status & launch UI / 阅读库查询与启动

**When**: User sends `/wiki`, or asks what is already in the reading library, or asks to open/start the Wiki UI (`启动 wiki` / `打开阅读库` / `start wiki`).

### Subcommands

| Input | Action |
|-------|--------|
| `/wiki` or `/wiki list` or「有哪些论文」 | List papers currently under `content/wiki/pages/` |
| `/wiki start` or「启动/打开 wiki」 | Start API + Web and open the browser |
| `/wiki week` | List **this ISO week** papers (same dedupe as SPA 一周推荐) |
| `/wiki thread` or `/wiki thread list` | List Cognitive Threads under `content/threads/` |
| `/wiki thread <id>` | Show hypothesis, claims, gaps, members, recent events |
| `/wiki thread create <title>` | Create thread via bridge (ask hypothesis/keywords if missing) |
| `/wiki thread delta [id]` | Run Watch/Delta (`auto`/`diff_brief`/`gap_focus`/`exp_bridge`) |
| `/wiki thread related-work [id]` | Write Related Work outline under `drafts/` |
| `/draft` or `/wiki thread draft [id]` | Multi-chapter Markdown paper draft pack (`drafts/paper_draft/`) |
| `/wiki pdf <path> --pdf file` | Ingest PDF/txt → `fulltext.md` beside paper |
| `/wiki claim-suggest <path> --thread id` | Suggested claims/evidences from fulltext |
| `/wiki bibtex [--thread id]` | Export BibTeX for paths / thread members |
| `/wiki ris [--thread id]` | Export RIS for Zotero/EndNote |
| `/wiki rank-intent` | Strip CAS/JCR/Q1/language markers → cleaned query |
| `/wiki verify-cites` | Citation integrity gate (arXiv/DOI/OpenAlex); drop hallucinated |
| `/wiki latex-export [--thread id]` | Markdown draft → Overleaf `latex/main.tex` pack |
| `/wiki filter-code` | Post-RRF code filter: `any` / `required` / `none` |
| `/wiki matrix` | Literature matrix JSON/MD table for related-work |
| `/wiki claim-ledger` | Draft claim→cite gate (MATERIAL GAP if uncited) |
| `/wiki answer-ground` | Expand `(E12)` → References; cannot-answer if no evidence |
| `/wiki gather-evidence` | Chunk docs, score relevance 0–10, keep above cutoff |
| `/wiki number-verify` | Draft/LaTeX floats must appear in exp metrics whitelist |
| `/wiki stats-rigor` | Results claims need ±/std/CI/seeds cues |
| `/wiki survey-draft` | Outline-merge + subsection RAG related-work draft |
| `/wiki novelty-check` | Idea novelty vs local corpus (+ optional OpenAlex) |
| `/wiki fig-review` | Figure/caption/ref consistency (heuristic) |
| `/wiki deep-research` | Learnings tree → follow-up queries (depth×breadth) |
| `/wiki research-session` | Deferred gather→write_report session (`research_id`) |
| `/wiki exp-reflect` | Outer-loop `findings.md` + research-state from exp dir |
| `/wiki repro-check` | Control/experimental design + double-exec gate |
| `/wiki exp-eval-hook` | Persist `/exp_eval` metrics then optional number-verify |
| `/wiki exp-tree` | Experiment tree show/add/buggy/ready |
| `/wiki posthoc-cite` | Bind uncited claim sentences to evidence pool |
| `/wiki research-brief` | Scope artifact before Module 1 |
| `/wiki screen-next` | Active screening next batch (TF-IDF hybrid AL) |
| `/wiki reflect-search` | Coverage issues → follow-up queries |
| `/wiki discovery-curve` | Advisory retrieval saturation |
| `/wiki cite-expand <path>` | 1-hop citation expand (S2/Crossref; no auto ingest) |
| `/wiki fetch-pdf <path>` | Legal OA PDF → fulltext.md |
| `/wiki feedback <thread> accept|skip|pin --path` | Weak feedback → events + seeds |

Writing checklist: [`references/writing-gates.md`](references/writing-gates.md) (contribution → Figure 1 → SEARCH→VERIFY cites).  
Draft review gate: [`references/neurips-review-gate.md`](references/neurips-review-gate.md) (AI-Scientist).

### Thread ops (do this yourself)

```powershell
cd packages/wiki-bridge
pip install -e .
python -m wiki_bridge.cli thread-list --wiki-root ../..
python -m wiki_bridge.cli thread-show --wiki-root ../.. --id <thread_id>
python -m wiki_bridge.cli thread-create --wiki-root ../.. --title "..." --hypothesis "..." --keywords "a,b"
python -m wiki_bridge.cli thread-delta --wiki-root ../.. --id <thread_id> --mode auto --print-md
python -m wiki_bridge.cli thread-graph --wiki-root ../.. --id <thread_id>
python -m wiki_bridge.cli related-work --wiki-root ../.. --thread <thread_id> --print-md
python -m wiki_bridge.cli paper-draft --wiki-root ../.. --thread <thread_id> --venue generic
python -m wiki_bridge.cli bibtex-export --wiki-root ../.. --thread <id> --out refs.bib
python -m wiki_bridge.cli ris-export --wiki-root ../.. --thread <id> --out refs.ris
python -m wiki_bridge.cli rank-intent --query "JCR Q1 retrieval augmented generation"
python -m wiki_bridge.cli citation-verify --bib refs.bib --write-filtered
python -m wiki_bridge.cli latex-export --wiki-root ../.. --thread <id> --venue neurips
python -m wiki_bridge.cli filter-code --json fused.json --mode required --out coded.json
python -m wiki_bridge.cli matrix-build --json coded.json --out matrix.json --md-out matrix.md
python -m wiki_bridge.cli claim-ledger --wiki-root ../.. --thread <id> --out claim_ledger.json --strict
python -m wiki_bridge.cli number-verify --wiki-root ../.. --thread <id> --exp-dir ../../content/exp/<exp> --strict
python -m wiki_bridge.cli posthoc-cite --wiki-root ../.. --thread <id> --evidences-json evs.json
python -m wiki_bridge.cli answer-ground --answer "Result holds (E1)." --evidences-json evs.json --relevance-cutoff 3.0
python -m wiki_bridge.cli gather-evidence --question "..." --documents docs.json --out evs.json
python -m wiki_bridge.cli stats-rigor --wiki-root ../.. --thread <id> --strict
python -m wiki_bridge.cli survey-draft --json papers.json --out related.md
python -m wiki_bridge.cli novelty-check --idea "..." --papers-json corpus.json
python -m wiki_bridge.cli fig-review --draft draft.md --strict
python -m wiki_bridge.cli deep-research --topic "..." --json papers.json
python -m wiki_bridge.cli research-session --wiki-root ../.. --action create --topic "..." --sources-json papers.json
python -m wiki_bridge.cli repro-check --exp-dir ../../content/exp/<exp> --init-design
python -m wiki_bridge.cli exp-reflect --exp-dir ../../content/exp/<exp>
python -m wiki_bridge.cli evidence-coverage --wiki-root ../.. --thread <thread_id>
python -m wiki_bridge.cli pdf-ingest --wiki-root ../.. --pdf sample.pdf --path llm/2025/foo
python -m wiki_bridge.cli claim-suggest --wiki-root ../.. --path llm/2025/foo --thread <id> --apply
python -m wiki_bridge.cli citation-expand --wiki-root ../.. --path llm/2025/foo --top-k 5
python -m wiki_bridge.cli pdf-fetch --wiki-root ../.. --path llm/2025/foo
python -m wiki_bridge.cli rrf-fuse --json lanes.json --out fused.json
python -m wiki_bridge.cli thread-feedback --wiki-root ../.. --thread <id> --action pin --path llm/2025/foo
python -m wiki_bridge.cli csl-json-export --wiki-root ../.. --thread <id> --out refs.json
python -m wiki_bridge.cli bibtex-export --wiki-root ../.. --thread <id> --out refs.bib
python -m wiki_bridge.cli thread-claim --wiki-root ../.. --id <thread_id>
python -m wiki_bridge.cli thread-claim --wiki-root ../.. --id <thread_id> --claim-id C1 --status supported --accept
```

SPA: http://127.0.0.1:5173/threads · API `/api/threads` · MCP: `docs/MCP.md` / `packages/thread-mcp` · configure: `paper-rec-configure` / `scripts/configure-mcp.ps1`.

### List papers (do this yourself)

1. Prefer running from workspace `Paper_Rec_Skill`:

```powershell
cd apps/wiki-api
python -c "from app.services.pages_index import list_all_papers; import json; print(json.dumps(list_all_papers(), ensure_ascii=False, indent=2))"
```

2. Or scan Markdown frontmatter under `content/wiki/pages/**/*.md` (skip paths with `_` segments).
3. Reply with a compact table: **title | keyword | score | rating | added_at | summary (≤1 sentence) | path**.
4. If empty, tell the user to run `/query_*` then Module 4 `sync-report`.

### One-click start Wiki UI

Run (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File apps/start-wiki.ps1
```

From repo root `Paper_Rec_Skill`. This opens two terminals (API `:8787`, Web `:5173`) and the browser at http://127.0.0.1:5173/ .

If ports are already in use, just open http://127.0.0.1:5173/ and confirm `/api/wiki/pages` is healthy.

### Notes

- `/wiki` does **not** run retrieval; use `/query_*` for new papers.
- After listing, offer Module 4 persist if the user wants chat results written into the library.

---

## Workflow Example / 工作流示例

See [examples.md](examples.md) for a full walkthrough.

**Minimal example**:

> User: "Find papers on efficient fine-tuning of LLMs for code generation"

1. **Input**: Summarize → keywords `[LoRA, QLoRA, parameter-efficient, code LLM]` → rewrite 3 queries
2. **Retrieval**: Search arXiv, HF Papers, PwC, GitHub → score 80 candidates → top 50
3. **Output**: Structured report for top 10, compact list for 11–50
4. **Persist** (optional): `sync-report` → `content/wiki/pages`

---

## Additional Resources / 附加资源

- Retrieval sources & CCF venues: [sources-reference.md](sources-reference.md)
- Output template: [output-template.md](output-template.md)
- Walkthrough examples: [examples.md](examples.md)
- Self-hosted Wiki + bridge: `../apps/wiki-api/`, `../apps/wiki-web/`, `../packages/wiki-bridge/`, `../content/`
- Workspace architecture: `../docs/ARCHITECTURE.md`
