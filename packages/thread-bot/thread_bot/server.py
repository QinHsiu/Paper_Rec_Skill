"""HTTP gateway for multi-channel Thread bots."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

# bootstrap paths
import sys

_ROOT = Path(os.environ.get("PAPER_REC_ROOT") or Path(__file__).resolve().parents[3]).resolve()
_BRIDGE = _ROOT / "packages" / "wiki-bridge"
_BOT = _ROOT / "packages" / "thread-bot"
for p in (_BRIDGE, _BOT):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from thread_bot.feishu import handle_feishu_event  # noqa: E402
from thread_bot.qq_onebot import handle_onebot_event  # noqa: E402
from thread_bot.router import handle_message, make_context  # noqa: E402
from thread_bot.telegram_adapter import handle_update as tg_handle  # noqa: E402
from thread_bot.wecom import handle_wecom_payload  # noqa: E402
from wiki_bridge.thread_templates import ensure_builtin_templates  # noqa: E402

app = FastAPI(title="Paper_Rec Thread Bot Gateway", version="0.1.0")


@app.on_event("startup")
def _startup():
    os.environ.setdefault("PAPER_REC_ROOT", str(_ROOT))
    ensure_builtin_templates(_ROOT)


@app.get("/health")
def health():
    return {"ok": True, "root": str(_ROOT)}


@app.post("/bot/feishu")
async def bot_feishu(request: Request):
    body = await request.json()
    return handle_feishu_event(body)


@app.post("/bot/telegram")
async def bot_telegram(request: Request):
    body = await request.json()
    try:
        reply = tg_handle(body)
        return {"ok": True, "reply": reply}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/bot/wecom")
async def wecom_verify(msg_signature: str = "", timestamp: str = "", nonce: str = "", echostr: str = ""):
    """WeCom URL verification — returns echostr (plain mode)."""
    token = os.environ.get("WECOM_TOKEN") or ""
    if token and echostr:
        # plain mode: just echo; encrypted mode needs WECOM_AES_KEY (see docs)
        return PlainTextResponse(echostr)
    return PlainTextResponse(echostr or "ok")


@app.post("/bot/wecom")
async def bot_wecom(request: Request):
    raw = await request.body()
    out = handle_wecom_payload(raw)
    if out.get("xml"):
        return Response(content=out["xml"], media_type="application/xml")
    return out


@app.post("/bot/qq")
async def bot_qq(request: Request):
    body = await request.json()
    out = handle_onebot_event(body)
    # If reverse HTTP client mode, caller may POST our onebot_action to NapCat
    return out


@app.post("/bot/chat")
async def bot_chat(request: Request):
    """Generic JSON chat: {channel, user_id, chat_id, text}."""
    body = await request.json()
    ctx = make_context(
        str(body.get("channel") or "generic"),
        user_id=str(body.get("user_id") or ""),
        chat_id=str(body.get("chat_id") or ""),
        root=_ROOT,
    )
    reply = handle_message(ctx, str(body.get("text") or ""))
    return {"ok": True, "reply": reply, "active_thread": ctx.active_thread}


def main():
    import uvicorn

    host = os.environ.get("BOT_HOST", "0.0.0.0")
    port = int(os.environ.get("BOT_PORT", "8790"))
    uvicorn.run("thread_bot.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
