from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.http_client import HttpTimeout
from wiki_bridge.trust_meta import annotate_papers, openalex_fetcher, paper_key, s2_fetcher

P1 = {"title": "Paper One", "doi": "10.1/one"}
P2 = {"title": "Paper Two", "doi": "10.1/two"}


def test_retracted_marks_and_blocks():
    oa = lambda p: {"cite": 100, "retracted": True}
    s2 = lambda p: {"cite": 98, "retracted": False}
    out = annotate_papers([P1], fetch_oa=oa, fetch_s2=s2)
    row = out["papers"][0]
    assert row["retracted"] is True
    assert row["trust_status"] == "retracted"
    assert out["retracted_n"] == 1
    assert paper_key(P1) in out["blocked_for_writing"]


def test_conflict_flagged_at_ratio():
    oa = lambda p: {"cite": 120, "retracted": False}
    s2 = lambda p: {"cite": 60, "retracted": False}
    out = annotate_papers([P1], fetch_oa=oa, fetch_s2=s2, conflict_ratio=0.3)
    row = out["papers"][0]
    assert row["conflict"] is True
    assert row["trust_status"] == "conflict"
    assert abs(row["conflict_ratio"] - 0.5) < 1e-9
    assert out["conflict_n"] == 1


def test_small_counts_not_conflict():
    oa = lambda p: {"cite": 3, "retracted": False}
    s2 = lambda p: {"cite": 1, "retracted": False}
    out = annotate_papers([P1], fetch_oa=oa, fetch_s2=s2, min_count_for_conflict=20)
    assert out["papers"][0]["trust_status"] == "ok"


def test_one_side_missing_is_unknown_not_ok():
    oa = lambda p: {"cite": 50, "retracted": False}
    s2 = lambda p: None
    out = annotate_papers([P1], fetch_oa=oa, fetch_s2=s2)
    row = out["papers"][0]
    assert row["trust_status"] == "unknown"
    assert row["conflict"] is None
    assert "s2_unresolved" in row["degraded_reasons"]
    assert out["unknown_n"] == 1


def test_fetch_error_degrades_item_and_continues():
    def oa(p):
        raise HttpTimeout("t")

    s2 = lambda p: {"cite": 10, "retracted": False}
    out = annotate_papers([P1, P2], fetch_oa=oa, fetch_s2=s2)
    assert out["degraded"] is True
    assert len(out["papers"]) == 2
    assert all("oa_error:HttpTimeout" in r["degraded_reasons"] for r in out["papers"])
    assert all(r["trust_status"] == "unknown" for r in out["papers"])


def test_offline_mode_all_unknown_without_fetch():
    calls = []
    oa = lambda p: calls.append(1) or {"cite": 1, "retracted": False}
    out = annotate_papers([P1], fetch_oa=oa, fetch_s2=oa, offline=True)
    assert calls == []
    assert out["papers"][0]["trust_status"] == "unknown"
    assert "offline" in out["degraded_reasons"]


def test_openalex_fetcher_parses_and_url():
    seen = {}

    def transport(req, timeout):
        seen["url"] = req.full_url
        return 200, json.dumps({"cited_by_count": 42, "is_retracted": False}).encode()

    f = openalex_fetcher(transport=transport)
    assert f(P1) == {"cite": 42, "retracted": False}
    assert "api.openalex.org/works/doi:10.1/one" in seen["url"]


def test_s2_fetcher_header_and_retracted_title():
    seen = {}

    def transport(req, timeout):
        seen["key"] = req.get_header("X-api-key")
        return 200, json.dumps({"citationCount": 7, "title": "RETRACTED: Paper One"}).encode()

    f = s2_fetcher(transport=transport, api_key="K")
    assert f(P1) == {"cite": 7, "retracted": True}
    assert seen["key"] == "K"


def test_s2_fetcher_no_key_header_when_absent(monkeypatch):
    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)
    seen = {}

    def transport(req, timeout):
        seen["key"] = req.get_header("X-api-key")
        return 200, b'{"citationCount": 1}'

    f = s2_fetcher(transport=transport)
    f(P1)
    assert seen["key"] is None


def test_fetcher_returns_none_on_404():
    f = openalex_fetcher(transport=lambda r, t: (404, b""))
    assert f(P1) is None
