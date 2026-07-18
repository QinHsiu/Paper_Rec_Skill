"""Offline + optional HTTP regression for Paper_Rec 2.12 features.

Usage (from repo root):
  python apps/wiki-api/scripts/regression_2_12.py
  python apps/wiki-api/scripts/regression_2_12.py --http   # needs API on :8787
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "wiki-bridge"))
sys.path.insert(0, str(ROOT / "apps" / "wiki-api"))

PASS = 0
FAIL = 0
BASE = "http://127.0.0.1:8787"


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


def offline() -> None:
    print("=== Offline regression 2.12 ===")
    from wiki_bridge import thread_store as ts
    from wiki_bridge.bibtex_export import export_bibtex
    from wiki_bridge.pdf_ingest import ingest_pdf, suggest_claims_from_fulltext
    from wiki_bridge.related_work import build_related_work_outline
    from wiki_bridge.thread_evidence import list_evidences
    from wiki_bridge.thread_graph import build_thread_graph, group_timeline
    from app.services import exp_store
    from app.services import thread_store as api

    ok("thread-list", len(ts.list_threads(ROOT)) >= 1)
    ok("evidences", len(list_evidences(ROOT, "mm-llm-alignment")) >= 1)
    g = build_thread_graph(ROOT, "mm-llm-alignment")
    ok("thread-graph", g["counts"]["nodes"] >= 3 and g["counts"]["edges"] >= 2, str(g["counts"]))
    ok("timeline", len(group_timeline(ts.list_events(ROOT, "mm-llm-alignment", limit=50))) >= 1)
    sample = ROOT / "content/wiki/pages/llm/2025/getting-started/sample_extract.txt"
    ing = ingest_pdf(ROOT, sample, "llm/2025/getting-started")
    ok("pdf-ingest", bool(ing.get("sections")))
    ok("claim-suggest", len(suggest_claims_from_fulltext(ROOT, "llm/2025/getting-started", max_claims=3)) >= 1)
    bib = export_bibtex(ROOT, ["llm/2025/getting-started"])
    ok("bibtex", bib["count"] == 1 and "@" in bib["bibtex"])
    rw = build_related_work_outline(ROOT, "mm-llm-alignment")
    ok("related-work", "Related Work" in rw["markdown"])
    exp = exp_store.get_experiment("demo-ocr-handwriting-v1")
    ok("curve_runs", len(exp.get("curve_runs") or []) >= 2)
    ag = api.thread_graph("mm-llm-alignment")
    ok("api.thread_graph", "timeline" in ag and ag.get("counts", {}).get("nodes", 0) >= 3)


def http_json(method: str, path: str, body: dict | None = None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw}
    except Exception as e:
        return 0, {"error": str(e)}


def http() -> None:
    print("\n=== HTTP regression 2.12 ===")
    c, h = http_json("GET", "/api/health")
    ok("health", c == 200 and bool(h and h.get("ok")))
    c, t = http_json("GET", "/api/threads")
    ok("GET /api/threads", c == 200 and len((t or {}).get("threads") or []) >= 1, str(c))
    c, th = http_json("GET", "/api/threads/mm-llm-alignment")
    ok("GET thread", c == 200 and len((th or {}).get("evidences") or []) >= 1)
    c, g = http_json("GET", "/api/threads/mm-llm-alignment/graph")
    ok("GET graph", c == 200 and ((g or {}).get("counts") or {}).get("nodes", 0) >= 3)
    c, b = http_json("GET", "/api/wiki/bibtex?paths=llm/2025/getting-started")
    ok("GET bibtex", c == 200 and (b or {}).get("count") == 1)
    c, rw = http_json("POST", "/api/threads/mm-llm-alignment/related-work", {})
    ok("POST related-work", c == 200 and "markdown" in (rw or {}))
    c, ex = http_json("GET", "/api/exp/demo-ocr-handwriting-v1")
    ok("GET exp curve_runs", c == 200 and len((ex or {}).get("curve_runs") or []) >= 2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--http", action="store_true")
    args = ap.parse_args()
    offline()
    if args.http:
        http()
    print(f"\n=== Summary: {PASS} PASS / {FAIL} FAIL ===")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
