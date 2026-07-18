"""QQ via OneBot v11 HTTP (NapCat / Lagrange / go-cqhttp compatible)."""
from __future__ import annotations

import json
from typing import Any

from .router import handle_message, make_context


def handle_onebot_event(body: dict[str, Any]) -> dict[str, Any]:
    """Handle OneBot message event; return {action, params} reply or empty."""
    post_type = body.get("post_type")
    if post_type != "message":
        return {"ok": True, "skipped": post_type}

    message = body.get("raw_message") or body.get("message") or ""
    if isinstance(message, list):
        # CQ segments
        parts = []
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") == "text":
                parts.append(str((seg.get("data") or {}).get("text") or ""))
            elif isinstance(seg, str):
                parts.append(seg)
        message = "".join(parts)
    message = str(message).strip()
    # strip @bot CQ codes
    import re

    message = re.sub(r"\[CQ:at,[^\]]+\]", "", message).strip()
    if not message:
        return {"ok": True, "skipped": "empty"}

    user_id = str(body.get("user_id") or "")
    group_id = str(body.get("group_id") or "")
    message_type = body.get("message_type") or "private"
    chat_id = group_id if message_type == "group" else user_id

    ctx = make_context("qq", user_id=user_id, chat_id=chat_id)
    reply = handle_message(ctx, message)

    if message_type == "group" and group_id:
        return {
            "ok": True,
            "reply": reply,
            "onebot_action": {
                "action": "send_group_msg",
                "params": {"group_id": int(group_id), "message": reply},
            },
        }
    return {
        "ok": True,
        "reply": reply,
        "onebot_action": {
            "action": "send_private_msg",
            "params": {"user_id": int(user_id) if user_id.isdigit() else user_id, "message": reply},
        },
    }
