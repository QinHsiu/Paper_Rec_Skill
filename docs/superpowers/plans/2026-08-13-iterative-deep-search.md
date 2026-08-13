# Iterative Deep Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `/query_*` from a one-shot keyword search into a Search → Read → Reason loop that expands follow-up questions until depth is exhausted or information is judged sufficient, then emit a reasoning-chain report (not just a paper list).

**Architecture:** Keep the existing offline tree planner (`wiki_bridge/deep_research.py`) unchanged. Add a **live loop engine** in `wiki_bridge/deep_search.py` with injectable `Searcher` and `Reasoner` protocols so unit tests never hit the network or an LLM. A thin CLI lives in both `python -m wiki_bridge.cli deep-search` and `skill/scripts/deep_search.py` (spec path). The Skill Markdown tells the agent to parse `--breadth` / `--depth` and call that CLI (or run the same loop in-process when a searcher is available).

**Tech Stack:** Python 3.10+, stdlib only in wiki-bridge core, existing arXiv Atom API (`export.arxiv.org/api/query`), existing `extract_learnings` / `followups_from_learnings` / `reflect_coverage` / `append_query_iter`.

## Global Constraints

- Python `>= 3.10`.
- `packages/wiki-bridge` core stays **stdlib-only** (no new required dependencies in `pyproject.toml`).
- Unit tests must not call live arXiv / Semantic Scholar / OpenAlex / any LLM. Inject `FakeSearcher` / `HeuristicReasoner` (or a stub Reasoner).
- Do not delete or change the behavior of `build_deep_research_plan` (offline tree used by `/wiki deep-research` today).
- CLI entry remains `python -m wiki_bridge.cli`.
- Do not commit AppID / AppSecret / API keys. Example commands use `<AppID>`-style placeholders only.
- Test style matches `packages/wiki-bridge/tests/test_arxiv_watch.py`: `test_*` functions plus `if __name__ == "__main__"` runner.
- Default `--breadth 3`, `--depth 2` (maps spec `--depth` to code `max_depth`).
- Dedup papers by normalized arXiv id, else DOI, else lowercased title.

---

## File structure

| File | Responsibility |
|------|----------------|
| `packages/wiki-bridge/wiki_bridge/deep_search.py` | Live loop: types, Searcher/Reasoner protocols, HeuristicReasoner, ArxivQuerySearcher, `run_deep_search`, report render |
| `packages/wiki-bridge/tests/test_deep_search.py` | Offline tests for loop, stop conditions, dedup, persist, mocked arXiv |
| `packages/wiki-bridge/wiki_bridge/cli.py` | New subcommand `deep-search` (distinct from existing `deep-research`) |
| `skill/scripts/deep_search.py` | Thin argparse wrapper that imports `wiki_bridge.deep_search` + CLI |
| `skill/SKILL.md` | `/query_* --breadth --depth` and `/wiki deep-search` instructions |
| `skill/examples.md` | One usage example |
| `skill/CHANGELOG.md`, `CHANGELOG.md`, `docs/THREAD_DESIGN.md` | Version notes |

Existing files to **reuse, not rewrite:** `deep_research.py`, `reflect_search.py`, `thread_store.append_query_iter` / `append_query_trace`, `arxiv_watch.parse_atom_feed`, `rrf.normalize_arxiv_id`.

---

### Task 1: PaperHit + FakeSearcher + one search round with dedup

**Files:**
- Create: `packages/wiki-bridge/wiki_bridge/deep_search.py`
- Test: `packages/wiki-bridge/tests/test_deep_search.py`

**Interfaces:**
- Consumes: nothing new
- Produces:
  - `PaperHit` TypedDict with keys `title: str`, `abstract: str`, `arxiv: str`, `doi: str`, `year: str`, `source_query: str`, `url: str`
  - `paper_id(hit: dict[str, Any]) -> str`
  - `Searcher` Protocol: `def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]`
  - `search_round(searcher, queries, *, seen_ids: set[str], limit_per_query: int) -> tuple[list[dict[str, Any]], set[str]]`

- [ ] **Step 1: Write the failing test**

```python
# packages/wiki-bridge/tests/test_deep_search.py
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.deep_search import FakeSearcher, paper_id, search_round


def test_paper_id_prefers_arxiv_then_doi_then_title():
    assert paper_id({"arxiv": "2204.10254v2", "title": "X"}) == "arxiv:2204.10254"
    assert paper_id({"doi": "10.5555/X", "title": "X"}) == "doi:10.5555/x"
    assert paper_id({"title": "Hello World"}) == "title:hello world"


def test_search_round_dedups_across_queries():
    searcher = FakeSearcher(
        {
            "q1": [{"title": "A", "arxiv": "1111.11111", "abstract": "a"}],
            "q2": [
                {"title": "A again", "arxiv": "1111.11111v3", "abstract": "a"},
                {"title": "B", "arxiv": "2222.22222", "abstract": "b"},
            ],
        }
    )
    hits, seen = search_round(searcher, ["q1", "q2"], seen_ids=set(), limit_per_query=8)
    ids = {paper_id(h) for h in hits}
    assert ids == {"arxiv:1111.11111", "arxiv:2222.22222"}
    assert "arxiv:1111.11111" in seen
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: FAIL with `ModuleNotFoundError: wiki_bridge.deep_search` or `cannot import name 'FakeSearcher'`.

- [ ] **Step 3: Write minimal implementation**

In `packages/wiki-bridge/wiki_bridge/deep_search.py`:

```python
"""Live Search → Read → Reason loop (injectable Searcher / Reasoner)."""
from __future__ import annotations

from typing import Any, Protocol

from .rrf import normalize_arxiv_id


def paper_id(hit: dict[str, Any]) -> str:
    arxiv = normalize_arxiv_id(str(hit.get("arxiv") or hit.get("id") or ""))
    if arxiv:
        return f"arxiv:{arxiv}"
    doi = str(hit.get("doi") or "").strip().lower().removeprefix("https://doi.org/")
    if doi:
        return f"doi:{doi}"
    title = " ".join(str(hit.get("title") or "").split()).lower()
    return f"title:{title}" if title else "title:"


class Searcher(Protocol):
    def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]: ...


class FakeSearcher:
    def __init__(self, table: dict[str, list[dict[str, Any]]]):
        self.table = table
        self.calls: list[str] = []

    def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        self.calls.append(query)
        rows = list(self.table.get(query) or [])
        return rows[:limit]


def _normalize_hit(hit: dict[str, Any], *, source_query: str) -> dict[str, Any]:
    out = dict(hit)
    out["title"] = str(hit.get("title") or "").strip()
    out["abstract"] = str(hit.get("abstract") or hit.get("summary") or "").strip()
    out["arxiv"] = normalize_arxiv_id(str(hit.get("arxiv") or ""))
    out["doi"] = str(hit.get("doi") or "").strip()
    out["year"] = str(hit.get("year") or (hit.get("published") or "")[:4])
    out["url"] = str(hit.get("url") or hit.get("paper_link") or "")
    out["source_query"] = source_query
    return out


def search_round(
    searcher: Searcher,
    queries: list[str],
    *,
    seen_ids: set[str] | None = None,
    limit_per_query: int = 8,
) -> tuple[list[dict[str, Any]], set[str]]:
    seen = set(seen_ids or [])
    new_hits: list[dict[str, Any]] = []
    for q in queries:
        q = (q or "").strip()
        if not q:
            continue
        for raw in searcher.search(q, limit=limit_per_query) or []:
            if not isinstance(raw, dict):
                continue
            hit = _normalize_hit(raw, source_query=q)
            pid = paper_id(hit)
            if not hit["title"] or pid in seen:
                continue
            seen.add(pid)
            new_hits.append(hit)
    return new_hits, seen
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: `OK` (add `if __name__ == "__main__"` that calls the two tests and prints `OK deep_search`).

- [ ] **Step 5: Commit**

```bash
git add packages/wiki-bridge/wiki_bridge/deep_search.py packages/wiki-bridge/tests/test_deep_search.py
git commit -m "feat: add injectable search round with paper-id dedup"
```

---

### Task 2: HeuristicReasoner — learnings, follow-ups, sufficient flag

**Files:**
- Modify: `packages/wiki-bridge/wiki_bridge/deep_search.py`
- Test: `packages/wiki-bridge/tests/test_deep_search.py`

**Interfaces:**
- Consumes: `extract_learnings`, `followups_from_learnings` from `wiki_bridge.deep_research`; `reflect_coverage` from `wiki_bridge.reflect_search`
- Produces:
  - `ReasonResult` dict: `learnings: list[dict]`, `followups: list[str]`, `sufficient: bool`, `coverage: dict`
  - `Reasoner` Protocol: `def reason(self, topic: str, round_papers: list[dict], all_learnings: list[dict], *, breadth: int, round_index: int, max_depth: int) -> dict[str, Any]`
  - `HeuristicReasoner.reason(...)` — no LLM
  - `clip_followups(followups: list[str], *, breadth: int) -> list[str]` — first `breadth` unique non-empty strings

`sufficient` is True when **any** of: (1) `round_index >= max_depth`; (2) `len(round_papers) == 0`; (3) `not followups`; (4) `coverage["should_retry"] is False` **and** `len(all_learnings) + len(round_papers) >= 8`.

- [ ] **Step 1: Write the failing test**

```python
from wiki_bridge.deep_search import HeuristicReasoner, clip_followups


def test_clip_followups_honors_breadth():
    qs = ["a", "b", "a", "", "c", "d"]
    assert clip_followups(qs, breadth=2) == ["a", "b"]


def test_heuristic_reasoner_emits_learnings_and_followups():
    papers = [
        {"title": "RAG limits", "abstract": "Retrieval augmented generation fails on long context."},
        {"title": "FiD", "abstract": "Fusion-in-Decoder improves open-domain QA."},
    ]
    r = HeuristicReasoner()
    out = r.reason(
        "RAG evaluation",
        papers,
        [],
        breadth=2,
        round_index=1,
        max_depth=3,
    )
    assert out["learnings"]
    assert out["followups"]
    assert out["sufficient"] is False


def test_heuristic_reasoner_sufficient_at_max_depth():
    r = HeuristicReasoner()
    out = r.reason("t", [{"title": "A", "abstract": "x"}], [], breadth=2, round_index=2, max_depth=2)
    assert out["sufficient"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: FAIL with `cannot import name 'HeuristicReasoner'`.

- [ ] **Step 3: Write minimal implementation**

Append to `deep_search.py`:

```python
from .deep_research import extract_learnings, followups_from_learnings
from .reflect_search import reflect_coverage


def clip_followups(followups: list[str], *, breadth: int) -> list[str]:
    out: list[str] = []
    for q in followups or []:
        q = str(q or "").strip()
        if q and q not in out:
            out.append(q)
        if len(out) >= max(1, breadth):
            break
    return out


class Reasoner(Protocol):
    def reason(
        self,
        topic: str,
        round_papers: list[dict[str, Any]],
        all_learnings: list[dict[str, Any]],
        *,
        breadth: int,
        round_index: int,
        max_depth: int,
    ) -> dict[str, Any]: ...


class HeuristicReasoner:
    def reason(
        self,
        topic: str,
        round_papers: list[dict[str, Any]],
        all_learnings: list[dict[str, Any]],
        *,
        breadth: int,
        round_index: int,
        max_depth: int,
    ) -> dict[str, Any]:
        learnings = extract_learnings(round_papers, max_items=max(4, breadth * 2))
        coverage = reflect_coverage(round_papers, query=topic)
        followups = followups_from_learnings(learnings, topic, breadth=breadth)
        for q in coverage.get("improved_queries") or []:
            if q not in followups:
                followups.append(q)
        followups = clip_followups(followups, breadth=breadth)
        known_n = len(all_learnings) + len(round_papers)
        sufficient = (
            round_index >= max_depth
            or not round_papers
            or not followups
            or (not coverage.get("should_retry") and known_n >= 8)
        )
        return {
            "learnings": learnings,
            "followups": followups,
            "sufficient": sufficient,
            "coverage": {k: coverage[k] for k in ("issues", "should_retry", "paper_count") if k in coverage},
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/wiki-bridge/wiki_bridge/deep_search.py packages/wiki-bridge/tests/test_deep_search.py
git commit -m "feat: add heuristic reasoner for deep-search follow-ups"
```

---

### Task 3: `run_deep_search` loop — Search → Read → Reason with stop conditions

**Files:**
- Modify: `packages/wiki-bridge/wiki_bridge/deep_search.py`
- Test: `packages/wiki-bridge/tests/test_deep_search.py`

**Interfaces:**
- Consumes: `search_round`, `HeuristicReasoner`, `clip_followups`
- Produces: `run_deep_search(topic: str, *, searcher: Searcher, reasoner: Reasoner | None = None, breadth: int = 3, max_depth: int = 2, limit_per_query: int = 8) -> dict[str, Any]`

Return dict keys (locked):

```python
{
  "topic": str,
  "breadth": int,
  "max_depth": int,
  "stop_reason": str,  # "max_depth" | "sufficient" | "no_new_papers" | "no_followups"
  "rounds": [
    {
      "round": int,           # 1-based
      "queries": list[str],
      "hits": list[dict],     # new papers this round
      "learnings": list[dict],
      "followups": list[str],
      "sufficient": bool,
    }
  ],
  "papers": list[dict],       # all unique hits in discovery order
  "learnings": list[dict],    # concatenated
  "followups": list[str],     # last round's unused follow-ups
}
```

Loop:

1. `queries = [topic]`; `seen = set()`; `all_papers = []`; `all_learnings = []`
2. For `round_index` in `1 .. max_depth`:
   - `hits, seen = search_round(...)`
   - If no hits: `stop_reason = "no_new_papers"`; break
   - Read: hits already carry `title`/`abstract` from `_normalize_hit`
   - `result = reasoner.reason(topic, hits, all_learnings, breadth=breadth, round_index=round_index, max_depth=max_depth)`
   - append round record; extend papers/learnings
   - If `result["sufficient"]`: `stop_reason = "max_depth"` if `round_index >= max_depth` else `"sufficient"`; break
   - `queries = result["followups"]`
   - If not queries: `stop_reason = "no_followups"`; break
3. If the for-loop finishes without break: `stop_reason = "max_depth"`

- [ ] **Step 1: Write the failing test**

```python
from wiki_bridge.deep_search import FakeSearcher, HeuristicReasoner, run_deep_search


def test_run_deep_search_two_rounds_then_max_depth():
    searcher = FakeSearcher(
        {
            "RAG": [{"title": "P1", "abstract": "retrieval augmented generation", "arxiv": "1111.00001"}],
            "RAG related to: P1": [{"title": "P2", "abstract": "limitations of RAG", "arxiv": "1111.00002"}],
        }
    )
    out = run_deep_search("RAG", searcher=searcher, reasoner=HeuristicReasoner(), breadth=1, max_depth=2)
    assert out["stop_reason"] in {"max_depth", "sufficient", "no_followups", "no_new_papers"}
    assert len(out["rounds"]) >= 1
    assert out["rounds"][0]["queries"] == ["RAG"]
    assert any(p["title"] == "P1" for p in out["papers"])


def test_run_deep_search_stops_when_no_new_papers():
    searcher = FakeSearcher({"lonely": []})
    out = run_deep_search("lonely", searcher=searcher, reasoner=HeuristicReasoner(), breadth=2, max_depth=3)
    assert out["stop_reason"] == "no_new_papers"
    assert out["rounds"] == [] or out["papers"] == []


class _AlwaysEnough:
    def reason(self, topic, round_papers, all_learnings, *, breadth, round_index, max_depth):
        return {"learnings": [{"learning": "enough", "citation": "x"}], "followups": ["more"], "sufficient": True, "coverage": {}}


def test_run_deep_search_stops_when_reasoner_says_sufficient():
    searcher = FakeSearcher(
        {"t": [{"title": "Only", "abstract": "one paper", "arxiv": "3333.00001"}]}
    )
    out = run_deep_search("t", searcher=searcher, reasoner=_AlwaysEnough(), breadth=2, max_depth=5)
    assert out["stop_reason"] == "sufficient"
    assert len(out["rounds"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: FAIL with `cannot import name 'run_deep_search'`.

- [ ] **Step 3: Write minimal implementation**

```python
def run_deep_search(
    topic: str,
    *,
    searcher: Searcher,
    reasoner: Reasoner | None = None,
    breadth: int = 3,
    max_depth: int = 2,
    limit_per_query: int = 8,
) -> dict[str, Any]:
    reasoner = reasoner or HeuristicReasoner()
    breadth = max(1, int(breadth))
    max_depth = max(1, int(max_depth))
    queries = [str(topic).strip()]
    seen: set[str] = set()
    all_papers: list[dict[str, Any]] = []
    all_learnings: list[dict[str, Any]] = []
    rounds: list[dict[str, Any]] = []
    stop_reason = "max_depth"
    last_followups: list[str] = []

    for round_index in range(1, max_depth + 1):
        hits, seen = search_round(
            searcher, queries, seen_ids=seen, limit_per_query=limit_per_query
        )
        if not hits:
            stop_reason = "no_new_papers"
            break
        result = reasoner.reason(
            topic,
            hits,
            all_learnings,
            breadth=breadth,
            round_index=round_index,
            max_depth=max_depth,
        )
        all_papers.extend(hits)
        all_learnings.extend(result.get("learnings") or [])
        last_followups = list(result.get("followups") or [])
        rounds.append(
            {
                "round": round_index,
                "queries": list(queries),
                "hits": hits,
                "learnings": result.get("learnings") or [],
                "followups": last_followups,
                "sufficient": bool(result.get("sufficient")),
            }
        )
        if result.get("sufficient"):
            stop_reason = "max_depth" if round_index >= max_depth else "sufficient"
            break
        queries = last_followups
        if not queries:
            stop_reason = "no_followups"
            break
    else:
        stop_reason = "max_depth"

    return {
        "topic": topic,
        "breadth": breadth,
        "max_depth": max_depth,
        "stop_reason": stop_reason,
        "rounds": rounds,
        "papers": all_papers,
        "learnings": all_learnings,
        "followups": last_followups,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/wiki-bridge/wiki_bridge/deep_search.py packages/wiki-bridge/tests/test_deep_search.py
git commit -m "feat: run Search-Read-Reason loop with depth and sufficiency stops"
```

---

### Task 4: Persist reasoning-chain report + `query_iter` ledger

**Files:**
- Modify: `packages/wiki-bridge/wiki_bridge/deep_search.py`
- Test: `packages/wiki-bridge/tests/test_deep_search.py`

**Interfaces:**
- Consumes: `thread_store.append_query_trace`, `thread_store.thread_dir`, `thread_store.utc_now_iso`
- Produces:
  - `render_deep_search_markdown(report: dict[str, Any]) -> str`
  - `persist_deep_search(wiki_root: Path, report: dict[str, Any], *, thread_id: str = "") -> dict[str, Any]` with keys `json_path`, `md_path`, `query_iter_n`

If `thread_id` is set, write:

- `content/threads/<id>/drafts/deep_search_<YYYY-MM-DD>.json`
- `content/threads/<id>/drafts/deep_search_<YYYY-MM-DD>.md`

and call `append_query_trace` with one row per round: `{"round", "queries", "raw_hits": len(hits), "kept": len(hits), "notes": stop/learnings summary}`.

If `thread_id` is empty, write under `content/deep_search/` instead (same filenames). Do not call `append_query_trace`.

Markdown shape (locked):

```markdown
# Deep Search — {topic}

- breadth: `3`
- max_depth: `2`
- stop_reason: `sufficient`
- papers: `N`

## Reasoning chain

### Round 1
- queries: ...
- new papers: ...
- learnings: ...
- follow-ups: ...

## Papers
- [title](url) — abstract[:180]
```

- [ ] **Step 1: Write the failing test**

```python
from wiki_bridge.deep_search import (
    FakeSearcher,
    HeuristicReasoner,
    persist_deep_search,
    render_deep_search_markdown,
    run_deep_search,
)
from wiki_bridge.thread_store import create_thread, list_events


def test_render_contains_reasoning_chain():
    report = {
        "topic": "RAG",
        "breadth": 2,
        "max_depth": 1,
        "stop_reason": "max_depth",
        "rounds": [
            {
                "round": 1,
                "queries": ["RAG"],
                "hits": [{"title": "P1", "url": "https://arxiv.org/abs/1111.00001", "abstract": "abs"}],
                "learnings": [{"learning": "abs", "citation": "P1"}],
                "followups": ["next"],
                "sufficient": False,
            }
        ],
        "papers": [{"title": "P1", "url": "https://arxiv.org/abs/1111.00001", "abstract": "abs"}],
        "learnings": [],
        "followups": ["next"],
    }
    md = render_deep_search_markdown(report)
    assert "# Deep Search — RAG" in md
    assert "Reasoning chain" in md
    assert "Round 1" in md
    assert "P1" in md


def test_persist_writes_files_and_query_iter(tmp_path):
    create_thread(tmp_path, title="T", thread_id="t1", hypothesis="h")
    searcher = FakeSearcher({"RAG": [{"title": "P1", "abstract": "a", "arxiv": "1111.00001"}]})
    report = run_deep_search("RAG", searcher=searcher, reasoner=HeuristicReasoner(), breadth=1, max_depth=1)
    out = persist_deep_search(tmp_path, report, thread_id="t1")
    assert Path(out["json_path"]).is_file()
    assert Path(out["md_path"]).is_file()
    kinds = [e.get("kind") for e in list_events(tmp_path, "t1", limit=50)]
    assert "query_iter" in kinds
    assert out["query_iter_n"] >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: FAIL with `cannot import name 'persist_deep_search'`.

- [ ] **Step 3: Write minimal implementation**

Use `create_thread` signature already in `thread_store.py`: `create_thread(wiki_root, title=..., thread_id=..., hypothesis=...)`. If the test helper name differs, import whatever `cmd_thread_create` uses (`create_thread` exists around line 324).

```python
from datetime import datetime, timezone
from pathlib import Path

from . import thread_store as ts


def render_deep_search_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Deep Search — {report.get('topic')}",
        "",
        f"- breadth: `{report.get('breadth')}`",
        f"- max_depth: `{report.get('max_depth')}`",
        f"- stop_reason: `{report.get('stop_reason')}`",
        f"- papers: `{len(report.get('papers') or [])}`",
        "",
        "## Reasoning chain",
        "",
    ]
    for rnd in report.get("rounds") or []:
        lines.append(f"### Round {rnd.get('round')}")
        lines.append(f"- queries: {', '.join(rnd.get('queries') or []) or '—'}")
        hits = rnd.get("hits") or []
        lines.append("- new papers: " + (", ".join(h.get("title") or "?" for h in hits) or "—"))
        learns = [str(x.get("learning") or "")[:160] for x in (rnd.get("learnings") or [])]
        lines.append("- learnings:")
        lines.extend(f"  - {x}" for x in learns or ["—"])
        fups = rnd.get("followups") or []
        lines.append("- follow-ups: " + (", ".join(fups) if fups else "—"))
        lines.append("")
    lines.extend(["## Papers", ""])
    for p in report.get("papers") or []:
        title = p.get("title") or "?"
        url = p.get("url") or ""
        abs_ = (p.get("abstract") or "")[:180]
        label = f"[{title}]({url})" if url else title
        lines.append(f"- {label} — {abs_}")
    lines.append("")
    return "\n".join(lines)


def persist_deep_search(
    wiki_root: Path,
    report: dict[str, Any],
    *,
    thread_id: str = "",
) -> dict[str, Any]:
    wiki_root = Path(wiki_root)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if thread_id:
        out_dir = ts.thread_dir(wiki_root, thread_id) / "drafts"
    else:
        out_dir = ts.workspace_from_wiki_root(wiki_root) / "content" / "deep_search"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"deep_search_{day}.json"
    md_path = out_dir / f"deep_search_{day}.md"
    json_path.write_text(__import__("json").dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_deep_search_markdown(report), encoding="utf-8")
    n = 0
    if thread_id:
        rows = []
        for rnd in report.get("rounds") or []:
            rows.append(
                {
                    "round": rnd.get("round"),
                    "queries": rnd.get("queries") or [],
                    "raw_hits": len(rnd.get("hits") or []),
                    "kept": len(rnd.get("hits") or []),
                    "notes": f"stop={report.get('stop_reason')}",
                }
            )
        written = ts.append_query_trace(wiki_root, thread_id, rows, by="deep_search")
        n = len(written)
    return {"json_path": str(json_path), "md_path": str(md_path), "query_iter_n": n}
```

Confirm `create_thread` import: it is `wiki_bridge.thread_store.create_thread`. If tests fail on the name, use:

```python
from wiki_bridge.thread_store import create_thread
```

and keep the call `create_thread(tmp_path, title="T", thread_id="t1", hypothesis="h")`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/wiki-bridge/wiki_bridge/deep_search.py packages/wiki-bridge/tests/test_deep_search.py
git commit -m "feat: persist deep-search reasoning report and query_iter events"
```

---

### Task 5: ArxivQuerySearcher (HTTP mocked)

**Files:**
- Modify: `packages/wiki-bridge/wiki_bridge/deep_search.py`
- Test: `packages/wiki-bridge/tests/test_deep_search.py`

**Interfaces:**
- Consumes: `arxiv_watch.parse_atom_feed`, `arxiv_watch._http_get` **or** a local `_http_get` copy — do not make `_http_get` public if it is private; pass `fetch_bytes: Callable[[str], bytes | None]` into `ArxivQuerySearcher`
- Produces:
  - `arxiv_search_url(query: str, *, limit: int = 8) -> str` — `https://export.arxiv.org/api/query?search_query=all:{quoted}&start=0&max_results={limit}`
  - `ArxivQuerySearcher(fetch_bytes=...)` with `.search(query, limit=8)` returning PaperHit-like dicts (`title`, `abstract` from Atom `summary`, `arxiv`, `url` = `https://arxiv.org/abs/{id}`)

Reuse `SAMPLE_ATOM` from `tests/test_arxiv_watch.py` (copy the XML string into `test_deep_search.py` — do not import the other test module).

- [ ] **Step 1: Write the failing test**

```python
from wiki_bridge.deep_search import ArxivQuerySearcher, arxiv_search_url

SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2204.10254v1</id>
    <published>2022-04-21T12:00:00Z</published>
    <title>Paper Alpha Title</title>
    <summary>Alpha abstract here.</summary>
    <arxiv:primary_category term="cs.IR"/>
  </entry>
</feed>
"""


def test_arxiv_search_url_encodes_query():
    url = arxiv_search_url("retrieval augmented", limit=5)
    assert url.startswith("https://export.arxiv.org/api/query?")
    assert "max_results=5" in url
    assert "search_query=" in url


def test_arxiv_query_searcher_parses_atom():
    def fake_fetch(url: str) -> bytes | None:
        assert "export.arxiv.org" in url
        return SAMPLE_ATOM.encode("utf-8")

    s = ArxivQuerySearcher(fetch_bytes=fake_fetch)
    hits = s.search("alpha", limit=8)
    assert hits[0]["title"] == "Paper Alpha Title"
    assert hits[0]["arxiv"] == "2204.10254"
    assert "Alpha abstract" in hits[0]["abstract"]
    assert hits[0]["url"] == "https://arxiv.org/abs/2204.10254"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: FAIL with `cannot import name 'ArxivQuerySearcher'`.

- [ ] **Step 3: Write minimal implementation**

```python
import urllib.parse

from .arxiv_watch import parse_atom_feed


def arxiv_search_url(query: str, *, limit: int = 8) -> str:
    q = urllib.parse.quote(f"all:{query}")
    n = max(1, int(limit))
    return f"https://export.arxiv.org/api/query?search_query={q}&start=0&max_results={n}"


class ArxivQuerySearcher:
    def __init__(self, fetch_bytes=None):
        if fetch_bytes is None:
            from .arxiv_watch import _http_get as fetch_bytes  # production only
        self.fetch_bytes = fetch_bytes

    def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        raw = self.fetch_bytes(arxiv_search_url(query, limit=limit))
        if not raw:
            return []
        docs = parse_atom_feed(raw, source_cat="search")
        out: list[dict[str, Any]] = []
        for d in docs[: max(1, int(limit))]:
            arxiv = str(d.get("arxiv") or "")
            out.append(
                {
                    "title": d.get("title") or "",
                    "abstract": d.get("summary") or d.get("abstract") or "",
                    "arxiv": arxiv,
                    "doi": d.get("doi") or "",
                    "year": str(d.get("published") or "")[:4],
                    "url": f"https://arxiv.org/abs/{arxiv}" if arxiv else str(d.get("paper_link") or ""),
                }
            )
        return out
```

If `parse_atom_feed` does not put `summary` on the dict, read `arxiv_watch._parse_entry` and map whatever key it uses (`summary` is set in `_parse_entry`).

- [ ] **Step 4: Run test to verify it passes**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/wiki-bridge/wiki_bridge/deep_search.py packages/wiki-bridge/tests/test_deep_search.py
git commit -m "feat: add mocked ArxivQuerySearcher for deep-search"
```

---

### Task 6: CLI `deep-search` + `skill/scripts/deep_search.py`

**Files:**
- Modify: `packages/wiki-bridge/wiki_bridge/cli.py`
- Create: `skill/scripts/deep_search.py`
- Test: `packages/wiki-bridge/tests/test_deep_search.py`

**Interfaces:**
- Consumes: `run_deep_search`, `persist_deep_search`, `FakeSearcher` (when `--json` seed file given), `ArxivQuerySearcher` (default)
- Produces: CLI `deep-search` with args `--topic` (required), `--breadth` default 3, `--depth` default 2 (maps to `max_depth`), `--wiki-root` default `.`, `--thread` default `""`, `--json` optional seed hits **or** a mapping `{query: [hits]}` for FakeSearcher (tests use this; production omits it), `--out` optional extra copy path, `--dry-run` (no persist)

`cmd_deep_search` return 0; print JSON `{"stop_reason", "paper_n", "round_n", "md_path"}`.

`skill/scripts/deep_search.py` must be runnable as `python skill/scripts/deep_search.py --topic RAG --breadth 2 --depth 2 --json hits.json` by inserting `packages/wiki-bridge` onto `sys.path` then calling the same `cmd` function **or** duplicating argparse that imports `run_deep_search`. Prefer importing `wiki_bridge.cli.cmd_deep_search` after path bootstrap to stay DRY.

Keep existing subcommand `deep-research` (offline planner) as-is.

- [ ] **Step 1: Write the failing test**

```python
import json
import subprocess
import sys


def test_cli_deep_search_with_seed_json(tmp_path):
    seed = {
        "RAG": [{"title": "P1", "abstract": "retrieval", "arxiv": "1111.00001"}]
    }
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(seed), encoding="utf-8")
    cmd = [
        sys.executable,
        "-m",
        "wiki_bridge.cli",
        "deep-search",
        "--topic",
        "RAG",
        "--breadth",
        "1",
        "--depth",
        "1",
        "--wiki-root",
        str(tmp_path),
        "--json",
        str(seed_path),
        "--dry-run",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1] if False else proc.stdout)
    # CLI prints one JSON object
    assert "stop_reason" in payload
    assert payload["paper_n"] >= 1
```

If stdout mixes logs, make `cmd_deep_search` print **only** the JSON object (match other cmds that `print(json.dumps(...))`).

- [ ] **Step 2: Run test to verify it fails**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: FAIL — argparse unknown command `deep-search` or non-zero returncode.

- [ ] **Step 3: Write minimal implementation**

In `cli.py`, add `cmd_deep_search` next to existing `cmd_deep_research` (do not replace it):

```python
def cmd_deep_search(args: argparse.Namespace) -> int:
    from .deep_search import (
        ArxivQuerySearcher,
        FakeSearcher,
        HeuristicReasoner,
        persist_deep_search,
        run_deep_search,
    )

    searcher: object
    if args.json:
        raw = json.loads(Path(args.json).read_text(encoding="utf-8-sig"))
        if isinstance(raw, dict) and any(isinstance(v, list) for v in raw.values()):
            searcher = FakeSearcher({k: v for k, v in raw.items() if isinstance(v, list)})
        else:
            papers = raw if isinstance(raw, list) else list(raw.get("papers") or [])
            searcher = FakeSearcher({args.topic: papers})
    else:
        searcher = ArxivQuerySearcher()
    report = run_deep_search(
        args.topic,
        searcher=searcher,
        reasoner=HeuristicReasoner(),
        breadth=args.breadth,
        max_depth=args.depth,
    )
    persisted = {"json_path": None, "md_path": None, "query_iter_n": 0}
    if not args.dry_run:
        persisted = persist_deep_search(Path(args.wiki_root), report, thread_id=args.thread)
        if args.out:
            Path(args.out).write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    print(
        json.dumps(
            {
                "stop_reason": report["stop_reason"],
                "paper_n": len(report["papers"]),
                "round_n": len(report["rounds"]),
                "md_path": persisted.get("md_path"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0
```

Register parser **after** the existing `deep-research` parser (around line 1812):

```python
s = sub.add_parser("deep-search", help="Live Search→Read→Reason loop (breadth×depth)")
s.add_argument("--topic", required=True)
s.add_argument("--breadth", type=int, default=3)
s.add_argument("--depth", type=int, default=2, help="max Search-Read-Reason iterations")
s.add_argument("--wiki-root", default=".")
s.add_argument("--thread", default="")
s.add_argument("--json", default="", help="seed hits or {query: [hits]} FakeSearcher table")
s.add_argument("--out", default="")
s.add_argument("--dry-run", action="store_true")
s.set_defaults(func=cmd_deep_search)
```

`skill/scripts/deep_search.py`:

```python
#!/usr/bin/env python3
"""Thin wrapper: skill/scripts/deep_search.py → wiki_bridge.cli deep-search."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BRIDGE = _ROOT / "packages" / "wiki-bridge"
if str(_BRIDGE) not in sys.path:
    sys.path.insert(0, str(_BRIDGE))

from wiki_bridge.cli import main

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "deep-search", *sys.argv[1:]]
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: PASS.

Also run: `python skill/scripts/deep_search.py --topic RAG --json <tmp seed> --dry-run --breadth 1 --depth 1` from repo root after putting wiki-bridge on `PYTHONPATH` via the script's own sys.path insert.

- [ ] **Step 5: Commit**

```bash
git add packages/wiki-bridge/wiki_bridge/cli.py skill/scripts/deep_search.py packages/wiki-bridge/tests/test_deep_search.py
git commit -m "feat: add deep-search CLI and skill script wrapper"
```

---

### Task 7: Skill + docs — `/query_* --breadth --depth`

**Files:**
- Modify: `skill/SKILL.md` (Activation table + Module 2a/2b + `/wiki deep-research` row)
- Modify: `skill/examples.md`
- Modify: `skill/CHANGELOG.md` (bump to 1.19.0)
- Modify: `skill/VERSION` (currently `1.18.0` → `1.19.0`)
- Modify: `CHANGELOG.md` (workspace 2.42.0)
- Modify: `docs/THREAD_DESIGN.md` (Iterative retrieval section)

**Interfaces:**
- Consumes: CLI from Task 6
- Produces: agent-facing contract below (copy verbatim into SKILL.md)

Locked command syntax:

```
/query_english --breadth 4 --depth 3 <topic>
/query_chinese --breadth 3 --depth 2 <topic>
/wiki deep-search --breadth 3 --depth 2 [thread:<id>] <topic>
```

Agent rules to add under Module 2b (after the existing “Default max rounds = 1” paragraph):

- If the user passes `--breadth` / `--depth` (or `breadth:` / `depth:` / `广度` / `深度`), **do not** stop after the old 1-wave refine. Run `python skill/scripts/deep_search.py --topic ... --breadth N --depth D` (add `--thread <id>` when Module 1.5 is active).
- `--breadth` = how many follow-up questions from the previous Reason step become next-round Search queries (default 3).
- `--depth` = max Search→Read→Reason iterations (default 2).
- Final user-facing output is the markdown report (`render_deep_search_markdown`), not only a ranked list. Still apply language mode (`/query_english` → English headings; `/query_chinese` → Chinese headings). For Chinese mode, the agent may translate the English markdown headings; the JSON artifact stays English keys.
- Existing `/wiki deep-research` stays as the **offline** planner. New `/wiki deep-search` is the **live** loop.

- [ ] **Step 1: Write the failing test** (docs contract)

Add to `test_deep_search.py`:

```python
def test_skill_mentions_breadth_depth_flags():
    skill = ROOT.parents[1] / "skill" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "--breadth" in text
    assert "--depth" in text
    assert "deep-search" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: FAIL assertion `--breadth` not in SKILL.md (or `deep-search` missing).

- [ ] **Step 3: Write the docs**

In `skill/SKILL.md`:

1. Quick Start checklist: add `- [ ] Module 2c (optional): live deep-search when --breadth/--depth`
2. Usage format block: add `/query_english --breadth 3 --depth 2 Find papers on ...`
3. Module 2b: add the agent rules above
4. Subcommands table: add row `/wiki deep-search` | Live Search→Read→Reason (depth×breadth); keep `/wiki deep-research` row

In `skill/examples.md` add:

```
/query_chinese --breadth 3 --depth 2 对比学习如何缓解多模态偏差
```

CHANGELOG entries: one bullet “live deep-search loop (Search→Read→Reason), `--breadth`/`--depth`, CLI `deep-search`”.

`docs/THREAD_DESIGN.md` Iterative retrieval: add “Phase F+ live loop: `deep-search` CLI persists `drafts/deep_search_*.md` + `query_iter`”.

- [ ] **Step 4: Run test to verify it passes**

Run: `python packages/wiki-bridge/tests/test_deep_search.py`

Expected: PASS (all Task 1–7 tests).

- [ ] **Step 5: Commit**

```bash
git add skill/SKILL.md skill/examples.md skill/CHANGELOG.md skill/VERSION CHANGELOG.md docs/THREAD_DESIGN.md packages/wiki-bridge/tests/test_deep_search.py
git commit -m "docs: expose --breadth/--depth live deep-search on /query and /wiki"
```

---

## Self-review

1. **Spec coverage:** Step 1 loop → Tasks 1–3. Step 2 breadth/depth params → Tasks 2, 3, 6, 7. Step 3 Search/Read/Reason → Tasks 1, 2, 5. Step 4 persist + reasoning-chain report → Task 4. Existing offline `deep-research` kept.
2. **Placeholder scan:** none — FakeSearcher, HeuristicReasoner, CLI flags, markdown headings, stop_reason enum are specified.
3. **Type consistency:** `run_deep_search(..., max_depth=)` internally; CLI flag is `--depth`. `clip_followups` uses `breadth`. `persist_deep_search` returns `json_path`/`md_path`/`query_iter_n`.
