# Optimization Plan v5 — 深化记忆 · 降低门槛（校准 2.12.0）

**状态（2026-07-18）**：v5 **P0–P2 已实现于 2.14.0**（安装一键 · 证据置信度 · PDF 流水线 · query auto · 写作反哺 · MCP 工具扩展）。

---

## 0. 测评口径校准（避免被竞品叙事带偏）

| 报告批评 | 2.12.0 已有 | 仍成立？ | 校准结论 |
|----------|-------------|---------|----------|
| PDF 需人工确认 | `pdf-ingest` + `claim-suggest`（suggested） | **部分成立** | 缺 **上传即跑流水线**；**保留 suggested 门闩**（不做无人值守写 accepted） |
| 数据源少于 Anaxa/PaperSeek | Skill Pack A–N（含 S2/PubMed 类入口文档） | **弱成立** | 补 **显式 API/查询路由 + 文档表**；不追求「源数量 KPI」 |
| 写作只有大纲 | Related Work outline + BibTeX | **刻意边界** | 做 **证据反哺写作辅助**；**不做** LaTeX 成稿/审稿/海报视频 |
| 证据缺 confidence | stance + gate | **成立** | 加 `confidence` / 细化 `support_status`（与 stance 对齐） |
| 迭代需人工触发 | 单 active Thread 默认 1 轮；显式 `iterative` | **弱成立** | 加 **`/query_* auto`**（Thread 条件下一句话跑完 2a/2b） |
| MCP 单一 | thread-mcp + wiki/exp/hint | **口径偏了** | **扩工具面**（graph/bibtex/related-work）；**不**拆 6 个检索 MCP |
| 安装门槛高 | CONTRIBUTING 手工步骤 | **成立** | **P0：一键 install + 启动脚本**（高于再堆功能） |
| 多智能体无人值守 | Skill 单 Agent 工作流 | **不做对标** | 用 Skill 编排步骤代替 swarm-notes 产品形态 |

**战略原则（不变并写进本轮）**

1. 护城河 = **Cognitive Thread 记忆**，不是 Anaxa / ResearchStudio 发表流水线。  
2. 检索 = Skill + **组合 article-mcp**；MCP 主卖记忆与本地 Wiki/Exp。  
3. 自动化 = **流水线默认跑 + 写入一律 suggested**，人在回路确认。  
4. 安装体验是增长杠杆；在线 Demo / 全自动多智能体 Vault **非本轮 KPI**。

---

## 1. 总目标（2.13 → 2.14）

降低「装得起来」的摩擦；把 PDF→候选证据做成 **默认流水线**；证据模型对齐竞品粒度（confidence）；检索一句话可跑通 Thread 条件路径；写作停在「反哺」，不成稿。

成功标准：

1. `./install.sh` 或 `install.ps1` 后，5 分钟内 Wiki + Skill 路径可用（含依赖提示）。  
2. Wiki 上传 PDF → 自动 `fulltext.md` + suggested claims/evidences（无需另敲 CLI）。  
3. Evidence schema 含 `confidence`（0–1 或 low/med/high）与可读 `support_status`；UI/API 可读写。  
4. `/query_* auto` 或等价：一句话 +（隐式）Thread → 多路检索 + ≤1 refine + 轨迹入库。  
5. Skill 来源表明确标注 Semantic Scholar / OpenAlex / Crossref / PubMed 的调用方式（web/API/MCP 组合）。  
6. MCP 增加 `thread_graph` / `bibtex_export` / `related_work`（或等价）；市场清单可执行。  
7. 编辑论文页时可选「推荐证据」（基于 Thread claims/evidences）；**无** LaTeX 导出成稿。

---

## 2. 工作流优先级（相对报告的重排）

报告四方向：自动化 / 扩源+检索 / 写作深度 / 降门槛。校准后：

```text
P0  一键安装 + 启动（install.sh / install.ps1 + README 30 秒块）
P0  Evidence 粒度：confidence + support_status（模型/API/UI）
P1  PDF 上传即流水线（Wiki UI → ingest + claim-suggest，仍 suggested）
P1  `/query_* auto` Thread 端到端（非引用网络爬虫）
P1  数据源：Pack 路由补强 S2 / OpenAlex / Crossref / PubMed（文档+Skill）
P2  证据反哺写作（选段 → 推荐 claim/exp/figure）；章节提纲扩展（Method/Exp 框）
P2  MCP 工具扩展 + 按 MCP_PUBLISH 提交准备
—   全自动多智能体 Vault、LaTeX 成稿审稿、海报/视频、PaperSeek 引用网爬虫
```

---

## 3. P0a — 一键安装与启动（2.13.0）

| 交付 | 说明 |
|------|------|
| `install.sh` / `scripts/install.ps1` | venv 可选；`pip install -e` wiki-bridge + thread-mcp；`npm install` wiki-web；检查 Python/Node |
| `scripts/start-wiki.sh` / `.ps1` | 并行起 `uvicorn app:app :8787` + `npm run dev :5173` |
| README | 「30 秒」复制块 + 常见失败（端口占用、缺 pymupdf） |
| 可选 | `make wiki` / `npm run wiki` 包装 |

**不做**：托管在线 SaaS Demo（成本高）；npx 全球包（可作 P2.5）。

---

## 4. P0b — 证据置信度（2.13.0，与安装并行）

扩展 `evidences.jsonl`：

```json
{
  "evidence_id": "E1",
  "claim_id": "C1",
  "stance": "supports",
  "support_status": "supports",
  "confidence": 0.7,
  "gate": "suggested|accepted",
  "...": "既有字段"
}
```

- `support_status` ∈ `supports|refutes|related|insufficient`（默认镜像 stance）  
- `confidence`：启发式（来源章节 abstract/conclusion → 更高；Agent 可改）或用户滑条  
- Thread 证据面板 + PageView 挂接表单展示/编辑  
- MCP `thread_add_evidence` 增加可选参数  

---

## 5. P1a — PDF 流水线产品化（2.13.x / 2.14）

| 做 | 不做 |
|----|------|
| Wiki：上传 PDF → 选 paper path 或新建 → 自动 ingest + claim-suggest | 自动 `gate=accepted` |
| API：`POST /api/wiki/pages/{path}/ingest`（multipart） | swarm 多智能体常驻服务 |
| 批量：`pdf-ingest --apply-suggest --thread` 一键 | OCR 扫描件 SOTA |

依赖：`pymupdf` 写入 `requirements` / install 脚本可选组。

---

## 6. P1b — 检索「一句话自动」（2.14）

Skill：

- 触发：`/query_* auto` 或用户说「全自动检索」且存在 Thread（`thread:` 或唯一 active）。  
- 行为：强制 2a 多路 + 2b 一轮 + 2.5 R + 写 `retrieval_trace` / `query_iter`。  
- **不做**：自动扩展整棵引用网络、Google Scholar 爬虫。

数据源（Skill / `sources-reference.md`）：

| 源 | 动作 |
|----|------|
| Semantic Scholar | Pack A 查询模板 + 可选 API key 环境变量说明 |
| OpenAlex | 同上 |
| Crossref | DOI 补全 / BibTeX 增强 |
| PubMed | Pack F 强化，生物医学路由默认带上 |

KPI = Thread 相关率与可复现轨迹，不是源计数。

---

## 7. P2 — 写作辅助（非成稿）与 MCP

### 7.1 证据反哺

- 论文编辑页：选中段落 →「推荐支撑」→ 列 Thread 内 claim/evidence/exp figure。  
- 可选生成 `drafts/method_outline.md` / `experiments_outline.md`（框，非 LaTeX）。

### 7.2 MCP

| Tool | 作用 |
|------|------|
| `thread_graph` | 返回认知地图 JSON |
| `bibtex_export` | 路径或 thread 成员 |
| `related_work` | 触发生成提纲 |

继续 **一个** `paper-rec-threads` 入口；检索外置 article-mcp。按 `docs/MCP_PUBLISH.md` 准备提交材料。

---

## 8. 明确不做（本轮与中期）

| 项 | 原因 |
|----|------|
| LaTeX/PDF 成稿 · 审稿 · 打包 · 海报/视频/博客 | Anaxa / ResearchStudio 主场 |
| 无人值守写入 accepted / 多智能体 Vault 产品 | 污染认知账本；与「人在回路」冲突 |
| 自建通用搜索 MCP 套件（6 服） | 与 article-mcp 同质化 |
| PaperSeek 级引用网络爬虫 | 成本高、非记忆护城河 |

---

## 9. 里程碑

| 版本 | 范围 |
|------|------|
| **2.13.0** | P0 安装脚本 + Evidence confidence/support_status |
| **2.13.x** | P1a Wiki PDF 上传流水线 |
| **2.14.0** | P1b `/query_* auto` + 源路由补强；P2 写作反哺 + MCP 工具扩展 |

---

## 10. 风险

| 风险 | 缓解 |
|------|------|
| 「全自动」被理解成免审 | UI 文案强调 suggested；批量接受需二次确认 |
| 扩源变成维护地狱 | 只加查询模板与路由，不自建爬虫集群 |
| 写作滑向成稿 | 输出仅 Markdown outline + 推荐列表 |
| 安装脚本平台碎片 | 先 Win ps1 + Unix sh；CI 冒烟 `install --dry-run` |

---

## 11. 建议下一步

1. ~~确认 v5 / 开工 2.13–2.14~~ → **2.14.0 已交付 P0–P2**  
2. 可选：MCP 市场提交、npx 包装、平行坐标看板  
3. 仍拒绝：LaTeX 全链条、无人值守 accepted、自建检索 MCP 套件

相对报告原文：报告将自动化与写作成稿抬很高；本计划将 **安装门槛与证据粒度** 提为双 P0，写作/多智能体大幅缩范围，以保住 Cognitive Thread 差异化。
