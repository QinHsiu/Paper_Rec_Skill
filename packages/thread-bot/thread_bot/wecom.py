"""WeCom (企业微信) callback — XML/JSON simplified text messages."""
from __future__ import annotations

import json
import os
import re
from typing import Any
from xml.etree import ElementTree as ET

from .router import handle_message, make_context


def handle_wecom_payload(raw: str | bytes | dict[str, Any]) -> dict[str, Any]:
    """Parse WeCom callback body and return {reply_text, ...}.

    Personal WeChat is not supported natively (use WeCom app or Wechaty puppet).
    """
    if isinstance(raw, dict):
        body = raw
        text = str(body.get("text") or body.get("Content") or "")
        user = str(body.get("FromUserName") or body.get("userid") or "")
        chat = str(body.get("ChatId") or body.get("chatid") or user)
    else:
        s = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        text, user, chat = "", "", ""
        if s.strip().startswith("<"):
            root = ET.fromstring(s)
            text = (root.findtext("Content") or "").strip()
            user = (root.findtext("FromUserName") or "").strip()
            chat = user
        else:
            try:
                body = json.loads(s)
                return handle_wecom_payload(body)
            except json.JSONDecodeError:
                text = s

    # echostr handshake for URL verify is handled by server route
    if not text:
        return {"ok": True, "skipped": "empty"}

    token = os.environ.get("WECOM_TOKEN") or ""
    _ = token  # decrypt/signature left to deploy docs when using encrypted mode

    ctx = make_context("wecom", user_id=user, chat_id=chat)
    reply = handle_message(ctx, text)
    return {
        "ok": True,
        "reply": reply,
        # plaintext passive reply XML (simple mode)
        "xml": (
            f"<xml><Content><![CDATA[{reply}]]></Content>"
            f"<MsgType><![CDATA[text]]></MsgType></xml>"
        ),
    }
