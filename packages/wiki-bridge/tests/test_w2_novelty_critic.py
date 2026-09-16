from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.novelty_check import check_idea_novelty
from wiki_bridge.novelty_critic import extract_facets, merge_verdicts, run_novelty_critic

CORPUS = [
    {"title": "Contrastive pretraining for dense passage retrieval", "abstract": "We pretrain dense passage retrieval encoders with contrastive learning on web corpora and evaluate on MS MARCO."},
    {"title": "Hard negative mining for dense retrieval", "abstract": "Mining hard negatives improves dense retrieval training on MS MARCO and Natural Questions."},
    {"title": "Sparse lexical retrieval with BM25 variants", "abstract": "We study BM25 parameter tuning for lexical retrieval on TREC collections."},
]


def test_extract_facets_buckets_cue_phrases():
    f = extract_facets("Contrastive pretraining for dense passage retrieval using hard negatives in low-resource languages")
    assert "retrieval" in " ".join(f["problem"])
    assert "negatives" in " ".join(f["method"])
    assert "languages" in " ".join(f["setting"])


def test_extract_facets_setting_before_method():
    f = extract_facets("Hard negative mining for dense retrieval in low-resource African languages with curriculum scheduling")
    assert "languages" in " ".join(f["setting"])
    assert "curriculum" in " ".join(f["method"])
    assert "retrieval" in " ".join(f["problem"])


def test_duplicate_when_whole_idea_overlaps():
    out = run_novelty_critic("Contrastive pretraining for dense passage retrieval encoders with contrastive learning on web corpora evaluated on MS MARCO", CORPUS)
    assert out["verdict"] == "duplicate" and out["rounds_run"] >= 1
    assert out["nearest"]["title"].startswith("Contrastive pretraining")


def test_incremental_when_facets_hit_but_whole_does_not():
    out = run_novelty_critic(
        "Dense passage retrieval for question answering in low-resource African languages using hard negative mining",
        CORPUS,
        high_overlap=6.5,
    )
    assert out["verdict"] == "incremental"
    assert out["rounds_run"] == 3 and len(out["per_round"]) == 3
    assert isinstance(out["shared_points"], list) and isinstance(out["distinguishing_points"], list)
    assert "languages" in " ".join(out["facets"]["setting"])


def test_novel_when_nothing_matches():
    out = run_novelty_critic("Quantum annealing schedules for protein folding energy landscapes", CORPUS)
    assert out["verdict"] == "novel" and out["shared_points"] == []


def test_merge_verdicts_llm_only_tightens():
    heur = {"verdict": "novel", "shared_points": [], "distinguishing_points": ["x"]}
    assert merge_verdicts(heur, {"verdict": "incremental", "shared_points": ["p"], "distinguishing_points": []})["verdict"] == "incremental"
    heur_dup = {"verdict": "duplicate", "shared_points": ["p"], "distinguishing_points": []}
    assert merge_verdicts(heur_dup, {"verdict": "novel"})["verdict"] == "duplicate"
    assert merge_verdicts(heur, None)["verdict"] == "novel"
    assert merge_verdicts(heur, {"verdict": "bogus"})["verdict"] == "novel"


def test_llm_auto_without_key_skips(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PAPER_REC_LLM_API_KEY", raising=False)
    out = run_novelty_critic("Quantum annealing for protein folding", CORPUS, use_llm="auto")
    assert out["llm"] == {"applied": False, "skipped": True, "skip_reason": "no_api_key", "model": None, "verdict": None}


def test_llm_applied_via_transport(monkeypatch):
    monkeypatch.setenv("PAPER_REC_LLM_API_KEY", "k")
    content = json.dumps({"verdict": "incremental", "shared_points": ["dense retrieval"], "distinguishing_points": ["protein folding"], "confidence": 0.7})
    transport = lambda req, t: (200, json.dumps({"choices": [{"message": {"content": content}}]}).encode())
    out = run_novelty_critic("Quantum annealing for protein folding", CORPUS, use_llm="auto", transport=transport)
    assert out["llm"]["applied"] is True and out["llm"]["verdict"] == "incremental"
    assert out["verdict"] == "incremental"  # tightened from novel


def test_llm_bad_confidence_degrades_to_heuristic(monkeypatch):
    monkeypatch.setenv("PAPER_REC_LLM_API_KEY", "k")
    content = json.dumps({"verdict": "incremental", "shared_points": ["p"], "distinguishing_points": [], "confidence": "high"})
    transport = lambda req, t: (200, json.dumps({"choices": [{"message": {"content": content}}]}).encode())
    out = run_novelty_critic("Quantum annealing for protein folding", CORPUS, use_llm="auto", transport=transport)
    assert out["llm"]["applied"] is False
    assert out["verdict"] == "novel"


def test_check_idea_novelty_keeps_legacy_keys_and_adds_critic():
    out = check_idea_novelty("Quantum annealing for protein folding", CORPUS)
    assert set(out) >= {"novel", "decision", "local", "openalex", "critic"}
    assert out["novel"] is True and out["decision"] == "novel"
    dup = check_idea_novelty("Contrastive pretraining for dense passage retrieval encoders with contrastive learning on web corpora evaluated on MS MARCO", CORPUS)
    assert dup["novel"] is False and dup["decision"] == "not novel" and dup["critic"]["verdict"] == "duplicate"
