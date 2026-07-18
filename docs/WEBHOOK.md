# Optional webhook Bot (Delta push)

Lightweight **one-way** notifier after Watch/Delta.

For interactive chat commands (`/threads` `/delta` `/templates` …) on Feishu / Telegram / WeCom / QQ, use the multi-channel gateway instead: **[BOTS.md](BOTS.md)**.

## Setup

1. Create an incoming webhook (Feishu custom bot / Slack incoming / any JSON POST URL).
2. Set env or pass CLI flag:

```powershell
$env:PAPER_REC_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx"
```

## Usage

```powershell
# Dry-run payload
python -m wiki_bridge.cli notify-webhook --dry-run

# After Delta
python -m wiki_bridge.cli thread-delta --wiki-root . --id mm-llm-alignment --mode auto --notify
# or
python -m wiki_bridge.cli thread-delta --wiki-root . --id mm-llm-alignment --webhook $env:PAPER_REC_WEBHOOK_URL
```

Payload includes Feishu-style `msg_type/content.text`, Slack-style `text`, and a structured `paper_rec` object.

## Non-goals

- No chat command loop (see [BOTS.md](BOTS.md))
- No multi-tenant SaaS bot hosting
