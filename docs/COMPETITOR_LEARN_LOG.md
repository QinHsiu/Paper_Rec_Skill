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

| Gap | Priority |
|-----|----------|
| Map-reduce per-chunk evidence scores before answer | P0 |
| Control/experimental partitions + double-exec repro | P0 |
| Survey outline-merge + subsection RAG writer | P0 |
| Outer `/exp_reflect` + 6-dim rigor seal | P0 |
| Deferred MCP `research_id` → write_report | P1 |
| VLM figure↔caption review | P1 |
| Persona-parallel question lanes | P1 |

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
