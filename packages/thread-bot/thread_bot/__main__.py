"""CLI entry for Thread Bot."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _bootstrap():
    here = Path(__file__).resolve().parent
    root = Path(os.environ.get("PAPER_REC_ROOT") or here.parents[2]).resolve()
    bridge = root / "packages" / "wiki-bridge"
    for p in (str(bridge), str(here.parent)):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ.setdefault("PAPER_REC_ROOT", str(root))
    return root


def main(argv: list[str] | None = None) -> int:
    _bootstrap()
    p = argparse.ArgumentParser(prog="paper-rec-bot")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="Start multi-channel HTTP gateway (:8790)")
    s.add_argument("--host", default="0.0.0.0")
    s.add_argument("--port", type=int, default=8790)

    s = sub.add_parser("telegram-poll", help="Telegram long polling")
    s = sub.add_parser("repl", help="Local stdin REPL")
    s = sub.add_parser("seed-templates", help="Ensure builtin thread templates exist")

    args = p.parse_args(argv)
    if args.cmd == "serve":
        os.environ["BOT_HOST"] = args.host
        os.environ["BOT_PORT"] = str(args.port)
        from thread_bot.server import main as serve_main

        serve_main()
        return 0
    if args.cmd == "telegram-poll":
        from thread_bot.telegram_adapter import run_polling

        run_polling()
        return 0
    if args.cmd == "repl":
        from thread_bot.router import handle_message, make_context

        ctx = make_context("repl", user_id="local", chat_id="local")
        print("Paper_Rec bot REPL — /help 退出: Ctrl+C")
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            print(handle_message(ctx, line))
        return 0
    if args.cmd == "seed-templates":
        from wiki_bridge.thread_templates import ensure_builtin_templates

        ids = ensure_builtin_templates(Path(os.environ["PAPER_REC_ROOT"]))
        print("templates:", ids)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
