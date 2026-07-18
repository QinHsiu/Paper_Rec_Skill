# Optimization Plan v4 — 认知地图加深（校准 2.10.1）

**状态（2026-07-18）**：v4 **P0–P3 已实现于 2.12.0**（认知地图 · PDF-lite · BibTeX · Related Work · 默认 iterative）。

前序 v3（Claim–Evidence / MCP / 迭代检索 / 多 run / CONTRIBUTING）已闭合，见 CHANGELOG 2.9–2.10.1。

---

## 0. 测评口径校准（避免重复造轮子 / 误伤定位）

| 报告批评 | 2.10.1 已有 | 仍成立？ | 校准结论 |
|----------|-------------|---------|----------|
| 图谱是「节点列表」 | `/graph` + thread/exp 节点；Thread 页有 evidence 列表 | **部分成立** | 缺 **claim–evidence–paper/exp 交互图** 与时间线；非缺「有没有图谱」 |
| 无 PDF 全文解析 | Claim–Evidence 靠高亮 + Agent suggest | **成立** | 要做 **轻量 PDF→章节 MD + 候选 claim/evidence（suggested）**，不做 GraphScholar 级审计库 |
| MCP 不如检索即服务 | thread-mcp 记忆 + query_hint + wiki/exp | **口径偏了** | **不新建 search-mcp 硬刚 article-mcp**；做 **统一入口包装 + 市场提交文档** |
| 数据源量级差距 | Skill 多 Pack（A–N）已覆盖主路径 | **弱成立** | 扩源是持续文案，**不以 15+/28 源为 KPI** |
| 迭代检索仍需人工触发 | 2a/2b + `query_iter`（需 `thread:` / `iterative`） | **部分成立** | 可加「活跃 Thread 默认 1 轮 refine」开关；**不做 PaperSeek 引用网络爬虫** |
| 无写作闭环 | 止于实验→图→Wiki | **刻意边界** | 只做 **BibTeX + Related Work 提纲**，不进入 Anaxa 成稿/评审 |

**战略原则（不变）**

1. 护城河 = **Cognitive Thread 记忆**（hypothesis / claim / evidence / gap / lit↔exp），不是全能发表流水线。  
2. 检索 = **Skill + 组合 article-mcp**；MCP 主卖记忆。  
3. PDF / 写作 = **反哺证据与提纲**，默认 `gate:suggested`，人在回路。

---

## 1. 总目标（2.11 → 2.12）

把已有的 Claim–Evidence **数据**升级为可探索的 **认知地图**；用轻量 PDF 解析 **喂候选** 而非替代人工判断；MCP 与导出降低接入摩擦；写作只做「证据反哺提纲」。

成功标准：

1. Thread 详情或 `/graph?thread=` 可见交互图：claim ↔ evidence ↔ paper/exp；可点选过滤。  
2. Thread 具备 **演进时间线**（claims/evidence/query_iter/delta 按时间）。  
3. 可选：本地 PDF → `content/wiki/...` 旁路 `fulltext.md` + 自动生成 **suggested** claims/evidences（用户确认）。  
4. 文档中有 **统一 MCP 入口** JSON；可选提交清单（Glama / MCP 目录）。  
5. Wiki 论文可选中导出 **BibTeX**；Thread 可生成 **Related Work 提纲**（Markdown，非 LaTeX 成稿）。

---

## 2. 工作流优先级（相对报告的重排）

报告建议双 P0（PDF + 图谱）+ MCP 拆分检索。校准后：

```text
P0  交互式 Claim–Evidence 图谱 + Thread 时间线     ← 报告「知识图谱」，用已有 evidences.jsonl
P1  轻量 PDF→章节 MD + 自动候选 claim/evidence    ← 报告「PDF」，缩范围、人在回路
P1  MCP 统一入口文档 + 市场提交说明（不新建搜索壳） ← 报告「MCP 生态」，改定位
P1  BibTeX 导出（Wiki 论文）                        ← 写作闭环的薄楔子
P2  Related Work 提纲（Thread→Markdown 框架）       ← 报告「写作」的可做子集
P3  活跃 Thread 默认 1 轮迭代 / 数据源文案补强       ← 体验，非战略主线
—   社区检测、引用网络爬虫、Anaxa 成稿/评审        ← 明确不做或远期
```

---

## 3. P0 — 交互式认知地图（2.11.0）

### 3.1 数据 → 图

从已有真源生成图模型（不必新存一份大 JSON，可运行时聚合）：

| 节点 | 来源 |
|------|------|
| `thread` / `claim` / `evidence` / `paper` / `experiment` | `thread.json` + `evidences.jsonl` + paths |

| 边 | 含义 |
|----|------|
| claim–evidence | `claim_id` |
| evidence–paper / evidence–exp | `paper_path` / `exp_id` |
| thread–paper / thread–exp | membership |

API：`GET /api/threads/{id}/graph` → `{ nodes, edges }`  
可选：全局 `/api/wiki/graph` 增加 claim/evidence 边（第二步）。

### 3.2 Wiki UI

1. **ThreadDetail**：嵌入小型力导向 / 分层图（可用现有图谱栈或轻量 vis-network / cytoscape；优先复用 `GraphView` 组件能力）。  
2. **过滤**：按 claim、stance、gate。  
3. **时间线视图**：复用 `events.jsonl`，按日分组展示 `query_iter` / `evidence_added` / `delta` / `claim_update`（Related Work 叙事用）。

### 3.3 不做

- 社区检测 / Louvain（可进 GOOD_FIRST 或 2.12+）  
- 从 PDF 自动抽引用网络当图谱主边

---

## 4. P1a — 轻量 PDF 解析（2.12.0 主交付之一）

### 4.1 范围

| 做 | 不做 |
|----|------|
| `skill-pdf` 或 `wiki_bridge.pdf_ingest`：PDF → 分节 Markdown（title/abstract/method/experiments/conclusion 启发式） | 全库向量检索 SaaS |
| 写入 `content/wiki/pages/<path>/fulltext.md`（或 `assets/`） | 替代人工阅读 |
| Agent/CLI：从章节生成 **suggested** claims / evidence quotes | 自动 `accepted` |
| 与现有「挂到主线」合流：候选列表一键 accept | GraphScholar 级 chunk 图谱库 |

依赖建议：优先 `pymupdf` / 纯文本层；OCR 非 MVP。

### 4.2 接口

```text
python -m wiki_bridge.cli pdf-ingest --wiki-root . --pdf X.pdf --path llm/2025/foo
python -m wiki_bridge.cli claim-suggest --wiki-root . --thread <id> --path llm/2025/foo
```

Skill：阅读 PDF 后可 `/wiki pdf` 或文档约定触发。

---

## 5. P1b — MCP 与导出（并行、低风险）

### 5.1 MCP（不拆出第二个检索产品）

| 项 | 说明 |
|----|------|
| 统一入口文档 | README/`docs/MCP.md`：`paper-rec-threads` 单配置；明确「检索请配 article-mcp」 |
| 可选 meta tools | 已有 wiki/exp/hint；可补 `wiki_get_page`（若仍缺） |
| 市场 | `docs/MCP_PUBLISH.md`：Glama / 目录提交 checklist（元数据、截图、描述） |
| 不做 | 独立 `search-mcp` 与 article-mcp 抢场景 |

### 5.2 BibTeX

- 从论文 frontmatter / README 生成 `.bib` 条目  
- CLI：`bibtex-export --paths …`；Wiki 论文页「导出 BibTeX」按钮  
- 字段不足时占位 + 警告，不伪造 DOI

---

## 6. P2 — Related Work 提纲（非成稿）

输入：Thread claims / gaps / accepted evidences / member papers。  
输出：`content/threads/<id>/drafts/related_work_outline.md`（小节标题 + 每条下挂论文路径与一句 rationale）。  

Skill：`/wiki thread related-work`。  
**明确非目标**：LaTeX、citation audit、peer review、打包发布。

---

## 7. P3 — 体验打磨

| 项 | 说明 |
|----|------|
| 活跃 Thread 默认 iterative | Skill：若唯一 `status:active` thread，默认 1 轮 2b（可用 `no-iterative` 关闭） |
| 数据源 | `sources-reference.md` 按领域补 2–3 个高价值入口，不追求「28 源」数字 |
| 平行坐标 | 有表格型 metrics 再做（仍属实验看板尾巴） |

---

## 8. 里程碑与版本

| 版本 | 范围 |
|------|------|
| **2.11.0** | P0 认知地图：`/threads/{id}/graph` + Thread 内交互图 + 时间线增强 |
| **2.12.0** | P1a PDF ingest + claim/evidence 候选；P1b BibTeX + MCP 发布文档 |
| **2.12.x** | P2 Related Work 提纲；P3 默认 iterative 开关 |

---

## 9. 风险

| 风险 | 缓解 |
|------|------|
| PDF 解析质量差 → 脏 claim | 仅 `suggested`；UI 批量驳回；章节启发式保守 |
| 图谱做成「第二个 GraphView」却空 | 强制以 evidences 为边；无证据时引导挂接而非空力导向 |
| MCP 加上搜索同质化 | 文档与工具命名坚持 Memory；检索外置 |
| Related Work 滑向 Anaxa | 只输出 outline Markdown，无 PDF gate / 评审 |

---

## 10. 建议下一步

1. ~~确认 v4 P0 图谱~~ → **2.12.0 已交付 P0–P3**  
2. 可选：社区检测、pymupdf 正式依赖写入 requirements、Glama 提交  
3. 体验：平行坐标、更多案例线程

对比报告原文的差异（供决策）：报告将 PDF 与图谱并列为 P0，并将「拆分 search-mcp」作 P1；本计划将 **图谱提到唯一主 P0**（数据已具备），PDF 次之且缩范围，**拒绝新建检索 MCP**。
