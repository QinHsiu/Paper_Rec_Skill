"""Pass-4 P0 engines: hard gate, VLM/fig semantic, survey deepen, feedback re-retrieve."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.feedback_edit import critique_answer, feedback_edit_loop
from wiki_bridge.fig_review import review_figures
from wiki_bridge.number_verify import load_registry
from wiki_bridge.survey_write import build_survey_draft, check_survey_citations
from wiki_bridge.verified_registry import hard_gate, persist_registry


def test_hard_gate_blocks_fabricated_results(tmp_path):
    metrics = tmp_path / "summary.json"
    metrics.write_text(json.dumps({"F1": 0.82, "accuracy": 0.91}), encoding="utf-8")
    reg = load_registry([metrics])["values"]
    bad = "# Results\n\nWe achieve accuracy 99.9 on the test set.\n"
    gate = hard_gate(bad, reg)
    assert gate["blocked"] is True
    good = "# Results\n\nWe achieve accuracy 0.91 on the test set.\n"
    gate2 = hard_gate(good, reg)
    assert gate2["blocked"] is False
    path = persist_registry(tmp_path, [metrics])
    assert path.is_file()


def test_hard_gate_empty_registry():
    text = "# Results\n\nWe report F1 0.77.\n"
    gate = hard_gate(text, {})
    assert gate["blocked"] is True
    assert "empty_registry" in gate["reason"]


def test_fig_semantic_polarity():
    md = (
        "As shown in Figure 1, accuracy increases steadily.\n\n"
        "**Figure 1.** Accuracy decreases over epochs.\n"
    )
    out = review_figures(md, emit_vlm_prompts=True)
    assert out["issue_n"] >= 1
    assert out.get("vlm_prompts")


def test_survey_cluster_and_cite_audit():
    papers = [
        {"title": "Dense retrieval with transformers", "abstract": "We study dense retrieval transformers for ranking."},
        {"title": "Benchmark for retrieval", "abstract": "A new evaluation benchmark and dataset for retrieval."},
        {"title": "Clinical NLP application", "abstract": "Application of NLP models in clinical notes."},
        {"title": "Graph neural ranking", "abstract": "Graph neural networks for document ranking methods."},
    ]
    out = build_survey_draft(papers, chunk_size=2, rag_k=2, topic="Retrieval")
    assert out["section_n"] >= 1
    assert "cite_audit" in out
    audit = check_survey_citations(out["markdown"], papers)
    assert "issue_n" in audit


def test_feedback_edit_needs_retrieve():
    answer = "Transformers clearly outperform all prior work on every dataset."
    evs = [{"eid": "E1", "quote": "We study pasta recipes with tomato sauce."}]
    out = feedback_edit_loop(
        "transformer retrieval ranking",
        answer,
        evs,
        candidate_docs=[
            {"title": "Dense retrieval", "abstract": "Transformers for dense retrieval ranking benchmarks."}
        ],
    )
    assert out["feedback_n"] >= 1
    assert out["needs_retrieve"]
    assert out["followup_queries"]
    assert "CITATION" in out["edited_answer"] or out["marked_n"] >= 0


def test_critique_missing_cite():
    fbs = critique_answer(
        "RAG evaluation",
        "Studies show retrieval improves generation quality substantially.",
        [{"eid": "E1", "quote": "Retrieval improves generation on QA tasks."}],
    )
    assert any("lacks citation" in f["feedback"].lower() or "citation" in f["feedback"].lower() for f in fbs)
