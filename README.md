<div align="center">

# Paper_Rec

### A Research Operating System for Literature & Experiments  
### 面向科研闭环的文献检索 · 阅读 Wiki · 实验沙箱 · 研究主线 · 写作诚信闸门

<br/>

[![Workspace](https://img.shields.io/badge/workspace-v2.35.0-0F766E?style=for-the-badge&labelColor=1A2332)](VERSION)
[![paper-rec](https://img.shields.io/badge/paper--rec-v1.15.0-1A2332?style=for-the-badge)](skill/VERSION)
[![exp-sandbox](https://img.shields.io/badge/exp--sandbox-v1.10.0-0F766E?style=for-the-badge&labelColor=1A2332)](skill-exp/VERSION)
[![plot-draw](https://img.shields.io/badge/plot--draw-v1.2.1-1f5c55?style=for-the-badge&labelColor=1A2332)](skill-draw/VERSION)
[![MCP](https://img.shields.io/badge/MCP-Thread%20Memory-0F766E?style=for-the-badge&labelColor=1A2332)](docs/MCP.md)
[![License](https://img.shields.io/badge/license-MIT-5C6B7A?style=for-the-badge&labelColor=1A2332)](LICENSE)

<br/>

**Discover · Annotate · Experiment · Verify · Remember**

从自然语言问题出发，完成多源文献检索与结构化报告；  
在自研 Wiki 中阅读、标注与沉淀；  
用**研究主线**（Cognitive Thread）串联假设 / 证据缺口 / 实验；  
用实验沙箱做方案验证与训练闭环，并把指标与曲线写回知识库；  
在出稿前用**数值硬闸 / 引用 / 图审 / 综述审计**挡住幻觉结果。

<br/>

`Claude Code` · `Codex` · `OpenClaw` · `Cursor` · `MCP` · 及其他可加载 Markdown Skill 的 Agent 运行时

<br/>

[快速开始](#快速开始) ·
[闭环](#研究闭环) ·
[能力](#核心能力) ·
[命令](#slash-commands) ·
[诚信闸门](#写作与诚信闸门) ·
[架构](#架构一览) ·
[文档](#文档地图) ·
[贡献](#贡献)

</div>

---

## 研究闭环

把「找论文 → 挂主线 → 读论文 → 做实验 → 校核写作 → 记结果」收成一条可复现管线：

```mermaid
flowchart LR
  A["/query_*<br/>多源检索"] --> T["Thread<br/>关联 · brief"]
  T --> B["sync-report --thread<br/>入库 Wiki"]
  B --> C["阅读 · screen-next<br/>claim / evidence"]
  C --> D["/exp_* · exp-tree<br/>分析 · 训练 · 评估"]
  D --> G["/draw · fig-review<br/>论文级图表"]
  D --> V["number-verify<br/>hard-gate · stats"]
  G --> V
  V --> E["sync-exp · latex-export<br/>指标 · 草稿回写"]
  E --> F["Wiki · 主线<br/>可追溯产物"]
```

| Stage | What happens |
|:------|:-------------|
| **Retrieve** | Query 改写 → 多源召回 → prerank / RRF → 打分排序 → 结构化报告 |
| **Thread** | 假设 / claims / gaps；`research-brief`；Thread-conditioned 关联度 R + ledger gate |
| **Curate** | 每篇独立 `README.md` · 评分/状态 · `screen-next` 主动筛选 · 知识图谱 |
| **Experiment** | Badcase 聚类 → Predict-then-Verify → mini-verify → 训练/评估 → `exp-tree` / `repro-check` |
| **Verify** | `gather-evidence` → `answer-ground`；`number-verify --hard-gate`；`stats-rigor`；`fig-review`；`claim-ledger` |
| **Persist** | Loss / 指标 / `findings.md` 与 `paper_refs` 同步至 Wiki；可选 `latex-export --hard-gate` |

---

## 核心能力

<table>
<tr>
<td width="25%" valign="top">

### Literature Skill
**paper-rec · v1.15**

- `/query_english` · `/query_chinese` · `/query_other`
- Module 0 clarify · research-brief · 1.5 / 2.5 主线注入
- arXiv · OpenAlex · HF · GitHub · PwC · CCF…
- 覆盖反思 · 发现饱和 · 主动筛选 · 新颖性熔断

[skill/README.md](skill/README.md)

</td>
<td width="25%" valign="top">

### Experiment + Draw
**exp-sandbox · plot-draw**

- `/exp_*` 沙箱闭环 · `/draw` 出图
- `exp-eval-hook` · `exp-tree` · `exp-reflect`
- `repro-check` 双跑一致性
- venue：cvpr / icml / neurips / acl / nature

[skill-exp](skill-exp/README.md) · [skill-draw](skill-draw/README.md)

</td>
<td width="25%" valign="top">

### Cognitive Thread
**研究主线**

- 假设 · claims · evidence gaps
- Watch / Delta · claim 闸门
- Wiki `/threads` · 图谱节点
- Thread Memory **MCP** · `research-session`

[docs/THREAD_DESIGN.md](docs/THREAD_DESIGN.md) · [docs/MCP.md](docs/MCP.md)

</td>
<td width="25%" valign="top">

### Reading Lab + Integrity
**Wiki · writing gates**

- FastAPI + Vue3 · Git Markdown
- 数值硬闸 · 引用校验 · 图/综述审计
- 交互式曲线（Chart.js）

[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [writing-gates](skill/references/writing-gates.md)

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
| `/draft` · `/wiki thread draft` | 多章 Markdown 草稿包 |
| `/wiki` + bridge CLI | 见下「写作与诚信闸门」与 Skill 全表 |

Query 可加前缀：`thread:<id> ...`；全自动检索可用 `/query_* auto`。

### exp-sandbox

| Command | Role |
|:--------|:-----|
| `/exp_analysis` [`train`\|`eval`] | 训练/测试集与 badcase 分析（含 `/draw` 出图） |
| `/exp_training` | 训练监控；曲线按 `/draw` 规范导出 |
| `/exp_eval` | 指标对照 `target_score` + 对比图；写 `metrics/summary.json` |
| `/exp_loop` | 分析 → 方案 → 清洗验证 → 训练 → 评估 → 迭代（更新 `exp-tree`） |

配套 CLI：`exp-eval-hook` · `exp-tree` · `repro-check` · `exp-reflect`（经 `wiki_bridge`）。

### plot-draw

| Command | Role |
|:--------|:-----|
| `/draw` [`chart_id?`] | 数据路径 + 描述 → 自动/指定图表（PDF+PNG） |
| `venue:` / `--venue` | `cvpr` · `icml` · `neurips` · `acl` · `nature` |

出图后建议：`fig-review --draft ... --emit-vlm-prompts`（可选填入 VLM JSON）。

---

## 写作与诚信闸门

出稿 / 导出前建议按序跑（详见 [`skill/references/writing-gates.md`](skill/references/writing-gates.md)）：

```powershell
cd packages/wiki-bridge
pip install -e .

# 1) 实验数值登记 + Results 硬闸（空 registry 或未登记浮点 → BLOCK）
python -m wiki_bridge.cli number-verify `
  --wiki-root ../.. --thread <id> --exp-dir ../../content/exp/<exp> `
  --hard-gate --write-registry --strict

# 2) 统计表述（± / CI / seeds）
python -m wiki_bridge.cli stats-rigor --wiki-root ../.. --thread <id> --strict

# 3) 引用与 claim
python -m wiki_bridge.cli citation-verify --bib refs.bib --write-filtered
python -m wiki_bridge.cli claim-ledger --wiki-root ../.. --thread <id> --strict
python -m wiki_bridge.cli posthoc-cite --wiki-root ../.. --thread <id> --evidences-json evs.json

# 4) 图一致性（结构 + 离线语义；可选 --vlm-json）
python -m wiki_bridge.cli fig-review --draft draft.md --emit-vlm-prompts --strict

# 5) 综述草稿 + 引文审计
python -m wiki_bridge.cli survey-draft --json papers.json --topic "..." --out related.md --strict

# 6) 接地问答：先打分再展开引用；反馈后再检索
python -m wiki_bridge.cli gather-evidence --question "..." --documents docs.json --out evs.json
python -m wiki_bridge.cli answer-ground --answer "..." --evidences-json evs.json --relevance-cutoff 3.0
python -m wiki_bridge.cli feedback-edit --question "..." --answer-file ans.md `
  --evidences-json evs.json --candidates-json pool.json

# 7) 导出（可再绑硬闸）
python -m wiki_bridge.cli latex-export --wiki-root ../.. --thread <id> `
  --venue neurips --exp-dir ../../content/exp/<exp> --hard-gate
```

| Gate | CLI | Blocks when |
|:-----|:----|:------------|
| Results 硬闸 | `number-verify --hard-gate` | Results 浮点不在 `verified_registry` / registry 为空却有数值主张 |
| 统计严谨 | `stats-rigor` | 单点浮点主张缺少 ±/CI/seeds 等线索 |
| 引用诚信 | `citation-verify` · `claim-ledger` | 幻觉 BibTeX / 无 cite 的实质 claim |
| 图一致性 | `fig-review` | 缺 caption、孤儿引用、题文极性冲突（+ 可选 VLM） |
| 综述审计 | `survey-draft --strict` | 子节 cite 与摘要不支撑 |
| 接地问答 | `gather-evidence` · `answer-ground` · `feedback-edit` | 低相关 chunk / 无证据 / 需补检索 |

完整 `/wiki` 子命令表见 [`skill/SKILL.md`](skill/SKILL.md)。

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

### ④ 主线 · 报告入库 · 实验回写

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

# 评估指标落盘 → 可选 number-verify
python -m wiki_bridge.cli exp-eval-hook \
  --exp-dir ../../content/exp/<id> \
  --metrics-json eval_metrics.json \
  --target-metric F1 --target-threshold 0.85

# Watch / Delta
python -m wiki_bridge.cli thread-delta --wiki-root ../.. --id mm-llm-alignment --mode auto

# 主线模板市场
python -m wiki_bridge.cli thread-template-list --wiki-root ../.. --seed
python -m wiki_bridge.cli thread-template-import --wiki-root ../.. --template rag-evaluation
```

### ⑤ Thread Memory MCP（可选）

```bash
cd packages/thread-mcp && pip install -e .
# 一键写入客户端配置（推荐）
paper-rec-configure --apply
# 或见 docs/MCP.md · packages/thread-mcp/README.md
```

延迟调研会话（gather → 稍后 write_report）：

```powershell
python -m wiki_bridge.cli research-session --wiki-root ../.. --action create --topic "..." --sources-json papers.json
python -m wiki_bridge.cli research-session --wiki-root ../.. --action write-report --research-id <id>
```

### ⑥ 多渠道路 Bot（可选）

```powershell
pip install -e packages/thread-bot
$env:PAPER_REC_ROOT = (Resolve-Path .).Path
python -m thread_bot repl    # 本地对话
python -m thread_bot serve   # :8790 飞书/Telegram/企微/QQ
```

详见 [`docs/BOTS.md`](docs/BOTS.md)。

### ⑦ 回归自检

```bash
python scripts/regress_exp_wiki.py
cd packages/wiki-bridge && python -m pytest tests -q
```

---

## 架构一览

```text
Paper_Rec_Skill/
├── skill/                      # paper-rec · 文献检索 + Thread + writing gates
├── skill-exp/                  # exp-sandbox · 实验沙箱 + eval_hook / exp_tree / repro
├── skill-draw/                 # plot-draw · /draw + lib/venues.py
├── apps/
│   ├── wiki-api/               # FastAPI  :8787  (/api/threads · /api/exp)
│   ├── wiki-web/               # Vue3 SPA :5173  (/threads · /experiments)
│   └── start-wiki.ps1
├── packages/
│   ├── wiki-bridge/            # sync · thread · integrity CLI（硬闸/图审/综述/反馈）
│   ├── thread-mcp/             # Thread Memory MCP Server
│   └── thread-bot/             # 飞书 / Telegram / 企微 / QQ 对话网关
├── content/
│   ├── wiki/pages/             # <kw>/<year>/<slug>/README.md
│   ├── wiki/pages/_exp/        # 实验 Wiki 镜像
│   ├── threads/                # Cognitive Thread · thread.json + events + evidences
│   ├── thread-templates/       # 主线模板市场
│   ├── exp/                    # metrics · verified_registry · curves · figures · findings
│   ├── weekly/
│   └── uploads/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── THREAD_DESIGN.md
│   ├── BOTS.md
│   ├── MCP.md
│   └── COMPETITOR_LEARN_LOG.md # 能力演进与借鉴审计（可选阅读）
├── scripts/regress_exp_wiki.py
├── VERSION
└── CHANGELOG.md
```

| Layer | Owns |
|:------|:-----|
| **skill/** | 检索流水线、主线注入/重排、`/wiki*`、写作闸门协议 |
| **skill-exp/** | 实验闭环；`eval_hook` / `exp_tree` / `repro_design` / `exp_reflect` |
| **skill-draw/** | `/draw` + venue 顶会风格 |
| **wiki-api / wiki-web** | 阅读、主线、实验看板、图谱 |
| **wiki-bridge** | 结构化报告 ↔ Git Markdown / Threads / 诚信 CLI |
| **thread-mcp** | MCP 暴露主线记忆工具 |
| **thread-bot** | 多渠道路对话 Bot |
| **content/** | 唯一内容真源（可版本管理） |

---

## 设计原则

| Principle | Meaning |
|:----------|:--------|
| **Agent-native** | 以 Markdown Skill 驱动，不绑定单一 IDE |
| **Git as database** | 笔记、实验与主线即文件，可 diff、可备份 |
| **Cognitive before OS** | 护城河是研究主线记忆，而非全能发表流水线 |
| **Predict before burn** | 先多方案偏好排序与小规模验证，再全量训练 |
| **Verify before claim** | Results 数值、引用、图注与综述 cite 须过闸门再导出 |
| **Human in the loop** | 自动关联默认 `suggested`；入库/claim 需 gate |

实验沙箱在方案排序思路上借鉴 [zjunlp/predict-before-execute](https://github.com/zjunlp/predict-before-execute)（Predict-then-Verify）；详见 [skill-exp/README.md](skill-exp/README.md#acknowledgement--借鉴说明)。

能力演进与外部项目对照（可选）：[`docs/COMPETITOR_LEARN_LOG.md`](docs/COMPETITOR_LEARN_LOG.md)。

---

## 文档地图

| Doc | Audience |
|:----|:---------|
| [skill/README.md](skill/README.md) | 文献 Skill 中英入口 |
| [skill/SKILL.md](skill/SKILL.md) | 完整 Module 与 `/wiki` CLI 表 |
| [skill/references/writing-gates.md](skill/references/writing-gates.md) | 写作 / 引用 / 硬闸清单 |
| [skill/references/neurips-review-gate.md](skill/references/neurips-review-gate.md) | 草稿审稿维度 |
| [skill-exp/README.md](skill-exp/README.md) | 实验 Skill · 借鉴说明 |
| [skill-draw/README.md](skill-draw/README.md) | `/draw` 出图 · venue 预设 |
| [packages/wiki-bridge/README.md](packages/wiki-bridge/README.md) | sync + thread + integrity CLI |
| [packages/thread-mcp/README.md](packages/thread-mcp/README.md) | MCP 安装与工具表 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 模块边界与数据约定 |
| [docs/THREAD_DESIGN.md](docs/THREAD_DESIGN.md) | Cognitive Thread v2 契约 |
| [docs/MCP.md](docs/MCP.md) | Thread Memory MCP · research_id 会话 |
| [docs/WEBHOOK.md](docs/WEBHOOK.md) | 可选 Delta webhook 推送 |
| [docs/BOTS.md](docs/BOTS.md) | 飞书 / Telegram / 企微 / QQ 对话 Bot |
| [docs/COMPETITOR_LEARN_LOG.md](docs/COMPETITOR_LEARN_LOG.md) | 能力缺口与借鉴审计日志 |
| [packages/thread-bot/README.md](packages/thread-bot/README.md) | Bot 包安装与端点速查 |
| [benchmarks/REPORT.md](benchmarks/REPORT.md) | 公信力评测成绩单（Thread-Bench · LitSearch…） |
| [benchmarks/thread-bench/README.md](benchmarks/thread-bench/README.md) | Thread-Bench（主线条件排序评测） |
| [benchmarks/litsearch/README.md](benchmarks/litsearch/README.md) | LitSearch 可复现评测 |
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

*Retrieve with any agent. Read in your own wiki. Follow the thread until the metric moves — then verify before you claim.*

<br/>

<sub>MIT License · Built for researchers who close the loop.</sub>

</div>
