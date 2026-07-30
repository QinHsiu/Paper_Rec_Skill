#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper_Rec skill-wxmp — CLI: Markdown reading note → WeChat draft box.

  python paper_note_publish.py create --account main --md note.md --auto-cover
  python paper_note_publish.py publish --account main --media-id MEDIA_ID
"""

from __future__ import annotations

import argparse
import os
import sys

# Allow running from any cwd
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from publish_draft import WeChatDraftPublisher, load_account_config  # noqa: E402


def _publisher_from_args(args: argparse.Namespace) -> WeChatDraftPublisher:
    ai_key = args.ai_key or os.environ.get("MODELSCOPE_API_KEY")
    if args.account:
        return WeChatDraftPublisher(account_name=args.account, ai_api_key=ai_key)
    if args.app_id and args.app_secret:
        return WeChatDraftPublisher(
            app_id=args.app_id, app_secret=args.app_secret, ai_api_key=ai_key
        )
    # load default account
    cfg = load_account_config(None)
    return WeChatDraftPublisher(
        app_id=cfg["app_id"],
        app_secret=cfg["app_secret"],
        ai_api_key=ai_key or cfg.get("modelscope_api_key"),
    )


def cmd_create(args: argparse.Namespace) -> int:
    if not os.path.isfile(args.md):
        print(f"Markdown not found: {args.md}", file=sys.stderr)
        return 1
    with open(args.md, "r", encoding="utf-8") as f:
        content = f.read()

    title = args.title
    if not title:
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        title = title or "论文读书笔记"

    # WeChat title limit ~32 字
    title = title[:32]

    digest = args.digest or ""
    if not digest:
        for line in content.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("!"):
                digest = s[:120]
                break

    publisher = _publisher_from_args(args)
    article = {
        "title": title,
        "author": args.author or "论文日更",
        "digest": digest[:120],
        "content": content,
        "content_type": "markdown",
        "content_source_url": args.source_url or "",
        "show_cover_pic": 1,
        "need_open_comment": int(args.comment),
        "only_fans_can_comment": 0,
    }
    if args.thumb_media_id:
        article["thumb_media_id"] = args.thumb_media_id

    result = publisher.add_draft(
        [article],
        format_markdown=True,
        auto_generate_cover=bool(args.auto_cover or not args.thumb_media_id),
    )
    media_id = result.get("media_id")
    print(f"OK draft media_id={media_id}")
    print("Open 公众号后台 → 草稿箱 to review, then publish manually (recommended).")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    publisher = _publisher_from_args(args)
    result = publisher.publish_draft(args.media_id)
    print(f"OK publish result={result}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Paper note → WeChat draft")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create", help="Create draft from Markdown note")
    c.add_argument("--md", required=True, help="Path to Markdown reading note")
    c.add_argument("--title", default="", help="Draft title (≤32 chars)")
    c.add_argument("--digest", default="", help="Digest ≤120 chars")
    c.add_argument("--author", default="论文日更")
    c.add_argument("--source-url", default="", help="阅读原文 URL (arXiv/DOI)")
    c.add_argument("--thumb-media-id", default="", help="Existing cover media_id")
    c.add_argument("--auto-cover", action="store_true", help="AI or default cover")
    c.add_argument("--comment", type=int, default=0, choices=[0, 1])
    c.add_argument("--account", default="", help="Account name in wxmp_accounts.json")
    c.add_argument("--app-id", default="")
    c.add_argument("--app-secret", default="")
    c.add_argument("--ai-key", default="", help="ModelScope API key override")
    c.set_defaults(func=cmd_create)

    pub = sub.add_parser("publish", help="Submit draft for publish (use sparingly)")
    pub.add_argument("--media-id", required=True)
    pub.add_argument("--account", default="")
    pub.add_argument("--app-id", default="")
    pub.add_argument("--app-secret", default="")
    pub.add_argument("--ai-key", default="")
    pub.set_defaults(func=cmd_publish)

    args = p.parse_args()
    # normalize empty strings
    if hasattr(args, "account") and not args.account:
        args.account = None
    if hasattr(args, "thumb_media_id") and not args.thumb_media_id:
        args.thumb_media_id = None
    try:
        return args.func(args)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
