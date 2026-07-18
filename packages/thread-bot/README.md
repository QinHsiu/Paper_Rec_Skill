# paper-rec-thread-bot

Multi-channel **Cognitive Thread** conversation gateway (Feishu / Telegram / WeCom / QQ OneBot).

Full setup: [`docs/BOTS.md`](../../docs/BOTS.md).

## Install

```bash
cd packages/thread-bot
pip install -e .
# needs wiki-bridge
pip install -e ../wiki-bridge
```

## Quick start

```powershell
$env:PAPER_REC_ROOT = "D:\path\to\Paper_Rec_Skill"
python -m thread_bot repl          # local stdin
python -m thread_bot serve         # HTTP :8790
python -m thread_bot seed-templates
```

| Endpoint | Channel |
|----------|---------|
| `POST /bot/feishu` | Feishu / Lark |
| `POST /bot/telegram` | Telegram webhook |
| `GET|POST /bot/wecom` | 企业微信 |
| `POST /bot/qq` | OneBot v11 |
| `POST /bot/chat` | Generic JSON |
| `GET /health` | Health |

Commands: `/help` `/threads` `/use` `/delta` `/templates` `/import` `/feedback` `/query`

Personal WeChat is not natively supported — use WeCom or bridge via `/bot/chat`.
