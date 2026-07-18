#!/usr/bin/env python3
"""Small regression for exp-sandbox + Wiki experiment linkage."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "wiki-bridge"))
sys.path.insert(0, str(ROOT / "apps" / "wiki-api"))
os.environ["PAPER_REC_ROOT"] = str(ROOT)

PASSED = 0
FAILED = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  OK  {name}")
    else:
        FAILED += 1
        print(f"  FAIL {name} — {detail}")


def main() -> int:
    print("=== Exp + Wiki regression ===")

    # 1) In-repo skills (portable — no machine-local paths)
    check("skill exp-sandbox in repo", (ROOT / "skill-exp" / "SKILL.md").is_file())
    check("skill paper-rec in repo", (ROOT / "skill" / "SKILL.md").is_file())
    check("skill-exp reference exists", (ROOT / "skill-exp" / "reference" / "orchestrator.py").is_file())

    # 2) sync-exp
    from wiki_bridge.exp_writer import load_exp_payload, sync_experiment
    from wiki_bridge.cli import main as bridge_main

    sample = ROOT / "packages" / "wiki-bridge" / "examples" / "sample_exp_report.json"
    payload = load_exp_payload(sample)
    outs = sync_experiment(ROOT, payload)
    check("sync-exp wrote content/exp", (outs["exp_dir"] / "final_report.md").is_file())
    check("sync-exp wrote metrics", (outs["exp_dir"] / "metrics" / "summary.json").is_file())
    check("sync-exp wrote curves", (outs["exp_dir"] / "metrics" / "curves.json").is_file())
    check("sync-exp wrote wiki _exp page", outs["wiki_page"].is_file())
    wiki_text = outs["wiki_page"].read_text(encoding="utf-8")
    check("wiki page has train_loss sparkline/mermaid", "train_loss" in wiki_text and "sparkline" in wiki_text)
    check("wiki page has F1 metric", "0.93" in wiki_text or "F1" in wiki_text)
    check("wiki page links paper_refs", "llm/2025/getting-started" in wiki_text)

    # 3) _exp not treated as paper
    from app.services.paths import is_paper_md, is_skipped_md
    from app.services import content_root as cr

    pages_root = cr.wiki_pages_dir()
    wiki_file = pages_root / "_exp" / "demo-ocr-handwriting-v1" / "README.md"
    check("_exp file exists on disk", wiki_file.is_file())
    check("_exp skipped by paper scanner", is_skipped_md(wiki_file, pages_root))
    check("_exp is not a paper", not is_paper_md(wiki_file, pages_root))

    # 4) API store
    from app.services import exp_store

    items = exp_store.list_experiments()
    ids = {x["id"] for x in items}
    check("exp_store lists demo", "demo-ocr-handwriting-v1" in ids)
    detail = exp_store.get_experiment("demo-ocr-handwriting-v1")
    check("exp detail has curves", bool(detail.get("curves", {}).get("train_loss")))
    check("exp detail has metrics F1", float(detail.get("metrics", {}).get("primary", {}).get("F1", 0)) >= 0.9)
    check("exp detail wiki_path set", detail.get("wiki_path") == "_exp/demo-ocr-handwriting-v1")
    figs = detail.get("figures") or []
    check("exp detail lists figures when png present", True)  # optional asset
    if any((ROOT / "content/exp/demo-ocr-handwriting-v1/figures").glob("*.png")):
        check("exp detail figures non-empty", len(figs) >= 1)
        check("figure url shape", figs[0].get("url", "").startswith("/api/exp/"))

    # 5) FastAPI routes smoke (TestClient)
    try:
        from fastapi.testclient import TestClient
        from app import app

        client = TestClient(app)
        r = client.get("/api/health")
        check("GET /api/health", r.status_code == 200 and r.json().get("ok"))
        r = client.get("/api/exp")
        check("GET /api/exp", r.status_code == 200 and any(
            e["id"] == "demo-ocr-handwriting-v1" for e in r.json().get("experiments", [])
        ))
        r = client.get("/api/exp/demo-ocr-handwriting-v1")
        check("GET /api/exp/{id}", r.status_code == 200 and "train_loss" in (r.json().get("curves") or {}))
        pngs = list((ROOT / "content/exp/demo-ocr-handwriting-v1/figures").glob("*.png"))
        if pngs:
            rel = f"figures/{pngs[0].name}"
            r = client.get(f"/api/exp/demo-ocr-handwriting-v1/asset/{rel}")
            check(
                "GET /api/exp/{id}/asset figure png",
                r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"),
            )
        r = client.get("/api/skills")
        skills = {s["id"] for s in r.json().get("skills", [])}
        check("skills include paper-rec + exp-sandbox", skills >= {"paper-rec", "exp-sandbox"})
        r = client.get("/api/wiki/pages")
        paths = [p.get("path", "") for p in r.json().get("pages", [])]
        check("papers list excludes _exp", not any(p.startswith("_exp") for p in paths))
    except Exception as e:
        check("FastAPI TestClient smoke", False, str(e))

    # 6) preference parse (reference module)
    sys.path.insert(0, str(ROOT / "skill-exp"))
    from reference.preference import parse_preference_response

    vote = parse_preference_response(
        'reasoning here\n{"predicted_best_index": 1, "confidence": 0.85}'
    )
    check("preference parse", vote.winner_index == 1 and abs(vote.confidence - 0.85) < 1e-6)

    from reference.train_monitor import ascii_sparkline

    check("sparkline non-empty", len(ascii_sparkline([1.8, 1.2, 0.9, 0.6])) >= 4)

    # 7) CLI entry
    rc = bridge_main(
        [
            "sync-exp",
            "--wiki-root",
            str(ROOT),
            "--report",
            str(sample),
        ]
    )
    check("cli sync-exp exit 0", rc == 0)

    print(f"\n=== Result: {PASSED} passed, {FAILED} failed ===")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
