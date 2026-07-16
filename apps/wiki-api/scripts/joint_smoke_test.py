"""Joint smoke test for Paper_Rec Wiki features added 2026-07-17."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_DIR = ROOT / "apps" / "wiki-api"
BRIDGE = ROOT / "packages" / "wiki-bridge"
sys.path.insert(0, str(API_DIR))

BASE = "http://127.0.0.1:8787"
WEB = "http://127.0.0.1:5173"
PASS = 0
FAIL = 0


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


def http_json(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | None]:
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


def http_status(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status
    except Exception:
        return 0


def main() -> int:
    print("=== 1. Runtime: API + Web ===")
    code, health = http_json("GET", "/api/health")
    ok("API /api/health", code == 200 and bool(health and health.get("ok")), str(health))
    ok("Web :5173", http_status(WEB + "/") == 200)

    print("\n=== 2. 论文库 fields (summary/score/added_at/rating) ===")
    code, data = http_json("GET", "/api/wiki/pages")
    pages = (data or {}).get("pages") if isinstance(data, dict) else None
    ok("GET /api/wiki/pages", code == 200 and isinstance(pages, list) and len(pages) >= 1, f"n={len(pages or [])}")
    if pages:
        sample = pages[0]
        ok("has summary", "summary" in sample, str(sample.get("summary", ""))[:40])
        ok("has score", "score" in sample)
        ok("has added_at", bool(sample.get("added_at")))
        ok("has rating key", "rating" in sample)
        path = sample["path"]
        code2, patched = http_json("PATCH", f"/api/wiki/pages/{path}/meta", {"rating": "8"})
        ok("PATCH rating", code2 == 200 and (patched or {}).get("rating") == "8" or (patched or {}).get("meta", {}).get("rating") == "8", str(code2))
        # restore empty-ish ok
        http_json("PATCH", f"/api/wiki/pages/{path}/meta", {"rating": sample.get("rating") or ""})

    print("\n=== 3. 知识图谱 (keyword nodes + href) ===")
    code, graph = http_json("GET", "/api/wiki/graph")
    nodes = (graph or {}).get("nodes") if isinstance(graph, dict) else []
    ok("GET /api/wiki/graph", code == 200 and len(nodes) >= 1, f"nodes={len(nodes)}")
    if nodes:
        n0 = nodes[0]
        ok("node has keyword", bool(n0.get("keyword") or n0.get("label")))
        ok("node has added_at", "added_at" in n0)
        ok("node has path/href", bool(n0.get("path") or n0.get("href_page")))

    print("\n=== 4. 一周推荐 (dedupe + this week) ===")
    code, weekly = http_json("GET", "/api/weekly")
    ok("GET /api/weekly", code == 200 and isinstance(weekly, dict), f"week={weekly.get('week') if weekly else None}")
    papers = (weekly or {}).get("papers") or []
    ok("weekly papers list", isinstance(papers, list) and len(papers) >= 1, f"count={weekly.get('count')}")
    from app.services.pages_index import dedupe_key

    keys = [dedupe_key(p) for p in papers]
    ok("weekly dedupe keys unique", len(keys) == len(set(keys)), f"keys={len(keys)}")

    print("\n=== 5. wiki_bridge sync → keyword README (/query_*) ===")
    report = {
        "papers": [
            {
                "title": "Joint Test Unique Paper Alpha",
                "authors": "Tester",
                "year": 2026,
                "arxiv": "https://arxiv.org/abs/8888.88888",
                "score": "7.7",
                "tags": ["llm", "joint-test"],
                "summary": "Joint smoke test paper for README + weekly append.",
                "core_idea": "Joint smoke test paper for README + weekly append.",
            }
        ]
    }
    probe = BRIDGE / "examples" / "_joint_test_report.json"
    probe.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    before_n = weekly.get("count") if weekly else 0
    cmd = [
        sys.executable,
        "-m",
        "wiki_bridge.cli",
        "sync-report",
        "--wiki-root",
        str(ROOT),
        "--report",
        str(probe),
        "--query-id",
        "joint-test-2026-07-17",
        "--mode",
        "query_english",
        "--original-query",
        "joint test /query_english into keyword README",
        "--mark-reading",
    ]
    r = subprocess.run(cmd, cwd=str(BRIDGE), capture_output=True, text=True)
    ok("sync-report exit 0", r.returncode == 0, (r.stdout or r.stderr)[-200:])
    readme = ROOT / "content" / "wiki" / "pages" / "llm" / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    ok("keyword README exists", readme.is_file())
    ok("README logs /query_english", "/query_english" in text and "joint-test-2026-07-17" in text)
    ok("README lists new paper", "Joint Test Unique Paper Alpha" in text)

    code, weekly2 = http_json("GET", "/api/weekly")
    after_n = (weekly2 or {}).get("count") if isinstance(weekly2, dict) else 0
    ok("weekly append after sync", after_n >= before_n + 1 or any("Joint Test" in p.get("title", "") for p in (weekly2 or {}).get("papers", [])), f"{before_n}→{after_n}")

    # second sync same arxiv — should not grow weekly by duplicate
    r2 = subprocess.run(cmd, cwd=str(BRIDGE), capture_output=True, text=True)
    code, weekly3 = http_json("GET", "/api/weekly")
    after2 = (weekly3 or {}).get("count") if isinstance(weekly3, dict) else 0
    joint = [p for p in (weekly3 or {}).get("papers", []) if "8888.88888" in (p.get("arxiv") or "")]
    ok("resync no weekly dup", len(joint) == 1 and after2 == after_n, f"joint={len(joint)} count={after2}")

    print("\n=== 6. /wiki skill surfaces ===")
    code, skills = http_json("GET", "/api/skills")
    cmds = []
    if isinstance(skills, dict):
        for s in skills.get("skills") or []:
            cmds.extend(s.get("commands") or [])
    ok("skills includes /wiki", "/wiki" in cmds, str(cmds))
    from app.services.pages_index import list_all_papers, papers_this_week

    all_p = list_all_papers()
    week_p = papers_this_week()
    ok("/wiki list data", len(all_p) >= 1, f"all={len(all_p)}")
    ok("/wiki week data", len(week_p) >= 1, f"week={len(week_p)}")
    ok("/wiki start (web up)", http_status(WEB + "/") == 200)

    print("\n=== 7. Search / Ask / Skills extras ===")
    code, search = http_json("GET", "/api/wiki/search?q=Qwen")
    ok("search", code == 200 and isinstance((search or {}).get("results"), list))
    code, ask = http_json("POST", "/api/ask", {"question": "Qwen"})
    ok("ask", code == 200)

    # Otter gone
    print("\n=== 8. Otter removed ===")
    ok("no services/otter-wiki", not (ROOT / "services" / "otter-wiki").exists())
    ok("no docker-compose.yml", not (ROOT / "docker-compose.yml").exists())
    ok("wiki_bridge package", (ROOT / "packages" / "wiki-bridge" / "wiki_bridge").is_dir())

    print(f"\n======== RESULT: {PASS} passed, {FAIL} failed ========")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
