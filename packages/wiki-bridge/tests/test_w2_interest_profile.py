from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.interest_profile import build_profile, drift_report, profile_match, split_events_for_drift
from wiki_bridge.thread_store import score_paper_against_thread


def _ev(action, slug, i):
    return {"kind": "feedback", "action": action, "path": f"retrieval/2024/{slug}", "ts": f"2026-01-{i:02d}T00:00:00Z"}


def test_build_profile_weights_positive_and_negative():
    events = [_ev("accept", "contrastive-dense-retrieval", 1), _ev("skip", "bm25-sparse-baseline", 2), _ev("pin", "contrastive-hard-negatives", 3)]
    prof = build_profile(events)
    assert prof["n_events"] == 3 and prof["pos_n"] == 2 and prof["neg_n"] == 1
    assert prof["terms"]["contrastive"] > prof["terms"]["dense"] > 0
    assert prof["terms"]["bm25"] < 0


def test_build_profile_ignores_non_feedback_and_decays():
    events = [{"kind": "delta"}, _ev("accept", "old-topic-alpha", 1)] + [_ev("accept", f"new-topic-beta-{k}", k + 2) for k in range(30)]
    prof = build_profile(events, half_life=5)
    assert prof["n_events"] == 31
    assert prof["terms"]["beta"] > prof["terms"]["alpha"]


def test_profile_match_is_normalized():
    prof = build_profile([_ev("accept", "contrastive-dense", 1)])
    assert profile_match(prof, ["contrastive", "dense"]) > profile_match(prof, ["contrastive"]) > 0
    assert profile_match(prof, ["unrelated"]) == 0.0
    assert profile_match({"terms": {}}, ["x"]) == 0.0


def test_drift_report_finds_emerging_and_fading():
    older = build_profile([_ev("accept", "bm25-sparse", i) for i in range(1, 6)])
    recent = build_profile([_ev("accept", "contrastive-dense", i) for i in range(1, 6)])
    rep = drift_report(older, recent)
    assert rep["drift_score"] > 0.9
    assert "contrastive" in rep["emerging"] and "bm25" in rep["fading"]
    assert drift_report(older, older)["drift_score"] < 1e-6


def test_split_events_for_drift_window():
    evs = [_ev("accept", f"s-{i}", 1) for i in range(30)]
    older, recent = split_events_for_drift(evs, window=20)
    assert len(older) == 10 and len(recent) == 20
    assert split_events_for_drift(evs[:5], window=20) == ([], evs[:5])


def test_score_unchanged_without_profile_and_reranks_with():
    data = {"hypothesis": "dense retrieval", "claims": [], "evidence_gaps": [], "tags": [], "keywords": []}
    a = score_paper_against_thread(data, title="Contrastive dense retrieval")
    b = score_paper_against_thread(data, title="Sparse dense retrieval")
    assert a["R"] == b["R"] and "profile_match" not in a["factors"]
    prof = build_profile([_ev("accept", "contrastive-hard-negatives", 1), _ev("accept", "contrastive-pretraining", 2), _ev("skip", "sparse-index", 3)])
    a2 = score_paper_against_thread(data, title="Contrastive dense retrieval", profile=prof)
    b2 = score_paper_against_thread(data, title="Sparse dense retrieval", profile=prof)
    assert a2["R"] > b2["R"] and a2["factors"]["profile_match"] > 0
