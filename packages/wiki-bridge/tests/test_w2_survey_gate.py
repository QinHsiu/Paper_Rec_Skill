from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.survey_write import build_survey_draft, check_claim_support, llm_merge_outline, retrieve_for_section, write_subsection

PAPERS = [
    {"title": "Dense passage retrieval for open-domain QA", "abstract": "Dense passage retrieval learns dual encoders for open-domain question answering with contrastive training.", "year": 2020},
    {"title": "Hard negatives for dense retrieval", "abstract": "Mining hard negatives improves dense retrieval encoders and passage ranking.", "year": 2021},
    {"title": "BM25 lexical baselines", "abstract": "BM25 sparse lexical matching remains a strong retrieval baseline on TREC collections.", "year": 2019},
    {"title": "Retrieval evaluation benchmarks", "abstract": "Benchmarks for retrieval evaluation including MS MARCO and BEIR measure recall and nDCG.", "year": 2021},
    {"title": "Unrelated: protein folding energy", "abstract": "Energy landscapes of protein folding studied with molecular dynamics.", "year": 2018},
]


def test_retrieve_ranks_by_tfidf_cosine():
    ranked = retrieve_for_section("dense retrieval encoders with hard negatives", PAPERS, k=2)
    assert [p["title"] for _, p in ranked][0].startswith(("Hard negatives", "Dense passage"))
    assert all(s > 0 for s, _ in ranked) and len(ranked) == 2


def test_write_subsection_marks_unsupported_claims():
    sec = {"title": "Dense retrieval", "description": "dense retrieval encoders and hard negatives"}
    sub = write_subsection(sec, PAPERS, rag_k=3, tau=0.12)
    assert sub["claims"] and all({"cite", "claim", "support_score", "supported"} <= set(c) for c in sub["claims"])
    sub_strict = write_subsection(sec, PAPERS, rag_k=3, tau=0.99)
    assert all(not c["supported"] for c in sub_strict["claims"])
    assert "[citation needed]" in sub_strict["markdown"]


def test_check_claim_support_counts():
    meta = [{"claims": [{"supported": True}, {"supported": False, "cite": "P2", "claim": "x"}]}, {"claims": [{"supported": False, "cite": "P1", "claim": "y"}]}]
    rep = check_claim_support(meta)
    assert rep["unsupported_n"] == 2 and [u["cite"] for u in rep["unsupported"]] == ["P2", "P1"]


def test_build_survey_default_ok_and_strict_tau_fails():
    out = build_survey_draft(PAPERS[:4], chunk_size=2, rag_k=2)
    assert set(out) >= {"markdown", "cite_audit", "ok", "llm"}
    assert out["llm"]["applied"] is False and out["llm"]["skip_reason"] == "disabled"
    assert "unsupported_n" in out["cite_audit"] and "unknown_keys" in out["cite_audit"]
    hard = build_survey_draft(PAPERS[:4], chunk_size=2, rag_k=2, tau=0.99)
    assert hard["cite_audit"]["unsupported_n"] > 0 and hard["ok"] is False


def test_llm_merge_outline_rejects_unrelated_titles():
    chunks = [{"sections": [{"title": "Dense retrieval methods"}, {"title": "Evaluation benchmarks"}]}]
    heur = {"sections": [{"title": "Dense retrieval methods", "description": "d"}, {"title": "Evaluation benchmarks", "description": "e"}]}
    good = lambda s, u: {"sections": [{"title": "Dense retrieval methods", "subsections": ["Hard negatives"]}, {"title": "Evaluation and benchmarks", "subsections": []}]}
    out, rejected = llm_merge_outline(good, chunks, heur)
    assert rejected is False and [s["title"] for s in out["sections"]][0] == "Dense retrieval methods"
    bad = lambda s, u: {"sections": [{"title": "Cooking recipes", "subsections": []}]}
    out2, rejected2 = llm_merge_outline(bad, chunks, heur)
    assert rejected2 is True and out2 == heur
    out3, rejected3 = llm_merge_outline(lambda s, u: None, chunks, heur)
    assert rejected3 is True


def test_llm_prose_is_gated_by_offline_cite_check(monkeypatch):
    monkeypatch.setenv("PAPER_REC_LLM_API_KEY", "k")
    calls = {"n": 0}

    def transport(req, timeout):
        calls["n"] += 1
        body = json.loads(req.data.decode())
        user = body["messages"][1]["content"]
        if "OUTLINES" in user:
            content = json.dumps({"sections": [{"title": "Dense retrieval methods", "subsections": []}]})
        else:
            content = json.dumps({"prose": "Dense passage retrieval learns dual encoders for question answering [P1]. Unicorns were used for indexing [P9]."})
        return 200, json.dumps({"choices": [{"message": {"content": content}}]}).encode()

    out = build_survey_draft(PAPERS[:4], chunk_size=2, rag_k=2, use_llm="auto", transport=transport)
    assert out["llm"]["applied"] is True and calls["n"] >= 2
    assert "P9" in out["cite_audit"]["unknown_keys"]
    assert out["ok"] is False
