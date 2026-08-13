from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.deep_search import FakeSearcher, HeuristicReasoner, clip_followups, paper_id, search_round


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


if __name__ == "__main__":
    test_paper_id_prefers_arxiv_then_doi_then_title()
    test_paper_id_normalizes_doi_prefixes()
    test_search_round_dedups_doi_prefix_variants()
    test_search_round_dedups_across_queries()
    test_clip_followups_honors_breadth()
    test_heuristic_reasoner_emits_learnings_and_followups()
    test_heuristic_reasoner_sufficient_at_max_depth()
    print("OK deep_search")
