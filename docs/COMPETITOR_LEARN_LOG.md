# Competitor learnings log

Working branch: `feat/competitor-learn`  
Clones: `../paper-rec-competitors/` (**18/18 OK**)

## Pass 1 — surface ports (docs + thin CLI)

See git history 2.25–2.31. Many items were protocol/docs only.

## Pass 2 — deep product gaps → code (2.32.0)

Honest gap analysis: prior “done” rows often lacked engines. Deep P0 implementations now in wiki-bridge:

| Capability | Why it matters (100★ UX) | CLI |
|------------|--------------------------|-----|
| Experiment number whitelist | Papers must not invent Results floats | `number-verify` |
| Discovery saturation | Know when another wave is low-yield | `discovery-curve` |
| Coverage reflection retry | Too few / no PDF / no code → new queries | `reflect-search` |
| Active screening re-rank | accept/skip reshape next batch | `screen-next` |
| Post-hoc attribution | Uncited claims get evidence or gap | `posthoc-cite` |
| Research brief | Clarify → brief → rewrite (not jump to search) | `research-brief` |
| Wiki filter parser | `+ - dt file:` actually parseable | `wiki-filter-parse` |

### Still open (next passes)

Critical→High engines shipped in **2.34.0** (see Pass 3 table below). Remaining:

| Gap | Priority |
|-----|----------|
| VLM semantic figure↔plot check (beyond heuristic) | P1 |
| Persona-parallel question lanes | P1 |
| Devil’s-advocate overclaim / wiki filter apply / … | P2 (Medium) |

### Shipped in 2.33

- Experiment tree / ablation journal (`exp_tree` + `exp-tree` CLI)
- number-verify ↔ `/exp_eval` (`eval_hook` + `exp-eval-hook`)

## Pass 3 — pain-point audit (2026-07-22, all 18)

Prior ports closed many *surface* gaps; remaining items are **engines** that still hurt users (hallucinated answers, fake wins, empty related-work, wasted GPU on non-novel ideas).

### Still worth building (ranked)

| Rank | Pain | Severity | Best source pattern | Paper_Rec gap today |
|------|------|----------|---------------------|---------------------|
| 1 | Grounded Q&A still uses unscored chunks | **Critical** | paper-qa map-reduce `relevance_score` | `answer-ground` expands cites; no chunk score cutoff |
| 2 | Results prose without ±/CI/seeds ships | **Critical** | AutoResearchClaw statistical rigor gate | `number-verify` = float whitelist only |
| 3 | Ablation journal ≠ control vs experimental + re-run | **Critical** | Curie partitions + double-exec | `exp_tree` logs nodes; no A/B repro seal |
| 4 | Related-work stays outline, not survey prose | **Critical** | AutoSurvey outline-merge + subsection RAG | writing-gates notes only |
| 5 | Ideas start without literature kill-switch | **High** | AI-Scientist `check_idea_novelty` | `idea-template` docs-only |
| 6 | Figures/captions can contradict plots | **High** | AI-Scientist-v2 VLM fig review | `/draw` has no vision gate |
| 7 | Experiment churn without narrative synthesis | **High** | AI-Research-SKILLs outer `/exp_reflect` + findings.md | no outer-loop artifact |
| 8 | Multi-facet topics gathered serially / shallow | **High** | open_deep_research parallel supervisor / GPT-R depth tree | `reflect-search` = one coverage pass |
| 9 | Screening 500+ papers still hand-slog | **High** | asreview real AL cycle | `screen-next` = centroid toy |
| 10 | MCP gather→write loses session | **High** | gptr-mcp `research_id` → deferred `write_report` | MCP.md protocol only |

### Pass 3 Critical→High — shipped (2026-07-22, workspace 2.34.0)

| Rank | Engine | CLI / artifact |
|------|--------|----------------|
| 1 | Chunk relevance map-reduce | `gather-evidence` + `answer-ground --relevance-cutoff` |
| 2 | Stats rigor beyond float whitelist | `stats-rigor` |
| 3 | Control/experimental + double-exec | `repro-check` → `trace/repro_check.json` |
| 4 | Survey outline-merge + subsection RAG | `survey-draft` |
| 5 | Novelty kill-switch | `novelty-check` (+ optional OpenAlex) |
| 6 | Fig/caption review | `fig-review` (VLM hook stub) |
| 7 | Outer exp reflect | `exp-reflect` → `findings.md` |
| 8 | Deep research tree | `deep-research` |
| 9 | Realer AL screening | `screen-next` TF-IDF hybrid |
| 10 | Deferred research session | `research-session` (`research_id`) |

Medium/polish rows below remain deferred.

### Medium / polish (defer)

| Item | Source | Note |
|------|--------|------|
| Devil’s-advocate overclaim gate | PaperPilot | after claim-ledger |
| Cross-source citation-count conflict | paper-search-pro | OA vs S2 ≥30% |
| Feedback→re-retrieve edit loop | OpenScholar | after chunk scoring |
| Persona-parallel question lanes | storm | coverage skew |
| Wiki filter **apply** on pages API | khoj | parse exists; apply missing |
| Review→forced re-experiment | AgentLaboratory | Medium |
| AI-Researcher | — | empty clone; skip until re-cloned |

### Saturated (little left)

paper-search-pro (core retrieval), PaperPilot (filters/matrix/ledger), first-wave citation/latex ports.

## Pass 4 — differentiation audit (2026-07-22)

Lens: **what would a user pick THIS repo for**, and which engines are still deeper than Paper_Rec stubs — not feature-name parity.

### Top 8 still worth building

| # | Capability | Why it still hurts | Best source | Paper_Rec today | Pri |
|---|------------|--------------------|-------------|-----------------|-----|
| 1 | Results **hard gate** (registry → prose/table BLOCK) | Fake metrics still ship if writer ignores soft verify | AutoResearchClaw `verified_registry.py` + Stage20 | `number-verify` / `stats-rigor` advisory | P0 |
| 2 | **VLM** fig↔caption↔body semantic review | Heuristic misses lying plots | AI-Scientist-v2 `perform_vlm_review.py` | `fig-review` structure + stub hook | P0 |
| 3 | True survey: LLM outline-merge + subsection RAG + cite check | Related-work still keyword buckets | AutoSurvey `src/prompt.py` | `survey-draft` heuristic | P0 |
| 4 | Feedback → rewrite → **re-retrieve** | Answers look grounded but drift | OpenScholar `open_scholar.py` | `posthoc-cite` / `answer-ground` one-shot | P0 |
| 5 | Supervisor **parallel** sub-research + compress | Multi-facet topics stay serial/shallow | open_deep_research `deep_researcher.py` | `deep-research` structure-only | P0 |
| 6 | Scientific AL + **stoppers** | 500+ screening still hand-slog | asreview `learner.py` / `stoppers.py` | `screen-next` TF-IDF toy | P0/P1 |
| 7 | Persona-parallel questions / Co-STORM mind map | Coverage skew | storm `persona_generator.py` | none | P1 |
| 8 | Trust layer: **retraction** + OA/S2 cite-count conflict + influCit | Bad cites / dirty rank | paper-qa retract; PSP `ss_helper.py` | none | P1 |

### Per-repo differentiator (1-liner) + leftover borrow

| Repo | Pick this when you want… | Still borrow (thin plugin) | Skip / different product |
|------|--------------------------|----------------------------|--------------------------|
| AutoResearchClaw | one-shot conference paper OS | VerifiedRegistry hard BLOCK; MetaClaw lesson→skill | 23-stage + domain sandboxes |
| AI-Scientist | template idea→exp→write loop | multi-round harsh novelty critic | full auto discovery |
| AI-Scientist-v2 | BFTS tree + workshop writeup | **VLM** img/cap/ref review; tree export | full BFTS writer |
| AgentLaboratory | human-in-loop lab phases | review-score → forced revise/re-exp | AgentRxiv multi-agent store |
| AI-Research-SKILLs | skill pack + outer/inner loops | ARA 6-dim rigor; DEEPEN/BROADEN/PIVOT | 98 domain skills wholesale |
| PaperPilot | protocolized lit review CLI | devil’s-advocate overclaim agent | Obsidian/PDF polish |
| paper-search-pro | multi-source Skill search + tiers | cite-count conflict; influCit; PRISMA-S log | tier UX only |
| paper-qa | agentic paper RAG that refuses | retraction flags; multimodal fig chunks | — (RCS already ported) |
| OpenScholar | ScholarQA-grade RAG edits | feedback→edit→re-retrieve loop | train 8B retriever |
| asreview | Nature-grade systematic screening | querier/balancer/stopper + simulation | full Web LAB |
| AutoSurvey | large-corpus survey generation | real outline-merge + subsection cite check | 530k local DB ops |
| gpt-researcher | parallel web deep research SaaS | role agent_creator + parallel lanes | full frontend SaaS |
| storm | wiki-style multi-perspective articles | persona lanes; Co-STORM mind map | pure wiki product |
| open_deep_research | LangGraph clarify→brief→supervisor | max_concurrent ConductResearch + compress | — |
| Curie | Docker rigorous ML experiments | patcher redo_partition; exec_validator | full Docker OS |
| khoj | personal second brain | **apply** wiki filters (parse exists) | whole second-brain |
| gptr-mcp | MCP deferred research write | expose research_id tools in thread-MCP | — |
| AI-Researcher | — | empty clone; skip | — |

### Extra clones (not in original 18) — quick take

| Repo | Differentiator | Borrow? |
|------|----------------|---------|
| **PaperFlow** | daily personalized digest + interest-drift feedback loop | P1: Watch/Delta profile drift from accept/skip (thread feedback → tomorrow rank) |
| **paperseek** | per-source query gen + intent audit + multi-recall prerank | P1: deepen `rank-intent` / reflect with on-/off-intent revision |
| **scholar-mcp** | S2→arXiv→CORE→PubMed→GS fallback + PDF chain | P2: PDF discovery via CORE (if ingest miss rate high) |

### Explicit non-goals (stay Paper_Rec)

Do **not** become: 23-stage auto paper OS, AgentRxiv, Khoj second brain, Curie Docker lab suite, or OpenScholar model training stack. Keep thin plugins into threads / wiki / packs / exp-sandbox.

### Pass 4 P0 — shipped (2026-07-22, workspace 2.35.0)

| # | Engine | CLI / artifact |
|---|--------|----------------|
| 1 | Results hard gate | `number-verify --hard-gate --write-registry`; `latex-export --hard-gate`; `metrics/verified_registry.json` |
| 2 | Fig semantic + VLM hook | `fig-review --emit-vlm-prompts` / `--vlm-json` |
| 3 | True-er survey | `survey-draft` TF-IDF clusters + cite audit (`--strict`) |
| 4 | Feedback → rewrite → re-retrieve | `feedback-edit` |

## Pass 5 — leftover after multi-agent-lab (2026-07-22, workspace 2.36)

Lens: after hard-gate / survey deepen / feedback-edit / fig VLM-hook / **skill-agents** Brain+tiers, what engines are **still shallow or missing**?

### Verdict

Surface ports and orchestration are largely saturated. Lab ate most “who does what / which model tier” value. Remaining ROI is **deeper engines**, not more role markdown.

### Top 10 still worth building

| # | Capability | Best source | Paper_Rec today | Pri |
|---|------------|-------------|-----------------|-----|
| 1 | **True VLM call** fig↔caption↔body | AI-Scientist-v2 `perform_vlm_review.py` / `vlm.py` | `fig-review` prompts + `--vlm-json` only | P0 |
| 2 | Supervisor **parallel** sub-research + compress | open_deep_research ConductResearch / compress | `deep-research` tree; lab sequential DAG | P0 |
| 3 | Trust: **retraction** + OA/S2 cite conflict + influCit | paper-qa `retractions.py`; PSP `ss_helper.py` | none | P1 |
| 4 | Scientific AL **stoppers** (N-consecutive irrelevant, …) | asreview `models/stoppers.py` | `screen-next` fake consecutive | P0/P1 |
| 5 | Persona parallel lanes / Co-STORM topic map | storm `persona_generator.py` | none | P1 |
| 6 | Survey **LLM** outline-merge + subsection RAG (±NLI) | AutoSurvey `src/prompt.py` | TF-IDF `survey-draft` | P1 |
| 7 | Multi-round **harsh novelty** + live search | AI-Scientist `generate_ideas.py` | single-shot `novelty-check` | P1 |
| 8 | Interest **drift → Watch/rank** | PaperFlow `drift_engine.py` | feedback events unused for profile | P1 |
| 9 | Wiki filter **apply** on pages search | khoj search_filter; local `match_meta` unused by API | parse-only CLI | P1 |
| 10 | Intent audit → **on/off-intent** rewrite | paperseek prompts/revision loop | `rank-intent` / `reflect` no audit loop | P1 |

### Honorable mentions (P2)

ARA 6-dim scorer · Devil’s-advocate code into Critique · MetaClaw lesson→skill · CORE PDF fallback · PRISMA-S log · Curie redo_partition · gpt-r dynamic agent_creator.

### Saturated / different-product

| State | Repos |
|-------|--------|
| Mostly squeezed | gptr-mcp; PaperPilot (except devil’s); PSP core retrieve; OpenScholar main loop; ARC hard-gate/stats surface |
| Different product only | Curie Docker OS; AgentRxiv; khoj second brain; AI-Scientist(v2) full discovery; gpt-researcher SaaS; storm pure wiki; SKILLs×98; AutoSurvey 530k DB |
| Lab already covers | Brain/roles/tiers; Accept-before-Write protocol text (needs engines above, not more agents) |

### Suggested next cut

**#1–#4 first** (true vision gate · parallel deep research · trust metadata · real screening stop). Then #5–#10 by product need (survey-heavy → #6; daily Watch → #8).
