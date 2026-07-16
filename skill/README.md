<div align="center">

# Paper_Rec

**Intelligent Literature Retrieval · Agent Skill**  
**智能文献检索 · Agent 技能（跨平台）**

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](VERSION)
[![Agents](https://img.shields.io/badge/Agents-Claude%20·%20Codex%20·%20OpenClaw%20·%20more-3D5A80?style=flat)](SKILL.md)
[![SemVer](https://img.shields.io/badge/SemVer-2.0.0-green.svg)](https://semver.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](#license)

*Query rewriting · Multi-source retrieval · Structured synthesis*

[English Docs](README.en.md) · [中文文档](README.zh-CN.md) · [Changelog](CHANGELOG.md)

</div>

---

## Overview / 概览

**Paper_Rec** is a production-ready **Agent Skill** that transforms natural-language research questions into ranked, structured literature reports — without writing application code. Works with Claude Code, Codex, OpenClaw, and other runtimes that load Markdown skills.

**Paper_Rec** 是一套面向通用 Agent 的文献检索技能，将自然语言研究问题转化为排序后的结构化论文报告。可在 Claude Code、Codex、OpenClaw 等平台挂载使用。

```mermaid
flowchart LR
    A[User Query<br/>用户 Query] --> B[Input Module<br/>输入模块]
    B --> C[Retrieval Module<br/>检索模块]
    C --> D[Output Module<br/>输出模块]
    D --> E[Structured Report<br/>结构化报告]

    B --> B1[Summarize 摘要]
    B --> B2[Keywords 关键词]
    B --> B3[Rewrite 改写]

    C --> C1[Multi-Source Search]
    C --> C2[Score & Rank Top-50]

    D --> D1[Core Fields × ≤2 sentences]
```

---

## Version Control / 版本控制

| Item | Location | Description |
|------|----------|-------------|
| **Current version** | [`VERSION`](VERSION) | Single source of truth (`1.3.0`) |
| **Change history** | [`CHANGELOG.md`](CHANGELOG.md) | SemVer-compliant release notes |
| **Skill manifest** | [`SKILL.md`](SKILL.md) | Agent execution spec (`name: paper-rec`) |
| **Repository** | [github.com/QinHsiu/Paper_Rec_Skill](https://github.com/QinHsiu/Paper_Rec_Skill) | Git remote for version tracking |

### Release workflow / 发版流程

1. Update skill logic or docs in this directory
2. Bump [`VERSION`](VERSION) following [SemVer](https://semver.org/)
3. Add entry to [`CHANGELOG.md`](CHANGELOG.md)
4. Sync the `skill/` pack into your agent’s skills directory and commit with tag `vX.Y.Z`

```bash
git add VERSION CHANGELOG.md SKILL.md
git commit -m "release: v1.3.0"
git tag v1.3.0
git push origin master --tags
```

---

## Quick Start / 快速开始

### 1 · Install / 安装

将本目录内容复制到 Agent 可读的 skills / prompts 路径（按平台调整）：

```bash
# 示例：项目级 skills 目录
mkdir -p .agents/skills/paper-rec
cp -r ./* .agents/skills/paper-rec/
# 或: skills/paper-rec/ · .claude/skills/paper-rec/ · 平台自定义路径
```

| Runtime | Note |
|---------|------|
| Claude Code / Codex / OpenClaw / … | 挂载 `SKILL.md` 所在目录即可 |
| 任意 Agent | 能加载本目录 Markdown 指令即可触发 `/query_*` |

Workspace hub: [../README.md](../README.md)

Reload / restart your agent session after install.

### 2 · Activate / 启用

Prefix every query with a language command (`/query_*` 必须写入本目录 README，并在同步时写入 `content/wiki/pages/<keyword>/README.md`)：

| Command | Mode | Output |
|---------|------|--------|
| `/query_english` | English | Full English report |
| `/query_chinese` | Chinese | 全中文报告 |
| `/query_other` | Adaptive | 自适应输入语言 |
| `/wiki` | Wiki ops | 查库 / 本周 / 启动界面 |

```
/query_english Find papers on efficient LLM fine-tuning with LoRA
/query_chinese 帮我找2024年后多模态大模型对齐的最新论文
/query_other  最新の物体検出モデルに関する論文を探して
/wiki
/wiki start
```

Persist (Module 4) 后：论文进 `content/wiki/pages/<keyword>/`，**`/query_*` 命令记入该关键词目录 `README.md`**，并进入「一周推荐」（去重追加）。

### 3 · Receive report / 获取报告

The agent executes **Input → Retrieval → Output** and returns a structured report with Top-10 full entries and Top-11–50 compact list.

---

## Architecture / 架构

| Module | 模块 | Responsibility | Key output |
|--------|------|----------------|------------|
| **Input** | 输入 | Summarize · Keywords · Query rewrite | Retrieval-ready queries |
| **Retrieval** | 检索 | Multi-source search · 3D scoring · Top-50 | Ranked candidate pool |
| **Output** | 输出 | Structured synthesis | Per-paper report fields |

**Scoring model** (Retrieval):

$$\text{Final} = 0.35 \times \text{Similarity} + 0.35 \times \text{Relevance} + 0.30 \times \text{Importance}$$

---

## Documentation / 文档索引

| Document | Purpose |
|----------|---------|
| [SKILL.md](SKILL.md) | Agent execution instructions |
| [sources-reference.md](sources-reference.md) | Sources, CCF venues, scoring rules |
| [output-template.md](output-template.md) | EN / CN / adaptive report templates |
| [examples.md](examples.md) | End-to-end walkthroughs |
| [README.en.md](README.en.md) | Full English guide |
| [README.zh-CN.md](README.zh-CN.md) | 完整中文指南 |

---

## Best Practices & Authoritative Resources / 最佳实践与权威资源

Paper_Rec is designed to align with established literature retrieval conventions. The following references define **best-practice sources and standards** used by this skill.

### Primary retrieval sources / 主要检索源

| Resource | URL | Best for |
|----------|-----|----------|
| **arXiv** | [arxiv.org](https://arxiv.org/) | Latest preprints; category-filtered CS/AI search |
| **Hugging Face Papers** | [huggingface.co/papers](https://huggingface.co/papers) | Community-trending ML papers |
| **Papers With Code** | [paperswithcode.com](https://paperswithcode.com/) | SOTA benchmarks & reproducibility |
| **GitHub** | [github.com/search](https://github.com/search) | Implementations & active repos |
| **Semantic Scholar** | [semanticscholar.org](https://www.semanticscholar.org/) | Citation graph & paper metadata |
| **DBLP** | [dblp.org](https://dblp.org/) | Authoritative CS bibliography |
| **OpenReview** | [openreview.net](https://openreview.net/) | ICLR and peer-review transparency |
| **ACL Anthology** | [aclanthology.org](https://aclanthology.org/) | NLP proceedings archive |

### Venue & ranking standards / 会议与分级标准

| Resource | URL | Role in Paper_Rec |
|----------|-----|-------------------|
| **CCF Recommended List** | [ccf.org.cn/Academic_Evaluation](https://www.ccf.org.cn/Academic_Evaluation/) | Chinese tier-A/B venue classification |
| **NeurIPS / ICML / ICLR** | [neurips.cc](https://neurips.cc/) · [icml.cc](https://icml.cc/) · [iclr.cc](https://iclr.cc/) | Tier-1 ML importance boost |
| **CVF Open Access** | [openaccess.thecvf.com](https://openaccess.thecvf.com/) | CVPR / ICCV / ECCV proceedings |

### Supplementary intelligence / 补充情报源

| Resource | URL | When to use |
|----------|-----|-------------|
| **Google Research** | [research.google](https://research.google/) | Industry flagship releases |
| **Meta AI Research** | [ai.meta.com/research](https://ai.meta.com/research/) | FAIR & applied ML papers |
| **Microsoft Research** | [microsoft.com/en-us/research](https://www.microsoft.com/en-us/research/) | Systems + ML crossover |
| **OpenAI Research** | [openai.com/research](https://openai.com/research) | Foundation model advances |

### Agent platforms / Agent 平台

Paper_Rec 不绑定单一 IDE。将 `skill/` 挂到 Claude Code、Codex、OpenClaw 等平台的 skills / 指令目录即可；核心入口始终是 [`SKILL.md`](SKILL.md)。

### Retrieval best practices enforced by this skill

1. **Always deduplicate** by arXiv ID / DOI / normalized title before ranking
2. **Always include English search terms** for international indexes, even in Chinese output mode
3. **Prefer primary sources** (PDF, arXiv abstract, official project page) over blog summaries
4. **Never fabricate** citation counts, benchmark numbers, or venue status
5. **Cap verbosity**: ≤2 sentences per report field; Top-10 full + 11–50 compact
6. **Flag uncertainty**: mark preprints, missing metrics, and inaccessible papers explicitly

---

## Project Structure / 项目结构

```
Paper_Rec_Skill/
├── SKILL.md                 # Agent skill spec
├── VERSION                  # Current release (1.3.0)
├── CHANGELOG.md             # SemVer release history
├── sources-reference.md     # Source & venue reference
├── output-template.md       # Report templates
├── examples.md              # Walkthrough examples
├── README.md                # This file (project hub)
├── README.en.md             # English guide
└── README.zh-CN.md          # Chinese guide
```

---

## License

MIT — free to use in research workflows and any agent runtime that loads this skill.

---

<div align="center">

**Paper_Rec** · v1.3.0 · Retrieve with any agent · remember in your wiki.

</div>
