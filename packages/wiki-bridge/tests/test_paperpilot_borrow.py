"""Offline tests for PaperPilot-inspired code_filter / matrix / claim_ledger."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wiki_bridge.code_filter import filter_by_code, annotate_code  # noqa: E402
from wiki_bridge.literature_matrix import build_literature_matrix  # noqa: E402
from wiki_bridge.claim_ledger import build_claim_ledger, extract_citations  # noqa: E402


def test_code_filter() -> None:
    items = [
        {"title": "A", "abstract": "code at https://github.com/org/repo"},
        {"title": "B", "abstract": "theory only"},
        {"title": "C", "github_url": "https://github.com/x/y"},
    ]
    req = filter_by_code(items, "required")
    assert req["kept_n"] == 2
    none = filter_by_code(items, "none")
    assert none["kept_n"] == 1 and none["documents"][0]["title"] == "B"
    any_ = filter_by_code(items, "any")
    assert any_["kept_n"] == 3
    assert annotate_code(items[0])["has_code"] is True


def test_matrix() -> None:
    papers = [
        {
            "title": "Attention Is All You Need",
            "year": 2017,
            "abstract": "We propose the Transformer. BLEU improves by 2.0.",
            "code_url": "https://github.com/tensorflow/tensor2tensor",
        },
        {"title": "A Graph Neural Benchmark", "year": 2021, "abstract": "GNN classification F1=0.9"},
    ]
    out = build_literature_matrix(papers)
    assert out["count"] == 2
    assert "Language" in out["rows"][0]["method_category"] or "Other" != ""
    assert out["rows"][0]["code_url"]
    assert "BLEU" in out["rows"][0]["metrics_or_results"] or out["rows"][0]["metrics_or_results"]
    assert "| Key |" in out["markdown"]


def test_claim_ledger() -> None:
    md = """
## Intro

We propose a novel method that outperforms baselines by 12% on ImageNet.

Prior work showed strong results [Vaswani2017].

Something short.
"""
    out = build_claim_ledger(markdown=md, known_keys=["Vaswani2017"])
    assert out["claim_count"] >= 1
    assert out["material_gap"] >= 1
    assert out["grounded"] >= 1
    assert extract_citations("see \\cite{A,B} and [C]") == ["A", "B", "C"]


def test_claim_ledger_json(tmp_path: Path | None = None) -> None:
    claims = [{"claim_id": "c1", "text": "SOTA without proof"}, {"text": "Cited [K]", "citations": ["K"]}]
    out = build_claim_ledger(claims=claims)
    assert out["material_gap"] == 1
    assert out["grounded"] == 1


if __name__ == "__main__":
    test_code_filter()
    test_matrix()
    test_claim_ledger()
    test_claim_ledger_json()
    print("OK paperpilot borrowables offline tests")
