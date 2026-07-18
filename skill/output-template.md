# Output Template / 输出模板

Copy and fill for each paper. **Each field: ≤2 sentences.** Choose the template block matching the active language mode.

---

## Mode Selection / 模式选择

| Active command | Use template section |
|----------------|---------------------|
| `/query_english` | [English Template](#english-template) |
| `/query_chinese` | [Chinese Template](#chinese-template) |
| `/query_other` | Detect input language → use English, Chinese, or Other template |

---

## English Template

### Single Paper Entry

```markdown
### [Rank N] {Paper Title}

**Meta**
- **Authors & Affiliation**: {authors} ({affiliations})
- **Date**: {YYYY-MM or YYYY}
- **Source**: {venue or platform} | [Link]({url})
- **Type**: {peer-reviewed / preprint / tech report}

**Core Idea**
{≤2 sentences}

**Contribution**
{≤2 sentences}

**Metrics**
{≤2 sentences; or "not reported"}

**Reference Value**
{≤2 sentences}

**Strengths**
{≤2 sentences}

**Weaknesses**
{≤2 sentences}
```

### Full Report Skeleton

```markdown
# Paper Recommendation Report

> Mode: English
> Query: "{original user query}"
> Date: {YYYY-MM-DD}

---

## 1. Query Summary

**Original intent**: {1 sentence}

**Rewritten queries**:
- Broad: ...
- Specific: ...
- Keywords: ...

---

## 2. Top Recommendations

{Repeat Single Paper Entry for ranks 1–10}

---

## 3. Extended List (Rank 11–50)

| Rank | Title | Team | Date | Source | Reason | Link |
|------|-------|------|------|--------|--------|------|
| 11 | ... | ... | ... | ... | ... | ... |

---

## 4. Search Coverage

| Source | Queried | Raw hits | After dedup |
|--------|---------|----------|-------------|
| arXiv | ✓ | | |
| Hugging Face | ✓ | | |
| GitHub | ✓ | | |
| Papers With Code | ✓ | | |
| CCF / conferences | ✓ | | |
| Supplementary | ✓ | | |
| **Total unique** | | | **≤50** |

---

## 4b. Retrieval Trace（iterative / thread 时）

| Round | Path | Query | Raw hits | Kept |
|-------|------|-------|----------|------|
| 0 | broad | ... | | |
| 0 | gap | ... | | |
| 1 | refine | ... | | |

`Latest-intent: on/off` · `Iterative: on/off` · `Thread: {id or —}`

---

## 4c. Thread relevance（主线激活时）

| Band | Papers |
|------|--------|
| Strong (R≥0.75) | ... |
| Weak (0.45–0.75) | ... |
| Uncovered gaps | ... |

---

## 5. Notes

- {gaps, inaccessible papers, follow-up suggestions}
```

---

## Chinese Template

### 单篇论文条目

```markdown
### [排名 N] {论文题目}（{English Title}）

**发表信息**
- **发表团队**: {authors}（{affiliations}）
- **发表时间**: {YYYY-MM 或 YYYY}
- **发表来源**: {venue or platform} | [链接]({url})
- **类型**: {正式发表 / 预印本 / 技术报告}

**核心观点**
{≤2 句话}

**核心贡献**
{≤2 句话}

**指标**
{≤2 句话；或「未公开」}

**参考价值**
{≤2 句话}

**强项**
{≤2 句话}

**不足之处**
{≤2 句话}
```

### 完整报告骨架

```markdown
# 论文推荐报告

> 模式：中文
> 检索主题：「{用户原始 query}」
> 日期：{YYYY-MM-DD}

---

## 1. 检索摘要

**原始意图**：{1 句话}

**改写检索式**：
- 宽泛：...
- 精确：...
- 关键词：...
- 英文检索词（国际源）：...

---

## 2. 重点推荐

{对排名 1–10 重复单篇论文条目}

---

## 3. 扩展列表（排名 11–50）

| 排名 | 题目 | 团队 | 时间 | 来源 | 推荐理由 | 链接 |
|------|------|------|------|------|----------|------|
| 11 | ... | ... | ... | ... | ... | ... |

---

## 4. 检索覆盖

| 来源 | 已检索 | 原始命中 | 去重后 |
|------|--------|----------|--------|
| arXiv | ✓ | | |
| Hugging Face | ✓ | | |
| GitHub | ✓ | | |
| Papers With Code | ✓ | | |
| CCF / 顶会 | ✓ | | |
| 补充来源 | ✓ | | |
| **去重总计** | | | **≤50** |

---

## 5. 备注

- {缺失信息、无法访问的论文、后续检索建议}
```

---

## Other-Language Template (Adaptive)

Use when `/query_other` detects a non-CN, non-EN language. Replace `{Lang}` with detected language (e.g., Japanese).

```markdown
# {Lang} Paper Recommendation Report / 論文推薦レポート

> Mode: Adaptive → {Lang}
> Query: "{original user query}"
> Date: {YYYY-MM-DD}

---

## 1. Query Summary / 検索概要

{≤2 sentences in {Lang}}

**English retrieval terms** (for international sources):
- Broad: ...
- Specific: ...
- Keywords: ...

---

## 2. Top Recommendations / おすすめ論文

### [Rank N] {Paper Title}

**Meta**
- **Authors**: ...
- **Date**: ...
- **Source**: ... | [Link](...)

**Summary** ({Lang}, ≤2 sentences)
**Contribution** ({Lang}, ≤2 sentences)
**Metrics** (≤2 sentences or "not reported")
**Reference Value** ({Lang}, ≤2 sentences)
**Strengths** ({Lang}, ≤2 sentences)
**Weaknesses** ({Lang}, ≤2 sentences)

---

## 3. Extended List (Rank 11–50)

| Rank | Title | Team | Date | Source | Reason ({Lang}) | Link |

---

## 4. Search Coverage

{Same table as English template}

---

## 4b. Retrieval Trace / 检索轨迹（iterative / thread）

{Same table as English template}

---

## 4c. Thread relevance / 主线关联

{Same as English template}

---

## 5. Notes

{In {Lang}, ≤2 sentences}
```

---

## Compact Entry (Rank 11–50) / 紧凑条目

**English**: `| {rank} | {title} | {author et al.} | {year} | {source} | {≤1 sentence} | [link]({url}) |`

**Chinese**: `| {排名} | {题目} | {作者等} | {年份} | {来源} | {≤1 句话} | [链接]({url}) |`

---

## Field Writing Guide / 字段写作指南

| Field | Do | Don't |
|-------|-----|-------|
| Core Idea | State problem + approach | Copy abstract verbatim |
| Contribution | Name 1–2 concrete novelties | List every minor ablation |
| Metrics | Quote key numbers with dataset | Invent numbers |
| Reference Value | Tie to user's query | Generic praise |
| Strengths | Evidence-based | Empty praise |
| Weaknesses | Fair gaps | Harsh criticism |
