# Paper_Rec_Skill

An **Agent Skill** for academic paper recommendation. It runs an end-to-end workflow — query rewriting, multi-source retrieval, scoring, and structured reporting — without requiring any application code. Works with Claude Code, Codex, OpenClaw, and other runtimes that load Markdown skills.

---

## Features

- **Three-stage pipeline**: Input → Retrieval → Output
- **Multi-source search**: arXiv, Hugging Face Papers, GitHub, Papers With Code, CCF top venues, and supplementary industry sources
- **Smart ranking**: Top 50 papers scored by similarity, relevance, and importance
- **Structured reports**: Title, authors, core idea, contribution, metrics, reference value, strengths, and weaknesses (≤2 sentences per field)
- **Three language modes**: English, Chinese, and adaptive

---

## Directory Structure

```
Paper_Rec_Skill/
├── SKILL.md              # Main skill instructions (Input / Retrieval / Output)
├── sources-reference.md  # Retrieval sources, CCF venues, scoring reference
├── output-template.md      # Report templates per language mode
├── examples.md             # Walkthrough examples
├── README.en.md            # This file (English)
└── README.zh-CN.md         # Chinese readme
```

---

## Installation

Copy this directory into your agent’s skills / prompts / instructions path (varies by platform):

```bash
# Example: project-scoped
mkdir -p .agents/skills/paper-rec
cp -r ./* .agents/skills/paper-rec/
# or: skills/paper-rec/ · .claude/skills/paper-rec/ · platform-specific paths
```

| Runtime | Note |
|---------|------|
| Claude Code / Codex / OpenClaw / … | Mount the directory that contains `SKILL.md` |
| Other agents | Any runtime that can load this Markdown pack can trigger `/query_*` |

After installation, use the slash commands below in your agent chat.
---

## Language Modes & Slash Commands

Every query **must** start with one of these commands (documented in this README and in each keyword directory README under `content/wiki/pages/<keyword>/`):

| Command | Mode | Output |
|---------|------|--------|
| `/query_english` | English | All summaries, labels, and report content in **English** |
| `/query_chinese` | Chinese | All summaries, labels, and report content in **Chinese** |
| `/query_other` | Adaptive | Output language matches the detected input language |
| `/wiki` | Wiki ops | List library / this week / start Wiki UI |

### Examples

```
/query_english Find papers on LoRA fine-tuning for large language models

/query_chinese 帮我找2024年后多模态大模型对齐的最新论文

/query_other What are the latest efficient object detection models for edge devices?

/wiki
/wiki start
```

After Module 4 sync, the slash command is appended to `content/wiki/pages/<keyword>/README.md`.

### Rules

- The slash command sets the mode for **that message only**.
- If no command is given, the agent will ask which mode to use before proceeding.
- International sources (arXiv, Hugging Face, GitHub) always include **English search terms** regardless of output language.

---

## Workflow Overview

### Module 1 — Input

Transform the user's raw query into retrieval-ready form:

1. **Summarize** — Compress long or noisy input into a focused summary
2. **Extract keywords** — Derive primary, secondary, and exclude terms
3. **Rewrite query** — Generate broad, specific, keyword, and recent search queries

### Module 2 — Retrieval

Search across multiple sources, score, and rank:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Similarity | 35% | Semantic match to rewritten query |
| Relevance | 35% | Task, method, and domain alignment |
| Importance | 30% | Venue tier, team reputation, recency, code availability |

Results are deduplicated and trimmed to the **top 50** papers.

### Module 3 — Output

Produce a structured report for each paper:

| Field | Description |
|-------|-------------|
| Title | Official paper title |
| Meta | Authors, affiliations, date, source, link |
| Core Idea | Main thesis (≤2 sentences) |
| Contribution | Key novelty (≤2 sentences) |
| Metrics | Benchmark numbers (≤2 sentences) |
| Reference Value | Why this paper matters for your query |
| Strengths | Top advantages (≤2 sentences) |
| Weaknesses | Limitations or gaps (≤2 sentences) |

Top 10 papers receive full entries; ranks 11–50 appear in a compact list.

---

## Retrieval Sources

**Primary**: arXiv · Hugging Face Papers · GitHub · Papers With Code · CCF top conference proceedings

**Supplementary**: Industry research blogs (Google, Meta, Microsoft, OpenAI, etc.), company forums, domain influencers (e.g., Kaiming He for CV)

See [sources-reference.md](sources-reference.md) for the full venue list and scoring details.

---

## Quick Start

1. Mount `skill/` into your agent’s skills directory
2. In the agent chat, type:

   ```
   /query_english Recommend papers on vision transformers for medical imaging
   ```

3. The agent will:
   - Rewrite your query (Input)
   - Search and rank papers (Retrieval)
   - Return a structured report (Output)

For more examples, see [examples.md](examples.md).

---

## Related Files

| File | Purpose |
|------|---------|
| [SKILL.md](SKILL.md) | Full agent instructions |
| [output-template.md](output-template.md) | English / Chinese / adaptive report templates |
| [sources-reference.md](sources-reference.md) | Source URLs, CCF venues, scoring rules |
| [examples.md](examples.md) | End-to-end walkthroughs |

---

## License

Use freely in research workflows and any agent runtime that loads this skill.
