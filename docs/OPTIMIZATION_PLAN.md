# Optimization Plan v3 — 从「有」到「优」

依据 `projects/same.txt`（2026-07-18 测评）与当时 workspace **2.8.0** 校准后的落地计划。

**状态（2026-07-18）**：**2.9.0–2.10.1** 已覆盖 v3 的 P0–P4。  
**下一轮计划**：[`OPTIMIZATION_PLAN_v5.md`](OPTIMIZATION_PLAN_v5.md)（**2.14.0 已落地 P0–P2**）。

## 0. 测评口径校准（避免重复造已有能力）

| 测评批评 | 2.8.0 已有 | 仍成立的差距 |
|----------|------------|--------------|
| 主线像标签 | 有 hypothesis/claims/gaps + ledger + Delta | **无论断级 evidence 锚点**（paper 正文片段 ↔ claim ↔ exp metric） |
| MCP 仅声明 | 有 `packages/thread-mcp` + docs | **无 npx/pipx 一键**；无检索类 tools；接入摩擦大 |
| 检索不够智能 | Skill 多源 + Thread 1.5/2.5 | **无自动迭代 / 多路召回 / 预重排** 可执行模块 |
| 实验只是静态图 | Chart.js 曲线 + venue 出图 | **无多 run 对比、无实时 tail、无平行坐标等看板** |
| 社区弱 | MIT + README | 缺 CONTRIBUTING / Discussions 引导 / good-first-issue |

**原则**：继续不硬刚 Anaxa 成稿管线、不重做 article-mcp 检索壳；把深度压在 **Claim–Evidence Map** 与 **可安装 MCP**。

---

## 1. 总目标

把 Cognitive Thread 从「主线文件夹」升级为 **论断–证据地图（Claim–Evidence Map）**；把 MCP 从「能跑」升级为 **一键可装、可被任意客户端调用**；检索与实验看板补齐体验，但不以追平 PaperSeek/TensorBoard 为 KPI。

成功标准（验收）：

1. 在 Wiki 论文页可选中段落 → 挂到 Thread claim，并可选绑 `exp_id` + `metric_key`  
2. Thread 详情页可视化：假设 → claims → evidences → papers/exps 边  
3. `pipx run` / 文档中的一键 MCP 配置可在 Cursor/Claude Desktop 5 分钟内跑通  
4. `/query_*` 支持可选「迭代检索」轮次（≥1 轮自动改写）并写入 ledger  
5. 实验页支持 ≥2 run 曲线叠加对比  

---

## 2. 工作流优先级

```text
P0  Claim–Evidence Map（认知壁垒）     ── 对标 Anaxa 深度，差异化核心
P1  MCP 一键化 + 能力面扩展             ── 对标 article-mcp 易用性
P2  检索 Agent（Thread-conditioned）   ── 借鉴 PaperSeek，但不做成独立搜索产品
P3  实验看板增强                         ── 在 Wiki 内做够用，不做完整 TB
P4  开源运营（文档/社群）                 ── 与功能并行，轻量持续
```

---

## 3. P0 — Claim–Evidence Map（深化研究主线）

### 3.1 数据模型

在 `content/threads/<id>/` 增加：

```text
evidences/
  <evidence_id>.json     # 或合并到 evidences.jsonl
```

单条 evidence schema：

```json
{
  "evidence_id": "E1",
  "claim_id": "C1",
  "kind": "quote|metric|figure|note",
  "paper_path": "llm/2025/foo",
  "quote": "选中的原文…",
  "quote_loc": {"section": "Method", "char_start": 120, "char_end": 200},
  "exp_id": null,
  "metric_key": null,
  "metric_value": null,
  "stance": "supports|refutes|related",
  "gate": "suggested|accepted",
  "created_at": "…"
}
```

`thread.json` 的 `claims[]` 增加：`evidence_ids[]`（或运行时聚合）。

### 3.2 API / Bridge / Skill

| 能力 | 接口 |
|------|------|
| 创建证据 | `POST /api/threads/{id}/evidences` |
| 接受/驳回 | `POST .../evidences/{eid}/gate` |
| 按 claim 列表 | `GET .../claims/{cid}/evidences` |
| CLI | `thread-evidence-add|list|accept` |
| Skill | 阅读时：用户高亮 → 写入 evidence；`/query` 报告可建议「可支持 C1」 |

### 3.3 Wiki UI

1. **PageView**：选中文本 →「挂到主线 claim」弹层（选 thread / claim / stance）  
2. **ThreadDetail**：Claim–Evidence 面板（树或简单图谱：claim 节点 ↔ evidence ↔ paper/exp）  
3. **GraphView**：可选边 `claim—evidence—paper`（Phase 内可先做 Thread 页内图，全局图第二步）

### 3.4 智能提醒（把 2.5 做实）

- `/query_*` 报告节：不仅给 R，还要 **映射到具体 claim_id**，并给出「建议创建 evidence（suggested）」  
- Delta：`gap_focus` 优先找能填缺口的论文，并预生成 evidence stubs（gate=suggested）

**不做什么**：自动从 PDF 全量抽取 claim（成本高、易错）；MVP 以人工高亮 + Agent 建议为主。

---

## 4. P1 — MCP 从「能跑」到「开箱」

### 4.1 打包与一键

1. 发布/本地：`pip install -e packages/thread-mcp` + console script（已有）  
2. 增加 **零 PYTHONPATH** 启动：server 内自动把 `wiki-bridge` 加入 path（相对包位置）  
3. 文档增加 Windows/macOS 两套 Cursor / Claude Desktop JSON（复制即用）  
4. 可选：`uvx` / `pipx` 说明；若要做 `npx` 需薄 Node wrapper（P1.5，非阻塞）

### 4.2 工具面扩展（仍不做「第二个 article-mcp」）

| 新增 tool | 作用 |
|-----------|------|
| `wiki_list_papers` / `wiki_get_page` | 读本地 Wiki |
| `exp_list` / `exp_get_metrics` | 读实验 |
| `thread_add_evidence` | P0 证据写入 |
| `thread_query_hint` | 返回改写 queries + seed（供客户端自行检索） |

检索执行：文档明确 **组合 article-mcp / Skill `/query_*`**；本 MCP 输出 `thread_query_hint` 即可。

### 4.3 README

- 徽章保持 `MCP · Thread Memory`  
- 首页 30 秒「复制配置」块  
- 对比表：vs article-mcp（我们 = 记忆；对方 = 检索）

---

## 5. P2 — 检索 Agent（Thread-conditioned）

落在 `skill/` + 可选 `packages/wiki-bridge` 辅助，**不新建独立 SaaS**。

### 5.1 流程

```text
Module 1.5 Thread inject
  → Module 2a 初始多路 query（broad / specific / gap / claim）
  → Module 2b 按命中量自动收窄/放宽（1–2 轮，有上限）
  → 多路候选合并去重
  → 轻量预重排（词袋 + claim 命中；可选 LLM 精排 Top-20）
  → Module 2.5 Thread R + claim 映射
```

### 5.2 产物

- 报告增加「检索轨迹」小节（可写入 `events.jsonl` kind=`query_iter`）  
- CLI 可选：`query-trace` 仅文档化；执行仍由 Agent 完成（与现 Skill 模式一致）

### 5.3 边界

不追求 PaperSeek 全源深度与引用网络爬虫；KPI = **在有 Thread 时相关率提升**，而非通用召回 SOTA。

---

## 6. P3 — 实验交互看板

基于现有 ExpDetail Chart.js：

| 项 | 说明 |
|----|------|
| 多 run 叠加 | 同 exp 多份 `curves*.json` 或对比另一 `exp_id` |
| 指标筛选 | 勾选 metric 系列显隐（已有图例，补「仅 primary」） |
| 简单平行坐标 | 多超参/多 seed 时（有 `metrics` 表才启用） |
| 准实时 | 可选 `?poll=5s` 刷新 `curves.json`（文件监视，非 TB 事件流） |

`/draw` venue：已有 5 套；P3 只补 **1–2 个缺的模板说明 + 示例**，不再扩大量预设。

---

## 7. P4 — 开源运营（轻量）

| 交付 | 说明 |
|------|------|
| `CONTRIBUTING.md` | 环境、skill 改法、PR 清单 |
| `GOOD_FIRST_ISSUES.md` 或 GitHub labels 说明 | 3–5 个可领任务（文案/venue/证据 UI） |
| Discussions 开启说明 | README 链到 Discussions |
| 案例教程 | 「用 Thread 管一个研究方向」1 篇（可用 mm-llm-alignment） |

---

## 8. 里程碑与版本建议

| 版本 | 范围 | 预估量级 |
|------|------|----------|
| **2.9.0** ✅ | P0 Claim–Evidence + P1 MCP 零 PYTHONPATH / wiki·exp·evidence | 已发布 |
| **2.10.0** ✅ | P2 迭代检索轨迹 + P3 多 run 对比 | 已发布 |
| **2.10.1** ✅ | P4 CONTRIBUTING + 案例 + good-first-issues | 已发布 |

---

## 9. 风险与决策

| 风险 | 缓解 |
|------|------|
| 做深 claim 滑向 Anaxa 全文审计 | 只做 Git 真源 + 人工/Agent 高亮，不做 citation audit/PDF gate |
| MCP 加上 search 同质化 | 只暴露 hint + 本地 wiki/exp/thread |
| 迭代检索烧 token | 默认 1 轮，需 `thread:` 或用户显式 `/query_* iterative` |

---

## 10. 建议的下一步动作

1. ~~P0–P4 / 2.9–2.10.1~~ → **已完成**  
2. 开启 GitHub Discussions；按 [`GOOD_FIRST_ISSUES.md`](GOOD_FIRST_ISSUES.md) 建 Issues 并打 `good first issue`  
3. 可选：平行坐标看板、更深迭代检索、更多案例线程
