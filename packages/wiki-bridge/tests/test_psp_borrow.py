"""Offline tests for paper-search-pro borrowables: rank_intent, RIS, RRF DOI-first."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wiki_bridge.rank_intent import parse_rank_intent  # noqa: E402
from wiki_bridge.ris_export import meta_to_ris  # noqa: E402
from wiki_bridge.rrf import _doc_key, normalize_doi, rrf_fuse  # noqa: E402


def test_rank_intent_cas() -> None:
    intent = parse_rank_intent("中科院一区 情绪调节")
    assert intent.platform == "cas"
    assert 1 in intent.tiers
    assert "情绪调节" in intent.cleaned_query
    assert "中科院" not in intent.cleaned_query
    assert intent.has_filter


def test_rank_intent_ambiguous_q1() -> None:
    intent = parse_rank_intent("Q1 transformer")
    assert intent.quartiles == ["Q1"]
    assert intent.ambiguous is True
    assert "transformer" in intent.cleaned_query.lower()


def test_rrf_doi_first_merges_openalex() -> None:
    assert normalize_doi("https://doi.org/10.48550/arXiv.1706.03762v5") == "10.48550/arxiv.1706.03762"
    a = {"title": "Attention", "doi": "10.5555/X", "openalex_id": "https://openalex.org/W1"}
    b = {"title": "Attention", "doi": "https://doi.org/10.5555/X", "id": "https://openalex.org/W1"}
    assert _doc_key(a) == _doc_key(b) == "doi:10.5555/x"
    fused = rrf_fuse({"oa": [a], "s2": [b]})
    assert fused["kept_n"] == 1
    assert fused["documents"][0]["rrf_key"].startswith("doi:")


def test_ris_meta() -> None:
    ris = meta_to_ris(
        {"title": "T", "authors": "A and B", "year": "2024", "doi": "10.1/x", "venue": "NeurIPS"},
        "llm/2024/t",
    )
    assert "TY  - JOUR" in ris
    assert "TI  - T" in ris
    assert "DO  - 10.1/x" in ris
    assert "ER  - " in ris


if __name__ == "__main__":
    test_rank_intent_cas()
    test_rank_intent_ambiguous_q1()
    test_rrf_doi_first_merges_openalex()
    test_ris_meta()
    print("OK paper-search-pro borrowables offline tests")
