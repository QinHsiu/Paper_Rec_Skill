<div align="center">

# Paper_Rec

### A Research Operating System for Literature & Experiments  
### 面向科研闭环的文献检索 · 阅读 Wiki · 实验沙箱 · 研究主线

<br/>

[![Workspace](https://img.shields.io/badge/workspace-v2.21.0-0F766E?style=for-the-badge&labelColor=1A2332)](VERSION)
[![paper-rec](https://img.shields.io/badge/paper--rec-v1.11.0-1A2332?style=for-the-badge)](skill/VERSION)
[![exp-sandbox](https://img.shields.io/badge/exp--sandbox-v1.8.0-0F766E?style=for-the-badge&labelColor=1A2332)](skill-exp/VERSION)
[![plot-draw](https://img.shields.io/badge/plot--draw-v1.2.0-1f5c55?style=for-the-badge&labelColor=1A2332)](skill-draw/VERSION)
[![MCP](https://img.shields.io/badge/MCP-Thread%20Memory-0F766E?style=for-the-badge&labelColor=1A2332)](docs/MCP.md)
[![License](https://img.shields.io/badge/license-MIT-5C6B7A?style=for-the-badge&labelColor=1A2332)](LICENSE)

<br/>

**Discover · Annotate · Experiment · Remember**

从自然语言问题出发，完成多源文献检索与结构化报告；  
在自研 Wiki 中阅读、标注与沉淀；  
用**研究主线**（Cognitive Thread）串联假设 / 证据缺口 / 实验；  
用实验沙箱做方案验证与训练闭环，并把指标与曲线写回知识库。

<br/>

`Claude Code` · `Codex` · `OpenClaw` · `MCP` · 及其他可加载 Markdown Skill 的 Agent 运行时

<br/>

[快速开始](#快速开始) ·
[闭环](#研究闭环) ·
[能力](#核心能力) ·
[命令](#slash-commands) ·
[架构](#架构一览) ·
[文档](#文档地图) ·
[贡献](#贡献)

</div>

---

## 研究闭环

把「找论文 → 挂主线 → 读论文 → 做实验 → 记结果」收成一条可复现管线：

```mermaid
flowchart LR
  A["/query_*<br/>多源检索"] --> T["Thread<br/>关联提醒"]
  T --> B["sync-report --thread<br/>入库 Wiki"]
  B --> C["人工阅读<br/>标记 / 笔记"]
  C --> D["/exp_*<br/>分析 · 方案 · 训练"]
  D --> G["/draw venue<br/>论文级图表"]
  D --> E["sync-exp --thread<br/>指标 · 曲线回写"]
  G --> E
  E --> F["Wiki 实验 · 主线<br/>可追溯产物"]
```

| Stage | What happens |
|:------|:-------------|
| **Retrieve** | Query 改写 → 多源召回 → 打分排序 → 结构化报告 |
| **Thread** | 假设 / claims / gaps；Thread-conditioned 关联度 R + ledger gate |
| **Curate** | 每篇独立 `README.md` · 评分/状态 · 知识图谱（含主线/实验节点） |
| **Experiment** | Badcase 聚类 → 多方案 Predict-then-Verify → 小规模验证 → 训练/评估 |
| **Persist** | Loss / 指标曲线与 `paper_refs` 同步至 Wiki「实验」，可挂主线 |

---

## 核心能力

<table>
<tr>
<td width="25%" valign="top">

### Literature Skill
**paper-rec**

- `/query_english` · `/query_chinese` · `/query_other`
- Module 1.5 / 2.5 主线注入与重排
- arXiv · HF · GitHub · PwC · CCF…
- Top-50 结构化字段报告

[skill/README.md](skill/README.md)

</td>
<td width="25%" valign="top">

### Experiment + Draw
**exp-sandbox** · **plot-draw**

- `/exp_*` 沙箱闭环 · `/draw` 出图
- venue 预设：cvpr / icml / neurips / acl / nature
- 学术配色 · PDF/PNG · `figures/`

[skill-exp](skill-exp/README.md) · [skill-draw](skill-draw/README.md)

</td>
<td width="25%" valign="top">

### Cognitive Thread
**研究主线**

- 假设 · claims · evidence gaps
- Watch / Delta · claim 闸门
- Wiki `/threads` · 图谱节点
- Thread Memory **MCP**

[docs/THREAD_DESIGN.md](docs/THREAD_DESIGN.md) · [docs/MCP.md](docs/MCP.md)

</td>
<td width="25%" valign="top">

### Reading Lab
**Self-hosted Wiki**

- FastAPI + Vue3 · Git Markdown
- 论文库 · **研究主线** · 实验 · 图谱
- 交互式曲线（Chart.js）

[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

</td>
</tr>
</table>

---

## Slash Commands

### paper-rec

| Command | Role |
|:--------|:-----|
| `/query_english` | 全英文报告 |
| `/query_chinese` | 全中文报告 |
| `/query_other` | 随输入语言自适应 |
| `/wiki` · `/wiki week` · `/wiki start` | 库内列表 / 本周 / 启动 UI |
| `/wiki thread` · `/wiki thread <id>` · `/wiki thread delta` | 研究主线列表 / 详情 / Delta |

Query 可加前缀：`thread:<id> ...`

### exp-sandbox

| Command | Role |
|:--------|:-----|
| `/exp_analysis` [`train`\|`eval`] | 训练/测试集与 badcase 分析（含 `/draw` 出图） |
| `/exp_training` | 训练监控；曲线按 `/draw` 规范导出 |
| `/exp_eval` | 指标对照 `target_score` + 对比图 |
| `/exp_loop` | 分析 → 方案 → 清洗验证 → 训练 → 评估 → 迭代 |

### plot-draw

| Command | Role |
|:--------|:-----|
| `/draw` [`chart_id?`] | 数据路径 + 描述 → 自动/指定图表（PDF+PNG） |
| `venue:` / `--venue` | `cvpr` · `icml` · `neurips` · `acl` · `nature` |

---

## 快速开始

### ① 一键安装（推荐）

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-wiki.ps1
```

```bash
# macOS / Linux / Git Bash
chmod +x install.sh scripts/start-wiki.sh
./install.sh
./scripts/start-wiki.sh
```

可选：`pip install pymupdf`（PDF 上传/OA 拉取解析）。Unpaywall 礼貌池：`UNPAYWALL_EMAIL` 或 `OPENALEX_EMAIL`。

**Docker（可选）**：`docker compose up --build` → API `:8787` + Web `:5173`。

**MCP 一键配置**（默认 dry-run，加 `-Apply` 写入）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/configure-mcp.ps1
powershell -ExecutionPolicy Bypass -File scripts/configure-mcp.ps1 -Apply
# 或: paper-rec-configure --apply
```

详见 [`docs/MCP.md`](docs/MCP.md)。

### ② 安装 Skills（跨平台）

```bash
mkdir -p .agents/skills/paper-rec .agents/skills/exp-sandbox .agents/skills/plot-draw
cp -r skill/* .agents/skills/paper-rec/
cp -r skill-exp/* .agents/skills/exp-sandbox/
cp -r skill-draw/* .agents/skills/plot-draw/
```

```text
/query_chinese thread:mm-llm-alignment 多模态大模型对齐的最新进展
/wiki thread mm-llm-alignment
/draw
data: content/exp/demo-ocr-handwriting-v1/metrics/curves.json
desc: train_loss 与 val_F1 曲线
venue: cvpr
```

### ③ 启动 Wiki

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-wiki.ps1
```

| Service | Endpoint |
|:--------|:---------|
| Web | http://127.0.0.1:5173/ · [研究主线](http://127.0.0.1:5173/threads) · [实验](http://127.0.0.1:5173/experiments) |
| API | http://127.0.0.1:8787/api/health · `/api/threads` · `/api/exp` |

### ③ 主线 · 报告入库 · 实验回写

```bash
cd packages/wiki-bridge && pip install -e .

# 创建研究主线
python -m wiki_bridge.cli thread-create \
  --wiki-root ../.. \
  --title "多模态对齐" --id mm-llm-alignment \
  --hypothesis "..." --keywords "multimodal,alignment"

# 文献报告 → 论文库（并写入主线 ledger）
python -m wiki_bridge.cli sync-report \
  --wiki-root ../.. \
  --report ./examples/sample_report.json \
  --mode query_chinese --mark-reading \
  --thread mm-llm-alignment

# 实验结果 → content/exp + Wiki「实验」+ 挂主线
python -m wiki_bridge.cli sync-exp \
  --wiki-root ../.. \
  --report ./examples/sample_exp_report.json \
  --thread mm-llm-alignment

# Watch / Delta
python -m wiki_bridge.cli thread-delta --wiki-root ../.. --id mm-llm-alignment --mode auto
```

### ④ Thread Memory MCP（可选）

```bash
cd packages/thread-mcp && pip install -e .
# 一键写入客户端配置（推荐）
paper-rec-configure --apply
# 或见 docs/MCP.md · packages/thread-mcp/README.md
```

### ⑤ 回归自检

```bash
python scripts/regress_exp_wiki.py
```

---

## 架构一览

```text
Paper_Rec_Skill/
├── skill/                      # paper-rec · 文献检索 + Thread 钩子
├── skill-exp/                  # exp-sandbox · 实验沙箱 + reference/
├── skill-draw/                 # plot-draw · /draw + lib/venues.py
├── apps/
│   ├── wiki-api/               # FastAPI  :8787  (/api/threads · /api/exp)
│   ├── wiki-web/               # Vue3 SPA :5173  (/threads · /experiments)
│   └── start-wiki.ps1
├── packages/
│   ├── wiki-bridge/            # sync-report · sync-exp · thread-* · templates
│   ├── thread-mcp/             # Thread Memory MCP Server
│   └── thread-bot/             # 飞书 / Telegram / 企微 / QQ 对话网关
├── content/
│   ├── wiki/pages/             # <kw>/<year>/<slug>/README.md
│   ├── wiki/pages/_exp/        # 实验 Wiki 镜像
│   ├── threads/                # Cognitive Thread · thread.json + events + evidences
│   ├── thread-templates/       # 主线模板市场
│   ├── exp/                    # 实验产物 · metrics · curves · figures
│   ├── weekly/
│   └── uploads/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── THREAD_DESIGN.md
│   ├── BOTS.md
│   └── MCP.md
├── scripts/regress_exp_wiki.py
├── VERSION
└── CHANGELOG.md
```

| Layer | Owns |
|:------|:-----|
| **skill/** | 检索流水线、主线注入/重排、`/wiki thread*` |
| **skill-exp/** | 实验闭环；`sync-exp --thread` |
| **skill-draw/** | `/draw` + venue 顶会风格 |
| **wiki-api / wiki-web** | 阅读、主线、实验看板、图谱 |
| **wiki-bridge** | 结构化报告 ↔ Git Markdown / Threads |
| **thread-mcp** | MCP 暴露主线记忆工具 |
| **thread-bot** | 多渠道路对话 Bot（飞书/Telegram/企微/QQ） |
| **content/** | 唯一内容真源（可版本管理） |

---

## 设计原则

| Principle | Meaning |
|:----------|:--------|
| **Agent-native** | 以 Markdown Skill 驱动，不绑定单一 IDE |
| **Git as database** | 笔记、实验与主线即文件，可 diff、可备份 |
| **Cognitive before OS** | 护城河是研究主线记忆，而非全能发表流水线 |
| **Predict before burn** | 先多方案偏好排序与小规模验证，再全量训练 |
| **Human in the loop** | 自动关联默认 `suggested`；入库/claim 需 gate |

实验沙箱在方案排序思路上借鉴 [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute)（Predict-then-Verify）；详见 [skill-exp/README.md](skill-exp/README.md#acknowledgement--借鉴说明)。

---

## 文档地图

| Doc | Audience |
|:----|:---------|
| [skill/README.md](skill/README.md) | 文献 Skill 中英入口 |
| [skill-exp/README.md](skill-exp/README.md) | 实验 Skill · 借鉴说明 |
| [skill-draw/README.md](skill-draw/README.md) | `/draw` 出图 · venue 预设 |
| [packages/wiki-bridge/README.md](packages/wiki-bridge/README.md) | sync + thread CLI |
| [packages/thread-mcp/README.md](packages/thread-mcp/README.md) | MCP 安装与工具表 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 模块边界与数据约定 |
| [docs/THREAD_DESIGN.md](docs/THREAD_DESIGN.md) | Cognitive Thread v2 契约 |
| [docs/MCP.md](docs/MCP.md) | Thread Memory MCP |
| [docs/WEBHOOK.md](docs/WEBHOOK.md) | 可选 Delta webhook 推送 |
| [docs/BOTS.md](docs/BOTS.md) | 飞书 / Telegram / 企微 / QQ 对话 Bot |
| [benchmarks/thread-bench/README.md](benchmarks/thread-bench/README.md) | Thread-Bench（主线条件排序评测） |
| [docs/MCP_PUBLISH.md](docs/MCP_PUBLISH.md) | MCP 目录提交清单 |
| [docs/tutorials/thread-research-memory.md](docs/tutorials/thread-research-memory.md) | 用 Thread 管研究方向（案例） |
| [docs/GOOD_FIRST_ISSUES.md](docs/GOOD_FIRST_ISSUES.md) | 新手可领任务 |
| [docs/MIGRATION.md](docs/MIGRATION.md) | 路径迁移 |
| [CHANGELOG.md](CHANGELOG.md) | Workspace 版本历史 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 环境 · PR 清单 · Skill 改法 |

---

## 贡献

欢迎 Issue / PR。先读 [CONTRIBUTING.md](CONTRIBUTING.md)；新手任务见 [GOOD_FIRST_ISSUES.md](docs/GOOD_FIRST_ISSUES.md)。

设计讨论请用 [GitHub Discussions](https://github.com/QinHsiu/Paper_Rec_Skill/discussions)（若仓库尚未开启：Settings → Features → Discussions）。

案例教程：[用 Thread 管一个研究方向](docs/tutorials/thread-research-memory.md)。

---

<div align="center">

### Paper_Rec

*Retrieve with any agent. Read in your own wiki. Follow the thread until the metric moves.*

<br/>

<sub>MIT License · Built for researchers who close the loop.</sub>

</div>
