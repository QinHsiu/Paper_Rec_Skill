# Paper_Rec_Skill

面向通用 **Agent** 的学术论文推荐技能（Claude Code · Codex · OpenClaw 等）。通过「输入改写 → 多源检索 → 结构化输出」全流程，帮你快速找到相关论文并生成精炼报告，无需编写任何应用代码。

---

## 功能特点

- **三阶段流水线**：输入 → 检索 → 输出
- **多源检索**：arXiv、Hugging Face Papers、GitHub、Papers With Code、CCF 顶会及大厂补充来源
- **智能排序**：按相似性、相关性、重要性三维打分，保留 Top 50
- **结构化报告**：论文题目、发表信息、核心观点、核心贡献、指标、参考价值、强项、不足（每字段最多 2 句话）
- **三种语言模式**：英文、中文、自适应

---

## 目录结构

```
Paper_Rec_Skill/
├── SKILL.md              # 主技能文件（输入 / 检索 / 输出）
├── sources-reference.md  # 检索来源、CCF 顶会、打分参考
├── output-template.md    # 各语言模式的报告模板
├── examples.md             # 完整 walkthrough 示例
├── README.en.md            # 英文说明
└── README.zh-CN.md         # 本文件（中文说明）
```

---

## 安装方法

将本目录复制到所用 Agent 的 skills / prompts / 指令目录（路径因平台而异）：

```bash
# 示例：项目级
mkdir -p .agents/skills/paper-rec
cp -r ./* .agents/skills/paper-rec/
# 或 skills/paper-rec/ · .claude/skills/paper-rec/ · 平台自定义路径
```

| 平台 | 说明 |
|------|------|
| Claude Code / Codex / OpenClaw / … | 挂载含 `SKILL.md` 的目录即可 |
| 其他 Agent | 能加载本目录 Markdown 指令即可触发 `/query_*` |

安装完成后，在对话中使用下方 slash 命令即可触发该技能。
---

## 语言模式与 Slash 命令

每条查询 **必须以** 以下命令之一开头（本目录 README 与关键词目录 README 均记录 `/query_*`）：

| 命令 | 模式 | 输出语言 |
|------|------|----------|
| `/query_english` | 英语模式 | 摘要、标签、报告正文 — **全英文** |
| `/query_chinese` | 中文模式 | 摘要、标签、报告正文 — **全中文** |
| `/query_other` | 自适应模式 | **根据输入语言自动匹配**输出语言 |
| `/wiki` | 阅读库 | 列出论文 / 本周推荐 / 启动 Wiki UI |

### 使用示例

```
/query_english Find papers on LoRA fine-tuning for large language models

/query_chinese 帮我找2024年后多模态大模型对齐的最新论文

/query_other 帮我 find efficient object detection papers for edge devices

/wiki
/wiki start
```

同步入库后，对应关键词目录会更新 `content/wiki/pages/<keyword>/README.md`（记录本次 `/query_*` 与论文链接）。

### 规则说明

- 语言模式 **按消息生效**，每条消息独立设置。
- 若未带命令，Agent 会先询问使用哪种模式再继续。
- 无论输出语言，对 arXiv、Hugging Face、GitHub 等国际源始终附加 **英文检索词** 以保证召回率。

### 自适应模式（`/query_other`）检测逻辑

| 输入语言 | 输出行为 |
|----------|----------|
| 以中文为主 | 等同 `/query_chinese` |
| 以英文为主 | 等同 `/query_english` |
| 中英混合 | 以主要研究问题的语言为准 |
| 其他语言（日/韩/法等） | 正文用该语言；检索仍含英文关键词 |

---

## 工作流概览

### 模块一：输入

将用户原始 query 转化为可检索形式：

1. **摘要** — 过长或多主题输入压缩为聚焦摘要
2. **抽取关键词** — 提取 Primary / Secondary / Exclude 三级关键词
3. **改写 query** — 生成宽泛、精确、关键词、时效四类检索式

### 模块二：检索

多源搜索、打分、排序：

| 维度 | 权重 | 衡量内容 |
|------|------|----------|
| 相似性 | 35% | 与改写 query 的语义匹配度 |
| 相关性 | 35% | 任务、方法、领域与用户意图的契合度 |
| 重要性 | 30% | 会议档次、团队声誉、时效性、代码可用性 |

去重后保留 **Top 50** 篇论文。

### 模块三：输出

为每篇论文生成结构化报告：

| 字段 | 说明 |
|------|------|
| 论文题目 | 保留英文原标题，可附中文译名 |
| 发表信息 | 团队、单位、时间、来源、链接 |
| 核心观点 | 论文主旨（≤2 句话） |
| 核心贡献 | 主要创新点（≤2 句话） |
| 指标 | 关键 benchmark 数据（≤2 句话） |
| 参考价值 | 与你 query 的关联理由 |
| 强项 | 主要优势（≤2 句话） |
| 不足之处 | 局限或空白（≤2 句话） |

排名前 10 的论文输出完整条目；第 11–50 名以紧凑列表呈现。

---

## 检索来源

**主要来源**：arXiv · Hugging Face Papers · GitHub · Papers With Code · CCF 顶会官网

**补充来源**：大厂研究博客（Google、Meta、Microsoft、OpenAI 等）、公司论坛、领域 KOL（如 CV 领域可关注何凯明）

完整会议列表与打分细则见 [sources-reference.md](sources-reference.md)。

---

## 快速开始

1. 将 `skill/` 挂到 Agent 可读的 skills 目录
2. 在对话中输入：

   ```
   /query_chinese 推荐几篇关于医学影像 Vision Transformer 的论文
   ```

3. Agent 将依次执行：
   - 改写 query（输入模块）
   - 多源检索与排序（检索模块）
   - 输出结构化报告（输出模块）

更多示例见 [examples.md](examples.md)。

---

## 相关文件

| 文件 | 用途 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 完整执行指令 |
| [output-template.md](output-template.md) | 英文 / 中文 / 自适应报告模板 |
| [sources-reference.md](sources-reference.md) | 来源 URL、CCF 顶会、打分规则 |
| [examples.md](examples.md) | 端到端 walkthrough 示例 |

---

## 许可

可在研究工作流及任意可加载本技能的 Agent 中自由使用。
