"""Offline tests for deep capability ports (number-verify, discovery, screen, etc.)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wiki_bridge.number_verify import load_registry, verify_text  # noqa: E402
from wiki_bridge.discovery_curve import analyze_snapshots  # noqa: E402
from wiki_bridge.reflect_search import reflect_coverage  # noqa: E402
from wiki_bridge.screen_next import screen_next  # noqa: E402
from wiki_bridge.posthoc_cite import posthoc_attribute  # noqa: E402
from wiki_bridge.research_brief import build_research_brief  # noqa: E402
from wiki_bridge.wiki_filters import match_meta, parse_wiki_query  # noqa: E402


def test_number_verify() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "summary.json"
        p.write_text(json.dumps({"f1": 0.912, "acc": 0.88}), encoding="utf-8")
        reg = load_registry([p])["values"]
        ok = verify_text("We achieve F1=0.912 and accuracy 88.0 on the test set.", reg)
        assert ok["ok"] is True
        bad = verify_text("We invent a magical score of 99.97 without metrics.", reg)
        assert bad["ok"] is False
        assert bad["unverified_n"] >= 1


def test_discovery_curve() -> None:
    snaps = [
        {"papers_evaluated": 20, "highly_relevant_count": 8},
        {"papers_evaluated": 40, "highly_relevant_count": 12},
        {"papers_evaluated": 60, "highly_relevant_count": 14},
        {"papers_evaluated": 80, "highly_relevant_count": 15},
    ]
    out = analyze_snapshots(snaps)
    assert out["advisory_only"] is True
    assert out["n_snapshots"] == 4
    assert "coverage_point" in out


def test_reflect_and_screen() -> None:
    papers = [{"title": "A", "year": 2019, "abstract": "x"} for _ in range(3)]
    ref = reflect_coverage(papers, query="RAG", since_year=2023, max_papers=50)
    assert "too_few_papers" in ref["issues"]
    assert ref["should_retry"] is True

    cands = [
        {"title": "good retrieval paper", "abstract": "retrieval augmented generation works"},
        {"title": "unrelated cooking", "abstract": "pasta recipes"},
        {"title": "dense retriever", "abstract": "retrieval models for QA"},
    ]
    labels = {"good retrieval paper": 1, "unrelated cooking": 0}
    nxt = screen_next(cands, labels, batch_size=2, strategy="hybrid")
    assert nxt["batch_n"] >= 1
    assert nxt["cold_start"] is False


def test_posthoc_brief_filters() -> None:
    evs = [
        {
            "eid": "E1",
            "abstract": "Self-attention transformers improve machine translation quality significantly.",
        }
    ]
    md = "We propose that self-attention transformers improve machine translation quality on benchmarks."
    out = posthoc_attribute(md, evs)
    assert out["attributed_n"] >= 1 or out["needs_attribution_n"] >= 1

    brief = build_research_brief(topic="RAG for code", must_answer=["Which retrievers work?"])
    assert "Must answer" in brief["markdown"]

    f = parse_wiki_query("+RAG -survey dt>=2023 file:fulltext")
    assert "RAG" in f.must and "survey" in f.must_not
    assert f.dt_op == ">=" and f.dt_value == "2023"
    assert f.file_type == "fulltext"
    assert match_meta({"title": "RAG methods", "year": "2024"}, f, has_fulltext=True)
    assert not match_meta({"title": "RAG survey", "year": "2024"}, f, has_fulltext=True)


if __name__ == "__main__":
    test_number_verify()
    test_discovery_curve()
    test_reflect_and_screen()
    test_posthoc_brief_filters()
    print("OK deep capability offline tests")
