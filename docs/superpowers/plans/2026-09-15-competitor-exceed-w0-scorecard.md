# Competitor Exceed W0 Scorecard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver SP0/W0 — auditable competitor scorecard (18 OSS + ≥5 closed), gap priority table, gold-set harness skeleton, and Pass 6 learn-log pointer — with no product-behavior claim of “全方位超过” yet.

**Architecture:** Machine-checkable scorecard lives as JSON under `evals/competitor_scorecard/`; a small stdlib renderer writes `docs/COMPETITOR_SCORECARD.md`. Gap priority is derived from `落后` cells that touch trust/correctness, seeded by Pass 5 leftovers. Gold-set cases under `evals/goldset/` run via a stdlib runner that exercises existing wiki-bridge pure functions offline.

**Tech Stack:** Python 3.10+, stdlib only (match `wiki-bridge` `requires-python >=3.10`, `dependencies = []`), Markdown docs, pytest already used in `packages/wiki-bridge/tests/`.

## Global Constraints

- Scope is **SP0/W0 only** — do not implement W1–W3 engines in this plan.
- Competitor pool: existing **18 OSS** clones + **≥5 closed** (default 7: Elicit, Consensus, Scite, ResearchRabbit, Connected Papers, Semantic Scholar, NotebookLM).
- Cell states exactly: `领先` | `持平` | `落后` | `不适用` (Paper_Rec relative to that competitor).
- Closed-source evidence tag: `public-docs` only; no login scraping / reverse engineering.
- Explicit non-goals stay `不适用` (23-stage OS, AgentRxiv, Khoj second brain, Curie Docker OS, OpenScholar training, gpt-researcher SaaS UI, STORM pure wiki, SKILLs×98 wholesale).
- Acceptance hybrid C applies after W1+; W0 must **not** claim product-wide “全方位超过”.
- Prefer Windows-friendly shell; commits use `git commit -m "message"` (no bash HEREDOC required).

---

## File Structure

| Path | Responsibility |
|------|----------------|
| `evals/competitor_scorecard/schema.py` | Dimension IDs + axes A/B/C constants |
| `evals/competitor_scorecard/data.json` | All competitor rows × dimension cells |
| `evals/competitor_scorecard/validate.py` | Completeness + enum checks; exit ≠0 on fail |
| `evals/competitor_scorecard/render.py` | JSON → `docs/COMPETITOR_SCORECARD.md` |
| `evals/competitor_scorecard/test_scorecard.py` | Pytest for validate + render |
| `docs/COMPETITOR_SCORECARD.md` | Generated human-readable matrix |
| `docs/GAP_PRIORITY.md` | Critical/High gaps → CLI/module → wave |
| `evals/goldset/README.md` | How to add cases / run |
| `evals/goldset/cases/*.json` | Minimal offline fixtures (4 families) |
| `evals/goldset/run_goldset.py` | Stdlib runner → JSON summary |
| `evals/goldset/test_run_goldset.py` | Pytest wrapper |
| `docs/COMPETITOR_LEARN_LOG.md` | Append Pass 6 section |

---

### Task 1: Scorecard schema + failing completeness test

**Files:**
- Create: `evals/competitor_scorecard/schema.py`
- Create: `evals/competitor_scorecard/validate.py`
- Create: `evals/competitor_scorecard/test_scorecard.py`
- Create: `evals/competitor_scorecard/data.json` (minimal stub that fails completeness)

**Interfaces:**
- Consumes: nothing
- Produces:
  - `DIMENSIONS: list[dict]` with keys `id`, `axis` (`A`|`B`|`C`), `label`
  - `OSS_COMPETITORS: list[str]` (exactly 18 names from spec)
  - `CLOSED_COMPETITORS: list[str]` (≥5)
  - `CELL_STATES = frozenset({"领先", "持平", "落后", "不适用"})`
  - `validate_scorecard(data: dict) -> list[str]` returning error strings (empty = ok)

- [ ] **Step 1: Write the failing test**

```python
# evals/competitor_scorecard/test_scorecard.py
from __future__ import annotations

import json
from pathlib import Path

from schema import CLOSED_COMPETITORS, DIMENSIONS, OSS_COMPETITORS
from validate import validate_scorecard

HERE = Path(__file__).resolve().parent


def test_dimension_count_and_axes():
    assert len(DIMENSIONS) >= 18
    axes = {d["axis"] for d in DIMENSIONS}
    assert axes == {"A", "B", "C"}


def test_competitor_pool_sizes():
    assert len(OSS_COMPETITORS) == 18
    assert len(CLOSED_COMPETITORS) >= 5


def test_data_json_validates_complete():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    errors = validate_scorecard(data)
    assert errors == [], errors
```

- [ ] **Step 2: Run test to verify it fails**

Run (from repo root):

```powershell
cd D:\PycharmProjects\pythonProject\projects\Paper_Rec_Skill
python -m pytest evals/competitor_scorecard/test_scorecard.py -v
```

Expected: FAIL — missing modules and/or incomplete `data.json`.

- [ ] **Step 3: Write schema + validate + stub data**

```python
# evals/competitor_scorecard/schema.py
from __future__ import annotations

DIMENSIONS: list[dict[str, str]] = [
    {"id": "a_multi_source", "axis": "A", "label": "Multi-source recall"},
    {"id": "a_query_rewrite", "axis": "A", "label": "Query rewrite / intent"},
    {"id": "a_ranking", "axis": "A", "label": "Interpretable ranking"},
    {"id": "a_graph_explore", "axis": "A", "label": "Graph / related-paper exploration"},
    {"id": "a_saturation", "axis": "A", "label": "Dedup + discovery saturation"},
    {"id": "a_report", "axis": "A", "label": "Structured report quality"},
    {"id": "b_grounded_qa", "axis": "B", "label": "Grounded Q&A"},
    {"id": "b_citation_trust", "axis": "B", "label": "Citation trust (retraction / conflict)"},
    {"id": "b_hard_gate", "axis": "B", "label": "Numeric results hard-gate"},
    {"id": "b_survey", "axis": "B", "label": "Survey / related-work quality"},
    {"id": "b_novelty", "axis": "B", "label": "Novelty kill-switch"},
    {"id": "b_parallel_deep", "axis": "B", "label": "Parallel deep-research + compress"},
    {"id": "b_fig_vlm", "axis": "B", "label": "Figure semantic / VLM review"},
    {"id": "b_al_stop", "axis": "B", "label": "Active screening + stoppers"},
    {"id": "c_thread", "axis": "C", "label": "Cognitive Thread memory"},
    {"id": "c_drift_watch", "axis": "C", "label": "Interest drift → Watch/rank"},
    {"id": "c_wiki_filter", "axis": "C", "label": "Wiki filter apply"},
    {"id": "c_mcp_session", "axis": "C", "label": "MCP deferred research_id"},
    {"id": "c_bot_push", "axis": "C", "label": "Bot / webhook push"},
    {"id": "c_local_audit", "axis": "C", "label": "Local auditability / CLI"},
]

OSS_COMPETITORS = [
    "AutoResearchClaw",
    "AI-Scientist",
    "AI-Scientist-v2",
    "AgentLaboratory",
    "AI-Researcher",
    "AI-Research-SKILLs",
    "PaperPilot",
    "paper-search-pro",
    "paper-qa",
    "OpenScholar",
    "asreview",
    "AutoSurvey",
    "gpt-researcher",
    "STORM",
    "open_deep_research",
    "Curie",
    "khoj",
    "gptr-mcp",
]

CLOSED_COMPETITORS = [
    "Elicit",
    "Consensus",
    "Scite",
    "ResearchRabbit",
    "Connected Papers",
    "Semantic Scholar",
    "NotebookLM",
]

CELL_STATES = frozenset({"领先", "持平", "落后", "不适用"})
```

```python
# evals/competitor_scorecard/validate.py
from __future__ import annotations

from schema import CELL_STATES, CLOSED_COMPETITORS, DIMENSIONS, OSS_COMPETITORS


def validate_scorecard(data: dict) -> list[str]:
    errors: list[str] = []
    comps = data.get("competitors")
    if not isinstance(comps, dict):
        return ["competitors must be an object"]

    expected = set(OSS_COMPETITORS) | set(CLOSED_COMPETITORS)
    missing = expected - set(comps)
    extra = set(comps) - expected
    if missing:
        errors.append(f"missing competitors: {sorted(missing)}")
    if extra:
        errors.append(f"unknown competitors: {sorted(extra)}")

    dim_ids = [d["id"] for d in DIMENSIONS]
    for name, row in comps.items():
        if not isinstance(row, dict):
            errors.append(f"{name}: row must be object")
            continue
        cells = row.get("cells")
        if not isinstance(cells, dict):
            errors.append(f"{name}: missing cells object")
            continue
        for did in dim_ids:
            cell = cells.get(did)
            if not isinstance(cell, dict):
                errors.append(f"{name}.{did}: missing cell")
                continue
            state = cell.get("state")
            if state not in CELL_STATES:
                errors.append(f"{name}.{did}: bad state {state!r}")
            note = cell.get("note")
            if not isinstance(note, str) or not note.strip():
                errors.append(f"{name}.{did}: note required")
            if name in CLOSED_COMPETITORS and cell.get("evidence") != "public-docs":
                errors.append(f"{name}.{did}: closed must evidence=public-docs")
    return errors
```

Stub `data.json` (intentionally incomplete so Step 4 still drives fill — but Step 3 can leave empty competitors `{}` so validate fails):

```json
{
  "version": 1,
  "as_of": "2026-09-15",
  "competitors": {}
}
```

- [ ] **Step 4: Run test — expect competitor completeness failure**

```powershell
python -m pytest evals/competitor_scorecard/test_scorecard.py::test_data_json_validates_complete -v
```

Expected: FAIL with `missing competitors: ...`

- [ ] **Step 5: Commit**

```powershell
git add evals/competitor_scorecard/schema.py evals/competitor_scorecard/validate.py evals/competitor_scorecard/test_scorecard.py evals/competitor_scorecard/data.json
git commit -m "test: add competitor scorecard schema and completeness harness"
```

---

### Task 2: Fill complete `data.json` for 18 OSS + 7 closed

**Files:**
- Modify: `evals/competitor_scorecard/data.json` (full matrix)
- Create: `evals/competitor_scorecard/render.py`
- Modify: `evals/competitor_scorecard/test_scorecard.py` (add render smoke test)

**Interfaces:**
- Consumes: `validate_scorecard`, `DIMENSIONS`, competitor name lists
- Produces: `render_scorecard(data: dict) -> str` (Markdown); writes `docs/COMPETITOR_SCORECARD.md`

**Scoring guidance (must follow when filling cells):**

Use Pass 5 + known CLIs as baseline for Paper_Rec:

| Dim | Paper_Rec today (evidence) | Typical `落后` vs |
|-----|----------------------------|------------------|
| `b_fig_vlm` | `fig-review` heuristic + prompt stub only | AI-Scientist-v2 |
| `b_parallel_deep` | `deep-research` tree serial | open_deep_research, gpt-researcher |
| `b_citation_trust` | none for retraction/OA-S2 conflict | paper-qa, paper-search-pro, Scite |
| `b_al_stop` | `screen-next` without real stoppers | asreview |
| `b_survey` | TF-IDF `survey-draft` | AutoSurvey |
| `b_novelty` | single-shot `novelty-check` | AI-Scientist |
| `c_drift_watch` | feedback unused for profile | PaperFlow pattern / ResearchRabbit |
| `c_wiki_filter` | parse-only | khoj |
| `b_hard_gate` | shipped hard-gate | often `领先` vs SaaS |
| `c_thread` / `c_local_audit` | Thread + git wiki + CLI | often `领先` vs closed SaaS |
| Full product OS dims | `不适用` vs Curie/AI-Scientist whole product | — |

For **AI-Researcher**: if clone empty, every cell `不适用` with note `clone empty / not scored` OR mark row `state` uniformly `不适用`.

Closed rows: every cell `evidence: "public-docs"` and a one-line public capability note (no login trials required).

- [ ] **Step 1: Extend test for render output headers**

```python
def test_render_contains_axes_and_closed_tag():
    from render import render_scorecard
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    md = render_scorecard(data)
    assert "Axis A" in md or "轴 A" in md or "## A" in md
    assert "Elicit" in md
    assert "public-docs" in md
    assert "落后" in md  # W0 must surface real gaps
```

- [ ] **Step 2: Run test — expect fail (empty data / no render)**

```powershell
python -m pytest evals/competitor_scorecard/test_scorecard.py -v
```

Expected: FAIL.

- [ ] **Step 3: Write `render.py`**

```python
# evals/competitor_scorecard/render.py
from __future__ import annotations

from pathlib import Path

from schema import CLOSED_COMPETITORS, DIMENSIONS, OSS_COMPETITORS


def render_scorecard(data: dict) -> str:
    lines = [
        "# Competitor Scorecard",
        "",
        f"As of: {data.get('as_of', '')}",
        "",
        "Cell = Paper_Rec relative to competitor: 领先 / 持平 / 落后 / 不适用.",
        "",
    ]
    for axis, title in (("A", "Retrieval & recommendation"), ("B", "Deep research & trust"), ("C", "Thread & workflow")):
        dims = [d for d in DIMENSIONS if d["axis"] == axis]
        lines.append(f"## {axis} — {title}")
        lines.append("")
        header = ["Competitor"] + [d["id"] for d in dims]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for name in list(OSS_COMPETITORS) + list(CLOSED_COMPETITORS):
            row = data["competitors"][name]
            cells = row["cells"]
            vals = [name] + [cells[d["id"]]["state"] for d in dims]
            lines.append("| " + " | ".join(vals) + " |")
        lines.append("")
    lines.append("## Notes (selected gaps)")
    lines.append("")
    for name in list(OSS_COMPETITORS) + list(CLOSED_COMPETITORS):
        row = data["competitors"][name]
        for did, cell in row["cells"].items():
            if cell["state"] == "落后":
                ev = cell.get("evidence", "code")
                lines.append(f"- **{name} / {did}**: {cell['note']} `({ev})`")
    lines.append("")
    return "\n".join(lines)


def write_docs(repo_root: Path, data: dict) -> Path:
    out = repo_root / "docs" / "COMPETITOR_SCORECARD.md"
    out.write_text(render_scorecard(data), encoding="utf-8")
    return out
```

- [ ] **Step 4: Fill `data.json` completely**

Create full JSON with all 25 competitors × 20 dimensions. Minimum content pattern per cell:

```json
"AutoResearchClaw": {
  "kind": "oss",
  "cells": {
    "a_multi_source": {"state": "持平", "note": "Both retrieve multi-source; Paper_Rec skill+CLI.", "evidence": "code"},
    "b_hard_gate": {"state": "持平", "note": "Paper_Rec number-verify --hard-gate vs VerifiedRegistry.", "evidence": "code"},
    "b_fig_vlm": {"state": "落后", "note": "ARC/AI-Scientist-v2 class VLM deeper than fig-review stub.", "evidence": "code"},
    "c_local_audit": {"state": "领先", "note": "Git wiki + thread ledger more auditable for lit workflow.", "evidence": "code"}
  }
}
```

Every dimension id from `DIMENSIONS` must appear. For dimensions not illustrated above, still set an explicit state+note (use `不适用` when comparing whole auto-paper OS phases that Paper_Rec deliberately skips).

Closed example:

```json
"Scite": {
  "kind": "closed",
  "cells": {
    "b_citation_trust": {
      "state": "落后",
      "note": "Scite smart citations / retraction UX; Paper_Rec lacks retraction+conflict engine.",
      "evidence": "public-docs"
    },
    "c_local_audit": {
      "state": "领先",
      "note": "Local CLI+git artifacts vs SaaS-only audit trail.",
      "evidence": "public-docs"
    }
  }
}
```

After filling, run validate until zero errors, then:

```powershell
python -c "import json; from pathlib import Path; import sys; sys.path.insert(0,'evals/competitor_scorecard'); from validate import validate_scorecard; from render import write_docs; root=Path('.'); data=json.loads((root/'evals/competitor_scorecard/data.json').read_text(encoding='utf-8')); e=validate_scorecard(data); assert not e, e; print(write_docs(root, data))"
```

- [ ] **Step 5: Run tests — expect PASS**

```powershell
python -m pytest evals/competitor_scorecard/test_scorecard.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add evals/competitor_scorecard/data.json evals/competitor_scorecard/render.py evals/competitor_scorecard/test_scorecard.py docs/COMPETITOR_SCORECARD.md
git commit -m "docs: add full competitor scorecard matrix for 18 OSS and 7 closed products"
```

---

### Task 3: Write `docs/GAP_PRIORITY.md` from scorecard `落后` cells

**Files:**
- Create: `docs/GAP_PRIORITY.md`
- Create: `evals/competitor_scorecard/derive_gaps.py`
- Create: `evals/competitor_scorecard/test_derive_gaps.py`

**Interfaces:**
- Consumes: `data.json` cells where `state == "落后"`
- Produces: `derive_gaps(data: dict) -> list[dict]` each with keys:
  - `id: str`
  - `severity: str` (`Critical`|`High`|`Medium`)
  - `dimension: str`
  - `competitors: list[str]`
  - `target_cli: str`
  - `wave: str` (`W1`|`W2`|`W3`)
  - `rationale: str`

**Severity rules (encode in `derive_gaps`):**

| dimension id | default severity | default wave | target_cli |
|--------------|------------------|--------------|------------|
| `b_fig_vlm` | Critical | W1 | `fig-review` |
| `b_parallel_deep` | Critical | W1 | `deep-research` |
| `b_citation_trust` | Critical | W1 | new `trust-meta` (planned) |
| `b_al_stop` | Critical | W1 | `screen-next` |
| `b_survey` | High | W2 | `survey-draft` |
| `b_novelty` | High | W2 | `novelty-check` |
| `c_drift_watch` | High | W2 | `thread-delta` / feedback |
| `c_wiki_filter` | High | W2 | `wiki-filter-parse` → apply |
| `a_*` gaps | High/Medium | W2/W3 | matching retrieve CLIs |
| other | Medium | W3 | per note |

- [ ] **Step 1: Write failing test**

```python
# evals/competitor_scorecard/test_derive_gaps.py
import json
from pathlib import Path

from derive_gaps import derive_gaps, render_gap_markdown

HERE = Path(__file__).resolve().parent


def test_derive_includes_pass5_criticals():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    gaps = derive_gaps(data)
    dims = {g["dimension"] for g in gaps}
    for must in ("b_fig_vlm", "b_parallel_deep", "b_citation_trust", "b_al_stop"):
        assert must in dims, must
    assert any(g["severity"] == "Critical" and g["wave"] == "W1" for g in gaps)


def test_render_gap_markdown_has_table():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    md = render_gap_markdown(derive_gaps(data))
    assert "| Critical |" in md or "|Critical|" in md.replace(" ", "")
    assert "fig-review" in md
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest evals/competitor_scorecard/test_derive_gaps.py -v
```

- [ ] **Step 3: Implement `derive_gaps.py` and write `docs/GAP_PRIORITY.md`**

```python
# evals/competitor_scorecard/derive_gaps.py
from __future__ import annotations

from collections import defaultdict

_RULES = {
    "b_fig_vlm": ("Critical", "W1", "fig-review"),
    "b_parallel_deep": ("Critical", "W1", "deep-research"),
    "b_citation_trust": ("Critical", "W1", "trust-meta"),
    "b_al_stop": ("Critical", "W1", "screen-next"),
    "b_survey": ("High", "W2", "survey-draft"),
    "b_novelty": ("High", "W2", "novelty-check"),
    "c_drift_watch": ("High", "W2", "thread-delta"),
    "c_wiki_filter": ("High", "W2", "wiki-filter-apply"),
}


def derive_gaps(data: dict) -> list[dict]:
    by_dim: dict[str, list[str]] = defaultdict(list)
    notes: dict[str, str] = {}
    for name, row in data["competitors"].items():
        for did, cell in row["cells"].items():
            if cell.get("state") == "落后":
                by_dim[did].append(name)
                notes.setdefault(did, cell.get("note", ""))
    gaps = []
    for did, comps in sorted(by_dim.items()):
        sev, wave, cli = _RULES.get(did, ("Medium", "W3", "tbd-cli"))
        if cli == "tbd-cli":
            cli = did.replace("_", "-")
        gaps.append(
            {
                "id": f"gap-{did}",
                "severity": sev,
                "dimension": did,
                "competitors": comps,
                "target_cli": cli,
                "wave": wave,
                "rationale": notes.get(did, ""),
            }
        )
    order = {"Critical": 0, "High": 1, "Medium": 2}
    gaps.sort(key=lambda g: (order.get(g["severity"], 9), g["dimension"]))
    return gaps


def render_gap_markdown(gaps: list[dict]) -> str:
    lines = [
        "# Gap Priority",
        "",
        "Derived from `evals/competitor_scorecard/data.json` cells with state `落后`.",
        "",
        "| Severity | Dimension | Wave | Target CLI | Competitors | Rationale |",
        "|----------|-----------|------|------------|-------------|-----------|",
    ]
    for g in gaps:
        comps = ", ".join(g["competitors"][:6])
        if len(g["competitors"]) > 6:
            comps += ", …"
        rat = g["rationale"].replace("|", "/")
        lines.append(
            f"| {g['severity']} | {g['dimension']} | {g['wave']} | `{g['target_cli']}` | {comps} | {rat} |"
        )
    lines.append("")
    lines.append("## Wave mapping")
    lines.append("")
    lines.append("- **W1:** Critical trust/depth engines only.")
    lines.append("- **W2:** High coverage + thread.")
    lines.append("- **W3:** Medium polish + prove narrative.")
    lines.append("")
    lines.append("SP1+ plans must not start until this file exists and Critical rows are acknowledged.")
    lines.append("")
    return "\n".join(lines)
```

Then write docs:

```powershell
python -c "import json,sys; from pathlib import Path; sys.path.insert(0,'evals/competitor_scorecard'); from derive_gaps import derive_gaps, render_gap_markdown; data=json.loads(Path('evals/competitor_scorecard/data.json').read_text(encoding='utf-8')); Path('docs/GAP_PRIORITY.md').write_text(render_gap_markdown(derive_gaps(data)), encoding='utf-8')"
```

- [ ] **Step 4: Run tests — PASS**

```powershell
python -m pytest evals/competitor_scorecard/test_derive_gaps.py -v
```

- [ ] **Step 5: Commit**

```powershell
git add evals/competitor_scorecard/derive_gaps.py evals/competitor_scorecard/test_derive_gaps.py docs/GAP_PRIORITY.md
git commit -m "docs: derive gap priority table from competitor scorecard lagging cells"
```

---

### Task 4: Gold-set harness skeleton (4 case families)

**Files:**
- Create: `evals/goldset/README.md`
- Create: `evals/goldset/cases/retrieval_rerank.json`
- Create: `evals/goldset/cases/citation_fidelity.json`
- Create: `evals/goldset/cases/screening_stop.json`
- Create: `evals/goldset/cases/hard_gate_block.json`
- Create: `evals/goldset/run_goldset.py`
- Create: `evals/goldset/test_run_goldset.py`

**Interfaces:**
- Consumes: wiki-bridge functions already shipped:
  - `wiki_bridge.number_verify` / `verified_registry.hard_gate` (import path as in `tests/test_pass4_p0.py`)
  - `wiki_bridge.screen_next` (screening batch helper — use consecutive-irrelevant heuristic stub in runner until W1 stoppers land)
  - `wiki_bridge.feedback_edit.critique_answer` for citation fidelity smoke
  - `wiki_bridge.prerank.prerank` or simple BM25 via `litsearch_eval.recall_at_k` for retrieval
- Produces: `run_all(cases_dir: Path) -> dict` with `passed`, `failed`, `results: list`

**Case JSON schema:**

```json
{
  "id": "hard_gate_block_fabricated",
  "family": "hard_gate",
  "expect": "blocked",
  "metrics": {"accuracy": 0.91},
  "prose": "# Results\n\nWe achieve accuracy 99.9 on the test set.\n"
}
```

- [ ] **Step 1: Write failing test**

```python
# evals/goldset/test_run_goldset.py
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "wiki-bridge"))

from run_goldset import run_all

HERE = Path(__file__).resolve().parent


def test_goldset_all_pass():
    summary = run_all(HERE / "cases")
    assert summary["failed"] == [], summary
    assert summary["passed"] >= 4
```

- [ ] **Step 2: Run — expect FAIL (no module)**

```powershell
python -m pytest evals/goldset/test_run_goldset.py -v
```

- [ ] **Step 3: Add four case files**

`evals/goldset/cases/hard_gate_block.json`:

```json
{
  "id": "hard_gate_block_fabricated",
  "family": "hard_gate",
  "expect": "blocked",
  "metrics": {"accuracy": 0.91},
  "prose": "# Results\n\nWe achieve accuracy 99.9 on the test set.\n"
}
```

`evals/goldset/cases/hard_gate_allow.json`:

```json
{
  "id": "hard_gate_allow_registry",
  "family": "hard_gate",
  "expect": "allowed",
  "metrics": {"accuracy": 0.91},
  "prose": "# Results\n\nWe achieve accuracy 0.91 on the test set.\n"
}
```

`evals/goldset/cases/citation_fidelity.json`:

```json
{
  "id": "citation_flags_uncited_claim",
  "family": "citation_fidelity",
  "query": "RAG evaluation",
  "answer": "Studies show retrieval improves generation quality substantially.",
  "evidence": [{"eid": "E1", "quote": "Retrieval improves generation on QA tasks."}],
  "expect_feedback_substring": "citation"
}
```

`evals/goldset/cases/retrieval_rerank.json`:

```json
{
  "id": "retrieval_gold_in_top5",
  "family": "retrieval",
  "query": "dense retrieval transformers ranking",
  "docs": [
    {"id": "g1", "title": "Dense Passage Retrieval", "abstract": "Dense retrieval with transformers for ranking."},
    {"id": "n1", "title": "Pasta recipes", "abstract": "Tomato sauce and noodles cooking tips."},
    {"id": "n2", "title": "Weather models", "abstract": "Atmospheric pressure forecasting methods."},
    {"id": "g2", "title": "ColBERT late interaction", "abstract": "Efficient transformer ranking retrieval."},
    {"id": "n3", "title": "Basketball stats", "abstract": "Player efficiency ratings over seasons."}
  ],
  "gold_ids": ["g1", "g2"],
  "k": 5,
  "min_recall": 1.0
}
```

`evals/goldset/cases/screening_stop.json`:

```json
{
  "id": "screening_stop_after_n_irrelevant",
  "family": "screening_stop",
  "n_consecutive_irrelevant": 3,
  "labels": ["irrelevant", "irrelevant", "irrelevant"],
  "expect_stop": true
}
```

Note: W0 runner implements a **local stopper helper** inside `run_goldset.py` (not production `screen-next`) so the case is runnable before W1:

```python
def should_stop(labels: list[str], n: int) -> bool:
    if len(labels) < n:
        return False
    return all(x == "irrelevant" for x in labels[-n:])
```

- [ ] **Step 4: Implement `run_goldset.py`**

```python
# evals/goldset/run_goldset.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "wiki-bridge"))

from wiki_bridge.feedback_edit import critique_answer
from wiki_bridge.litsearch_eval import recall_at_k
from wiki_bridge.prerank import prerank
from wiki_bridge.verified_registry import hard_gate


def should_stop(labels: list[str], n: int) -> bool:
    if len(labels) < n:
        return False
    return all(x == "irrelevant" for x in labels[-n:])


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    fam = case["family"]
    cid = case["id"]
    if fam == "hard_gate":
        # verified_registry expects dict[float, str] (value → metric name)
        reg = {float(v): str(k) for k, v in case["metrics"].items()}
        gate = hard_gate(case["prose"], reg)
        blocked = bool(gate.get("blocked"))
        ok = (case["expect"] == "blocked" and blocked) or (case["expect"] == "allowed" and not blocked)
        return {"id": cid, "ok": ok, "detail": gate}
    if fam == "citation_fidelity":
        fbs = critique_answer(case["query"], case["answer"], case["evidence"])
        blob = " ".join(str(f.get("feedback", "")) for f in fbs).lower()
        ok = case["expect_feedback_substring"].lower() in blob
        return {"id": cid, "ok": ok, "detail": {"feedback_n": len(fbs)}}
    if fam == "retrieval":
        # prerank() returns {"items": [...]} not a bare list
        out = prerank(case["query"], case["docs"], top_k=int(case["k"]), use_citations=False)
        ids = [str(d.get("id") or d.get("title")) for d in out.get("items") or []]
        rec = recall_at_k(ids, set(case["gold_ids"]), int(case["k"]))
        ok = rec >= float(case["min_recall"])
        return {"id": cid, "ok": ok, "detail": {"recall": rec, "ids": ids}}
    if fam == "screening_stop":
        stopped = should_stop(case["labels"], int(case["n_consecutive_irrelevant"]))
        ok = stopped == bool(case["expect_stop"])
        return {"id": cid, "ok": ok, "detail": {"stopped": stopped}}
    return {"id": cid, "ok": False, "detail": {"error": f"unknown family {fam}"}}


def run_all(cases_dir: Path) -> dict[str, Any]:
    results = []
    for path in sorted(cases_dir.glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        results.append(run_case(case))
    failed = [r for r in results if not r["ok"]]
    passed = [r for r in results if r["ok"]]
    return {"passed": len(passed), "failed": failed, "results": results}


def main() -> int:
    summary = run_all(Path(__file__).resolve().parent / "cases")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

If `prerank` signature differs, adjust call to match `wiki_bridge/prerank.py` (read file before coding; keep offline list-in/list-out).

`README.md` must document:

```markdown
# Gold-set

Offline regression cases for competitor-exceed gates.

## Run

```powershell
python evals/goldset/run_goldset.py
python -m pytest evals/goldset/test_run_goldset.py -v
```

## Families

- `hard_gate` — fabricated metrics blocked
- `citation_fidelity` — uncited claims flagged
- `retrieval` — gold docs in top-k after prerank
- `screening_stop` — N-consecutive irrelevant stops (harness helper until W1)

W0 does not claim beating closed-source SaaS; it locks the gate machinery.
```

- [ ] **Step 5: Fix prerank/hard_gate import mismatches if tests fail; re-run until PASS**

```powershell
python evals/goldset/run_goldset.py
python -m pytest evals/goldset/test_run_goldset.py -v
```

Expected: exit 0 / PASS. If `load_registry` unused, remove import. If `prerank` API differs, open `packages/wiki-bridge/wiki_bridge/prerank.py` and adapt ranking to return docs with `id` preserved.

- [ ] **Step 6: Commit**

```powershell
git add evals/goldset
git commit -m "test: add offline gold-set harness for hard-gate citation retrieval screening"
```

---

### Task 5: Pass 6 learn-log pointer + SP0 done checklist

**Files:**
- Modify: `docs/COMPETITOR_LEARN_LOG.md` (append Pass 6)
- Create: `docs/superpowers/specs/2026-09-15-competitor-exceed-scorecard-design.md` already exists — do not rewrite; only link from Pass 6

- [ ] **Step 1: Append Pass 6 section** at end of `COMPETITOR_LEARN_LOG.md`:

```markdown
## Pass 6 — Scorecard-first exceed program (2026-09-15)

Spec: `docs/superpowers/specs/2026-09-15-competitor-exceed-scorecard-design.md`  
Plan (W0): `docs/superpowers/plans/2026-09-15-competitor-exceed-w0-scorecard.md`

| Artifact | Path |
|----------|------|
| Scorecard | `docs/COMPETITOR_SCORECARD.md` (source: `evals/competitor_scorecard/data.json`) |
| Gaps | `docs/GAP_PRIORITY.md` |
| Gold-set | `evals/goldset/` |

### SP0 exit criteria

- [x] 18 OSS + ≥5 closed scored
- [x] Critical lags listed for W1
- [x] Gold-set runner green on skeleton cases
- [ ] W1 engines not started in SP0 (explicit)

Do **not** market “全方位超过” until W1 Critical clear + gold-set wave gate.
```

- [ ] **Step 2: Verify all SP0 gates locally**

```powershell
python -m pytest evals/competitor_scorecard evals/goldset -v
python evals/goldset/run_goldset.py
Test-Path docs/COMPETITOR_SCORECARD.md
Test-Path docs/GAP_PRIORITY.md
```

Expected: pytest PASS; goldset exit 0; both docs exist.

- [ ] **Step 3: Commit**

```powershell
git add docs/COMPETITOR_LEARN_LOG.md
git commit -m "docs: add Pass 6 scorecard-first competitor exceed entry"
```

---

## Spec coverage checklist (plan self-review)

| Spec requirement | Task |
|------------------|------|
| `COMPETITOR_SCORECARD.md` 18 OSS + ≥5 closed | Task 2 |
| Cell states + evidence rules | Task 1–2 |
| `GAP_PRIORITY.md` Critical→wave | Task 3 |
| `evals/goldset/` runnable skeleton | Task 4 |
| Pass 6 in learn log | Task 5 |
| No W1–W3 engine impl in SP0 | All tasks (enforced by scope) |
| Non-goals / `不适用` | Task 2 scoring guidance |
| Closed `public-docs` only | Task 1 validate + Task 2 |

No TBD placeholders remain. `trust-meta` / `wiki-filter-apply` appear only as **target_cli names in gap table** for later waves, not implemented here.

---

## Execution handoff

After this plan is saved, choose how to execute W0 tasks.
