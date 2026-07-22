"""
Capture Paper_Rec wiki promo screenshots + optional short video.
Requires: wiki web on :5173, API on :8787, playwright installed.

  cd apps/wiki-web
  npx playwright install chromium
  python docs/promo/capture_promo.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "shots"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:5173"

# Route path → filename (path may be adjusted after probing API)
SHOTS = [
    ("/", "01-home.png"),
    ("/pages", "02-pages.png"),
    ("/ask", "06-ask.png"),
    ("/threads", "04-threads-list.png"),
    ("/experiments", "05-experiments.png"),
    ("/weekly", "02b-weekly.png"),
    ("/skills", "07-skills.png"),
]


async def main() -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("pip install playwright && npx playwright install chromium", file=sys.stderr)
        return 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.5,
            locale="zh-CN",
        )
        # Record a short continuous walkthrough
        await context.tracing.start(screenshots=True, snapshots=False)
        page = await context.new_page()

        # Probe first paper / thread for deep shots
        paper_path = None
        thread_id = "mm-llm-alignment"
        try:
            import urllib.request
            import json

            with urllib.request.urlopen("http://127.0.0.1:8787/api/wiki/papers", timeout=5) as r:
                papers = json.loads(r.read().decode())
            if isinstance(papers, list) and papers:
                paper_path = papers[0].get("path") or papers[0].get("id")
            elif isinstance(papers, dict):
                items = papers.get("items") or papers.get("papers") or []
                if items:
                    paper_path = items[0].get("path") or items[0].get("id")
        except Exception as e:
            print(f"warn: papers probe failed: {e}")

        for route, name in SHOTS:
            url = BASE + route
            print(f"shot {name} <- {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(600)
            await page.screenshot(path=str(OUT / name), full_page=False)

        if paper_path:
            url = f"{BASE}/page/{paper_path}"
            print(f"shot 03-read-dual.png <- {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(800)
            await page.screenshot(path=str(OUT / "03-read-dual.png"), full_page=False)

        url = f"{BASE}/threads/{thread_id}"
        print(f"shot 04-thread.png <- {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(OUT / "04-thread.png"), full_page=False)

        # Walkthrough video via page.video
        await context.close()
        browser2 = await p.chromium.launch(headless=True)
        context2 = await browser2.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.25,
            record_video_dir=str(Path(__file__).resolve().parent / "out"),
            record_video_size={"width": 1440, "height": 900},
        )
        page2 = await context2.new_page()
        tour = [
            ("/", 2200),
            ("/pages", 2500),
            (f"/page/{paper_path}" if paper_path else "/pages", 3200),
            (f"/threads/{thread_id}", 3200),
            ("/experiments", 2500),
            ("/ask", 2500),
            ("/", 1800),
        ]
        for route, dwell in tour:
            await page2.goto(BASE + route, wait_until="domcontentloaded", timeout=60000)
            await page2.wait_for_timeout(dwell)

        await context2.close()
        await browser2.close()
        await browser.close()

    print(f"shots -> {OUT}")
    print(f"video -> {Path(__file__).resolve().parent / 'out'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
