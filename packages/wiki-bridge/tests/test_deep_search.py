from __future__ import annotations

import sys
import json
import subprocess
import tempfile
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.deep_search import (
    ArxivQuerySearcher,
    FakeSearcher,
    HeuristicReasoner,
    arxiv_search_url,
    clip_followups,
    paper_id,
    persist_deep_search,
    render_deep_search_markdown,
    run_deep_search,
    search_round,
)
from wiki_bridge.thread_store import create_thread, list_events


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


def test_paper_id_prefers_arxiv_then_doi_then_title():
    assert paper_id({"arxiv": "2204.10254v2", "title": "X"}) == "arxiv:2204.10254"
    assert paper_id({"doi": "10.5555/X", "title": "X"}) == "doi:10.5555/x"
    assert paper_id({"title": "Hello World"}) == "title:hello world"


def test_paper_id_normalizes_doi_prefixes():
    canonical = "doi:10.5555/x"
    for form in (
        "10.5555/X",
        "doi:10.5555/X",
        "http://doi.org/10.5555/X",
        "https://doi.org/10.5555/X",
        "https://dx.doi.org/10.5555/X",
    ):
        assert paper_id({"doi": form, "title": "X"}) == canonical


def test_search_round_dedups_doi_prefix_variants():
    searcher = FakeSearcher(
        {
            "q1": [{"title": "Paper One", "doi": "10.5555/X", "abstract": "a"}],
            "q2": [{"title": "Paper One again", "doi": "https://doi.org/10.5555/X", "abstract": "a"}],
        }
    )
    hits, seen = search_round(searcher, ["q1", "q2"], seen_ids=set(), limit_per_query=8)
    assert len(hits) == 1
    assert paper_id(hits[0]) == "doi:10.5555/x"
    assert "doi:10.5555/x" in seen


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
        return {
            "learnings": [{"learning": "enough", "citation": "x"}],
            "followups": ["more"],
            "sufficient": True,
            "coverage": {},
        }


def test_run_deep_search_stops_when_reasoner_says_sufficient():
    searcher = FakeSearcher(
        {"t": [{"title": "Only", "abstract": "one paper", "arxiv": "3333.00001"}]}
    )
    out = run_deep_search("t", searcher=searcher, reasoner=_AlwaysEnough(), breadth=2, max_depth=5)
    assert out["stop_reason"] == "sufficient"
    assert len(out["rounds"]) == 1


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


def test_persist_uses_thread_store_clock_for_both_filenames(tmp_path):
    report = {
        "topic": "RAG",
        "breadth": 1,
        "max_depth": 1,
        "stop_reason": "max_depth",
        "rounds": [],
        "papers": [],
    }
    with patch("wiki_bridge.deep_search.ts.utc_now_iso", return_value="2026-08-14T00:00:00Z"):
        out = persist_deep_search(tmp_path, report)
    assert Path(out["json_path"]).name == "deep_search_2026-08-14.json"
    assert Path(out["md_path"]).name == "deep_search_2026-08-14.md"


def test_skill_mentions_breadth_depth_flags():
    skill = ROOT.parents[1] / "skill" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "--breadth" in text
    assert "--depth" in text
    assert "deep-search" in text


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
    payload = json.loads(proc.stdout)
    assert "stop_reason" in payload
    assert payload["paper_n"] >= 1


if __name__ == "__main__":
    test_arxiv_search_url_encodes_query()
    test_arxiv_query_searcher_parses_atom()
    test_paper_id_prefers_arxiv_then_doi_then_title()
    test_paper_id_normalizes_doi_prefixes()
    test_search_round_dedups_doi_prefix_variants()
    test_search_round_dedups_across_queries()
    test_clip_followups_honors_breadth()
    test_heuristic_reasoner_emits_learnings_and_followups()
    test_heuristic_reasoner_sufficient_at_max_depth()
    test_run_deep_search_two_rounds_then_max_depth()
    test_run_deep_search_stops_when_no_new_papers()
    test_run_deep_search_stops_when_reasoner_says_sufficient()
    test_render_contains_reasoning_chain()
    test_skill_mentions_breadth_depth_flags()
    with tempfile.TemporaryDirectory() as tmp:
        test_persist_writes_files_and_query_iter(Path(tmp))
        test_persist_uses_thread_store_clock_for_both_filenames(Path(tmp))
    print("OK deep_search")
