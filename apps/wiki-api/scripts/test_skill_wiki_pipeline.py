"""Skill wiki pipeline smoke test: sync dedupe/append + /wiki list."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "apps" / "wiki-api"
BRIDGE = ROOT / "packages" / "wiki-bridge"
sys.path.insert(0, str(API))

from app.services.pages_index import dedupe_key, list_all_papers, papers_this_week  # noqa: E402


def main() -> int:
    before_all = list_all_papers()
    before_week = papers_this_week()
    print(f"BEFORE all={len(before_all)} week={len(before_week)}")
    for p in before_week:
        print(f"  week: {p['title'][:50]}")

    report = BRIDGE / "examples" / "dedupe_probe.json"
    cmd = [
        sys.executable,
        "-m",
        "wiki_bridge.cli",
        "sync-report",
        "--wiki-root",
        str(ROOT),
        "--report",
        str(report),
        "--query-id",
        "skill-test-weekly",
        "--mode",
        "query_chinese",
        "--mark-reading",
    ]
    print("RUN:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(BRIDGE))

    after_all = list_all_papers()
    after_week = papers_this_week()
    print(f"AFTER all={len(after_all)} week={len(after_week)}")
    for p in after_week:
        print(f"  week: {p['title'][:60]} | {dedupe_key(p)}")

    keys = [dedupe_key(p) for p in after_week]
    assert len(keys) == len(set(keys)), "DEDUP FAIL: duplicate keys in weekly"
    assert any("Probe" in p["title"] for p in after_week), "APPEND FAIL: new paper missing"
    deepseek_n = sum(1 for p in after_week if "2501.12948" in (p.get("arxiv") or ""))
    assert deepseek_n <= 1, "DEDUP FAIL: DeepSeek duplicated in weekly"
    assert len(after_week) >= len(before_week), "weekly shrank unexpectedly"
    # new unique paper should increase week count by at most +1 (if probe wasn't there)
    print("PASS: weekly dedupe + append OK")

    print("\n=== /wiki list ===")
    for p in list_all_papers():
        print(
            f"- {p['title'][:55]} | kw={p['keyword']} | score={p['score']} "
            f"| added={p['added_at']} | {p['path']}"
        )
    print("\n=== /wiki week ===")
    for p in papers_this_week():
        print(f"- {p['title'][:55]} | added={p['added_at']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
