"""Offline tests for paper-qa inspired evidence grounding + page markers."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wiki_bridge.evidence_ground import (  # noqa: E402
    CANNOT_ANSWER_PHRASE,
    ground_answer,
)
from wiki_bridge.pdf_ingest import page_of_offset, quote_loc_for_snippet  # noqa: E402


def test_cannot_answer_empty() -> None:
    out = ground_answer("Anything (E1)", [])
    assert out["cannot_answer"] is True
    assert out["has_successful_answer"] is False
    assert CANNOT_ANSWER_PHRASE in out["answer"]


def test_ground_expand() -> None:
    evs = [
        {"paper_path": "llm/2017/attn", "page": 3, "quote": "Attention is all you need"},
        {"paper_path": "llm/2020/rag", "page": 2, "quote": "retrieve then generate", "support_status": "insufficient", "relevance_score": 0},
    ]
    out = ground_answer("Transformers work well (E1).", evs)
    assert out["has_successful_answer"] is True
    assert "E1" in out["used_evidences"]
    assert "attn" in out["grounded_answer"]
    assert "References:" in out["grounded_answer"]


def test_page_markers() -> None:
    text = "<!-- page: 1 -->\nHello\n<!-- page: 2 -->\nWorld attention\n"
    assert page_of_offset(text, text.find("World")) == 2
    loc = quote_loc_for_snippet("## Method\n\n" + text, "World attention")
    assert loc.get("page") == 2


if __name__ == "__main__":
    test_cannot_answer_empty()
    test_ground_expand()
    test_page_markers()
    print("OK paper-qa borrowables offline tests")
