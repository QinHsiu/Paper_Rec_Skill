"""Optional webhook notifier for Watch/Delta (Feishu/Slack/generic JSON)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def resolve_webhook_url(explicit: str = "") -> str:
    return (explicit or os.environ.get("PAPER_REC_WEBHOOK_URL") or "").strip()


def build_payload(
    *,
    thread_id: str,
    mode: str,
    title: str = "",
    candidates: list[dict[str, Any]] | None = None,
    delta_path: str = "",
    markdown_preview: str = "",
) -> dict[str, Any]:
    cands = candidates or []
    lines = [
        f"**Paper_Rec Delta** · `{thread_id}` · mode=`{mode}`",
        title and f"Title: {title}",
        f"Candidates: {len(cands)}",
    ]
    for c in cands[:8]:
        lines.append(
            f"- R={c.get('R', c.get('relevance', '—'))} · {c.get('title') or c.get('path')}"
        )
    if delta_path:
        lines.append(f"Path: `{delta_path}`")
    text = "\n".join(x for x in lines if x)

    # Generic + Feishu text + Slack text shapes
    return {
        "msg_type": "text",
        "content": {"text": text},
        "text": text,
        "paper_rec": {
            "kind": "thread_delta",
            "thread_id": thread_id,
            "mode": mode,
            "title": title,
            "candidate_count": len(cands),
            "candidates": cands[:20],
            "delta_path": delta_path,
            "markdown_preview": (markdown_preview or "")[:1500],
        },
    }


def post_webhook(url: str, payload: dict[str, Any], *, timeout: int = 15) -> dict[str, Any]:
    if not url:
        raise ValueError("webhook URL empty")
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "PaperRecSkill/2.20"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {"ok": True, "status": resp.status, "body": body[:500]}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "body": (e.read() or b"").decode("utf-8", errors="replace")[:500]}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "status": None, "body": str(e)}


def notify_delta(
    result: dict[str, Any],
    *,
    webhook_url: str = "",
) -> dict[str, Any]:
    """Send a Delta result dict to webhook if URL configured."""
    url = resolve_webhook_url(webhook_url)
    if not url:
        return {"skipped": True, "reason": "no webhook URL (set PAPER_REC_WEBHOOK_URL or --webhook)"}
    payload = build_payload(
        thread_id=str(result.get("thread_id") or ""),
        mode=str(result.get("mode") or "auto"),
        title=str((result.get("thread") or {}).get("title") or result.get("title") or ""),
        candidates=list(result.get("candidates") or []),
        delta_path=str(result.get("delta_path") or ""),
        markdown_preview=str(result.get("markdown") or result.get("markdown_preview") or ""),
    )
    resp = post_webhook(url, payload)
    return {"skipped": False, "webhook": resp, "payload_preview": payload.get("text", "")[:300]}
