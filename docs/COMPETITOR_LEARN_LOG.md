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
