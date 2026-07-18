"""Telegram bot — long polling (python stdlib HTTP)."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from .router import handle_message, make_context


def _api(method: str, **params: Any) -> dict[str, Any]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or ""
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN required")
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def send_message(chat_id: int | str, text: str) -> dict[str, Any]:
    # Telegram limit 4096
    text = (text or "")[:4000]
    return _api("sendMessage", chat_id=chat_id, text=text)


def handle_update(update: dict[str, Any]) -> str | None:
    msg = update.get("message") or update.get("edited_message") or {}
    text = msg.get("text") or ""
    chat = msg.get("chat") or {}
    user = msg.get("from") or {}
    if not text:
        return None
    ctx = make_context(
        "telegram",
        user_id=str(user.get("id") or ""),
        chat_id=str(chat.get("id") or ""),
    )
    reply = handle_message(ctx, text)
    send_message(chat.get("id"), reply)
    return reply


def run_polling(*, offset: int = 0, idle_sleep: float = 0.5) -> None:
    print("Telegram polling… (Ctrl+C to stop)")
    off = offset
    while True:
        try:
            data = _api("getUpdates", offset=off, timeout=30)
            for upd in data.get("result") or []:
                off = int(upd["update_id"]) + 1
                try:
                    handle_update(upd)
                except Exception as e:
                    print("update error:", e)
        except KeyboardInterrupt:
            print("stopped")
            break
        except Exception as e:
            print("poll error:", e)
            time.sleep(idle_sleep)
