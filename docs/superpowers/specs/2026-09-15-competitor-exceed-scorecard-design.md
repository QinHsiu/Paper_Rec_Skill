# Paper_Rec Competitor Exceed — Scorecard-First Design

**Date:** 2026-09-15  
**Status:** Draft for user review  
**Approach:** Scorecard first, then Critical-engine waves (方案 1)  
**Scope mode:** Full-stack (A + B + C), decomposed into waves  
**Acceptance:** Hybrid (C) — clear Critical gaps, then gold-set regression; closed-source judged on public docs + local/auditable advantages  

---

## 1. Goal

Make `Paper_Rec_Skill` **provably competitive and superior** across retrieval, deep-research trust, and research-thread workflows against **18 existing open-source clones plus ≥5 closed-source products**, without turning the repo into a different product (auto paper OS, second brain, Docker lab suite).

Primary deliverable of the **first sub-project (W0)** is an auditable scorecard + gap priority list + gold-set harness. Implementation waves (W1–W3) close engines mapped from that list.

---

## 2. Decisions locked in brainstorming

| Decision | Choice |
|----------|--------|
| Battlefield | D — full stack (retrieval + trust depth + thread workflow) |
| First move | 4 — matrix + gap priority before feature coding |
| Competitor pool | A — existing 18 OSS clones + ≥5 closed/commercial |
| Acceptance | C — no Critical gaps + small gold-set; closed-source: public parity + local audit edge |
| Delivery path | 方案 1 — scorecard → Critical sprints → polish |

---

## 3. Competitor pool

### 3.1 Open-source (existing clones under `../paper-rec-competitors/`)

1. AutoResearchClaw  
2. AI-Scientist  
3. AI-Scientist-v2  
4. AgentLaboratory  
5. AI-Researcher (clone historically empty — re-clone or mark `N/A` until restored)  
6. AI-Research-SKILLs  
7. PaperPilot  
8. paper-search-pro  
9. paper-qa  
10. OpenScholar  
11. asreview  
12. AutoSurvey  
13. gpt-researcher  
14. STORM  
15. open_deep_research  
16. Curie  
17. khoj  
18. gptr-mcp  

**Extras already noted (optional rows, not required for W0 denominator):** PaperFlow, paperseek, scholar-mcp.

### 3.2 Closed-source / commercial (public-docs evidence only)

Minimum set (≥5; default seven):

1. Elicit  
2. Consensus  
3. Scite  
4. ResearchRabbit  
5. Connected Papers  
6. Semantic Scholar (+ Library / alerts as documented)  
7. NotebookLM (academic / PDF corpus usage)

Evidence tag on every closed-source cell: `public-docs`. No unauthorized reverse engineering, scraping behind login walls, or ToS-violating automation.

### 3.3 Explicit non-goals (do not chase parity)

- 23-stage conference auto-paper OS (AutoResearchClaw whole product)  
- AgentRxiv multi-agent paper store  
- Khoj-class personal second brain  
- Curie full Docker experiment OS  
- OpenScholar retriever training stack  
- gpt-researcher full SaaS frontend  
- STORM as a pure wiki product  
- Wholesale import of 98 domain skills  

These dimensions are scored `不适用` and **excluded from the “全方位超过” denominator**.

---

## 4. Scorecard model

### 4.1 Cell states

Matrix layout: **rows = competitors**, **columns = dimensions**.  
Each cell is Paper_Rec’s standing **relative to that competitor** on that dimension:

| State | Meaning |
|-------|---------|
| `领先` | Paper_Rec clearly better than this competitor |
| `持平` | Comparable capability / quality |
| `落后` | This competitor stronger; gap must be tracked |
| `不适用` | Different product surface; not in win denominator |

### 4.2 Capability axes (A / B / C)

**A — Retrieval & recommendation**

- Multi-source recall  
- Query rewrite / intent  
- Interpretable ranking  
- Graph / related-paper exploration  
- Dedup + discovery saturation  
- Structured report quality  

**B — Deep research & trust**

- Grounded Q&A (chunk relevance cutoff)  
- Citation trust (retraction, OA/S2 conflict, influCit-class signals)  
- Numeric results hard-gate  
- Survey / related-work quality  
- Novelty kill-switch (multi-round where needed)  
- Parallel deep-research + compress  
- Figure↔caption↔body semantic review (real VLM when keyed)  
- Active screening + scientific stoppers  

**C — Thread & daily workflow**

- Cognitive Thread memory (hypothesis / claims / gaps)  
- Watch / interest drift → re-rank  
- Wiki filter **apply** (not parse-only)  
- MCP deferred session (`research_id`) continuity  
- Bot / webhook push  
- Local auditability / scriptable CLI / offline-friendly artifacts  

### 4.3 Acceptance rules (hybrid C)

1. **Critical clear:** Any cell that is `落后` **and** affects correctness or trust (hallucinated metrics, uncited claims, retracted cites, fake fig claims, unbounded screening) must be closed before claiming win.  
2. **Gold-set:** On `evals/goldset`, Paper_Rec must meet or beat the strongest **open-source** baseline for the same task family.  
3. **Closed-source:** For applicable public capabilities, not weaker overall; plus **≥2** clear local/auditable advantages (e.g. git-native wiki, hard-gate registry, thread ledger, runnable CLI without SaaS lock-in).  
4. **`不适用` cells** do not count against “全方位”.

---

## 5. W0 artifacts (this sub-project)

| Artifact | Path | Purpose |
|----------|------|---------|
| Scorecard | `docs/COMPETITOR_SCORECARD.md` | Full matrix: 18 OSS + ≥5 closed × A/B/C dimensions |
| Gap priority | `docs/GAP_PRIORITY.md` | Critical → P0/P1/P2 mapped to engines/CLIs |
| Gold-set harness | `evals/goldset/` | Small fixtures + runner for retrieval, citation fidelity, screening stop, thread drift |
| Learn log Pass 6 | `docs/COMPETITOR_LEARN_LOG.md` | Entry pointing at scorecard + gap table |

W0 **does not** change product behavior except adding eval harness scaffolding if needed.

Seed for gaps: existing Pass 5 leftover list in `COMPETITOR_LEARN_LOG.md` (true VLM, parallel deep-research, trust metadata, AL stoppers, persona lanes, survey LLM deepen, multi-round novelty, interest drift, wiki filter apply, intent audit loop).

---

## 6. Implementation waves (after W0)

| Wave | Goal | Seed engines (final order from `GAP_PRIORITY.md`) |
|------|------|-----------------------------------------------------|
| **W0** | Scorecard + gaps + gold-set skeleton | Docs + `evals/goldset` only |
| **W1** | Critical trust / depth | Real VLM `fig-review`; parallel `deep-research` + compress; retraction / cite-conflict; AL stoppers on `screen-next` |
| **W2** | Coverage + thread | Persona-parallel lanes; survey LLM deepen; multi-round novelty; interest drift → Watch; wiki filter apply; intent on/off rewrite |
| **W3** | Prove + polish | Full gold-set; refresh scorecard to zero Critical; CHANGELOG / positioning narrative |

**Wave exit gate:** update scorecard cells + pass relevant gold-set subset. Fail → no “已超过” claim; fix engine or reduce claim.

Thin-plugin landing (unchanged architecture):

- Engines → `packages/wiki-bridge` CLIs  
- When to call → `skill/` / `skill-exp` / `skill-agents`  
- Artifacts → `content/threads`, `content/wiki`, `metrics/*.json`  
- Continuity → `thread-mcp` / `thread-bot`  

Do **not** add a parallel “super agent OS”.

---

## 7. Data flow (research turn)

1. Skill trigger → optional research-brief / Thread inject  
2. Retrieve / deep-research → candidates + discovery-curve / stoppers  
3. Trust layer → evidence gather + relevance cutoff; `number-verify --hard-gate`; retraction / cite-conflict annotations  
4. Optional fig-review → structure always; VLM if key present else `vlm_skipped` (never fake pass)  
5. Persist → wiki page / thread events / registries  
6. Feedback → `feedback-edit` / Watch drift (W2)

---

## 8. Error handling & degradation

| Failure | Behavior |
|---------|----------|
| External API timeout / missing key (OA, S2, VLM, …) | Degrade; mark `degraded:` in report; do not invent success |
| Hard-gate fail | **Block** export / claimed result numbers; return registry diff |
| Screening stopper / saturation | Stop further waves; emit coverage summary |
| Gold-set regression fail | Wave cannot claim “exceed”; fix or narrow claim |

---

## 9. Testing strategy

- **Unit:** Continue wiki-bridge pytest style per CLI.  
- **Gold-set:** Created in W0; mandatory subset per wave from W1.  
- **Scorecard refresh:** End of each wave, rewrite affected cells with evidence links (OSS: file/CLI; closed: public URL + date).

---

## 10. Sub-project decomposition

| Sub-project | Spec / plan | Depends on |
|-------------|-------------|------------|
| SP0 Scorecard + gold harness | This design → W0 plan | — |
| SP1 Trust engines (W1) | Separate plan after `GAP_PRIORITY.md` | SP0 |
| SP2 Coverage + thread (W2) | Separate plan | SP1 Critical clear |
| SP3 Prove + narrative (W3) | Separate plan | SP2 or partial if only polish left |

Only **SP0** is authorized by approval of this design. SP1+ require gap table output from SP0 before writing their plans.

---

## 11. Success definition for SP0

SP0 is done when:

1. `COMPETITOR_SCORECARD.md` covers all 18 OSS + ≥5 closed products on A/B/C dimensions with cell states and evidence notes.  
2. `GAP_PRIORITY.md` lists Critical/High items with target CLI/module and suggested wave.  
3. `evals/goldset/` has a runnable skeleton (even if fixtures are minimal) and documented how to extend.  
4. `COMPETITOR_LEARN_LOG.md` has a Pass 6 pointer section.  
5. No product claim of “全方位超过” until W1+ gates pass.

---

## 12. Out of scope for SP0

- Implementing W1–W3 engines  
- Re-cloning AI-Researcher beyond noting status  
- Paid closed-source account automation  
- Redesigning Wiki UI or bot adapters unless gap table later requires a thin hook
