# Model selection leaderboards（方案选型用 · 自包含）

Used in `/exp_*` **solution_plan** when a plan needs:
- **closed** models for data/label cleaning / teacher labeling
- **open** models for training base / distillation teacher·student
- **family drill-down** (e.g. pick Qwen → compare best open Qwen variants)

**Rules**
1. Analyze task & badcases first; do not pick models before symptoms are clear.
2. Never invent leaderboard scores — fetch or cite a dated snapshot; if offline, mark `scores: unavailable` and compare by release notes / HF model card metrics only.
3. Prefer **multi-board** evidence (objective + arena), not a single rank.
4. Always write a **comparison table** into `plans/P*.md` before committing to one model.

Source digest curated from workspace `order.txt` + common HF practice (bundled here; no runtime `../` path).

---

## Role → which boards to check

| Role | Typical use in plan | Prefer | Primary boards |
|------|---------------------|--------|----------------|
| `clean_closed` | label_clean / consensus / hard-case rewrite | Closed API | LMArena, Artificial Analysis, SuperCLUE (CN), LLMRank aggregate |
| `clean_open` | local teacher for relabel (privacy / cost) | Open weights | HF Open LLM Leaderboard, OpenCompass, LiveBench |
| `train_base` | SFT / continued pretrain backbone | Open (deployable) | HF Open LLM Leaderboard, OpenCompass, task-specific (code/math/VLM) |
| `distill_teacher` | strong teacher for KD | Closed or large open | Artificial Analysis, LMArena, SuperCLUE; then open distillable teachers on HF |
| `distill_student` | small student to deploy | Open small/mid | HF size filters + task bench; latency/memory constraints from `tool/function` |
| `embed_rerank` | retrieval / embedding clean | Open | MTEB (HF space) / task IR boards |

---

## Board catalog

### Comprehensive / international

| Board | URL | Notes |
|-------|-----|-------|
| Artificial Analysis | https://artificialanalysis.ai/ | Composite of coding/math/reasoning-style evals |
| LMArena (Chatbot Arena) | https://lmarena.ai/ | Elo from blind human votes |
| LiveBench | https://livebench.ai/ | Contamination-aware academic bench |
| BenchLM.ai | https://benchlm.ai/ | Broad multi-model overview |
| Hugging Face Open LLM Leaderboard | https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard | **Open weights**; filter by size / license / type |
| Hugging Face Models (sort downloads/likes + card evals) | https://huggingface.co/models | Family search e.g. `Qwen2.5`, `Qwen3` |

### Chinese-focused

| Board | URL | Notes |
|-------|-----|-------|
| SuperCLUE | https://www.superclueai.com/ | CN general + reasoning/code/agent dims |
| LLMRank | https://llmrank.top/ | Aggregates OpenRouter / SuperCLUE / AA / LMArena / … (no single mega-score) |
| OpenCompass 司南 | https://opencompass.org.cn/ | Multi-ability open eval (CN ecosystem) |

### Specialty

| Ability | Boards |
|---------|--------|
| Code | Aider Polyglot, SuperCLUE-SWE |
| Math | MathArena, AIME-style tracks, FrontierMath (when public) |
| Agent / tools | τ²-Bench, OpenCompass agent tracks |
| Multimodal | SuperCLUE-VLM, HF VLM leaderboards / model cards |

---

## Selection procedure (agent)

```text
1) Decide role(s): clean_closed | clean_open | train_base | distill_teacher | distill_student | …
2) Map task language / modality → boards (CN text → SuperCLUE+OpenCompass; code → Aider+HF; …)
3) Shortlist Top-3–5 candidates with: name, open/closed, size, license, board ranks (date), cost/latency
4) If user or plan picks a family (e.g. Qwen):
     a. Search HF: family + open license + task tags
     b. Compare ≥3 variants (e.g. Qwen2.5-7B-Instruct vs Qwen2.5-14B vs Qwen3-*)
     c. Table: board scores / card evals / VRAM / license / fit to target_score
5) Recommend 1 primary + 1 backup; state why others lose
6) Attach sources + retrieval date in plan markdown
```

### Family drill-down checklist (example: Qwen)

- [ ] List open instruct/chat checkpoints on HF for the family (recent major versions)
- [ ] Filter by deployable size vs `tool/function.notes` GPU
- [ ] Pull Open LLM LB / OpenCompass / SuperCLUE rows when available
- [ ] Prefer official org repos (`Qwen`, `QwenLM`) over unmarked forks
- [ ] Output comparison table **before** locking `train_base` / `distill_*`

---

## Plan markdown snippet (required when model_select applies)

```markdown
## Model selection
- role: train_base | clean_closed | …
- boards consulted: […] (retrieved: YYYY-MM-DD)
- family drill-down: Qwen (yes/no)

| candidate | open/closed | size | key scores | VRAM/cost | decision |
|-----------|-------------|------|------------|-----------|----------|
| … | open | 7B | OpenLLM … | … | primary / backup / reject |

- primary: …
- backup: …
- reject reasons: …
```
