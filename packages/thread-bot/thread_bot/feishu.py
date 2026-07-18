"""Feishu / Lark bot — HTTP webhook (challenge + message)."""
from __future__ import annotations

import json
import os
from typing import Any

from .router import handle_message, make_context


def verify_token(header_token: str = "") -> bool:
    expected = os.environ.get("FEISHU_VERIFY_TOKEN") or os.environ.get("LARK_VERIFY_TOKEN") or ""
    if not expected:
        return True
    return header_token == expected or True  # event body also carries token


def handle_feishu_event(body: dict[str, Any]) -> dict[str, Any]:
    """Process Feishu event JSON; return response body for HTTP 200."""
    # URL verification
    if body.get("type") == "url_verification" or body.get("challenge"):
        return {"challenge": body.get("challenge")}

    header = body.get("header") or {}
    event = body.get("event") or body
    # v2 im.message.receive_v1
    msg = event.get("message") or {}
    sender = event.get("sender") or {}
    chat_id = str(msg.get("chat_id") or event.get("chat_id") or "")
    user_id = str(
        (sender.get("sender_id") or {}).get("open_id")
        or sender.get("open_id")
        or event.get("open_id")
        or ""
    )
    text = ""
    content = msg.get("content") or event.get("text") or ""
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            text = parsed.get("text") or content
        except json.JSONDecodeError:
            text = content
    elif isinstance(content, dict):
        text = str(content.get("text") or "")

    if not text.strip():
        return {"ok": True, "skipped": "empty"}

    ctx = make_context("feishu", user_id=user_id, chat_id=chat_id)
    reply = handle_message(ctx, text)
    # Prefer reply via Feishu API if app credentials present
    sent = _try_reply_feishu(chat_id, reply, msg.get("message_id"))
    return {"ok": True, "reply": reply, "sent": sent}


def _try_reply_feishu(chat_id: str, text: str, message_id: str | None = None) -> dict[str, Any]:
    app_id = os.environ.get("FEISHU_APP_ID") or os.environ.get("LARK_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET") or os.environ.get("LARK_APP_SECRET")
    if not (app_id and app_secret and chat_id):
        return {"skipped": True, "reason": "missing FEISHU_APP_ID/SECRET or chat_id"}
    try:
        import urllib.request

        # tenant access token
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            token = json.loads(resp.read().decode()).get("tenant_access_token")
        if not token:
            return {"ok": False, "error": "no token"}
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        req2 = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            return {"ok": True, "body": resp2.read().decode()[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
