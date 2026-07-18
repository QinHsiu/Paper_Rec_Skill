# Multi-channel Thread Bot

统一对话入口：飞书 / Telegram / 企业微信 / QQ(OneBot)。个人微信不直连（见下文）。

## Quick start

```powershell
$env:PAPER_REC_ROOT = "D:\PycharmProjects\pythonProject\projects\Paper_Rec_Skill"
cd packages/thread-bot
pip install -e .
# 本地 REPL
python -m thread_bot repl
# HTTP 网关（默认 :8790）
python -m thread_bot serve
```

| 端点 | 渠道 |
|------|------|
| `POST /bot/feishu` | 飞书事件订阅 |
| `POST /bot/telegram` | Telegram webhook |
| `GET/POST /bot/wecom` | 企业微信 |
| `POST /bot/qq` | QQ OneBot v11 反向 HTTP |
| `POST /bot/chat` | 通用 JSON |

健康检查：`GET /health`

## 命令

| 命令 | 作用 |
|------|------|
| `/help` | 帮助 |
| `/threads` | 列出研究主线 |
| `/thread <id>` | 主线摘要 |
| `/use <id>` | 设置当前主线 |
| `/delta [mode]` | Watch/Delta（默认 `auto`） |
| `/templates` | 模板市场 |
| `/import <template_id> [new_id]` | 从模板创建主线 |
| `/feedback <accept\|skip\|pin\|read> <path>` | 弱反馈 |
| `/query <问题>` | 检索提示（配合 Skill / 外接 MCP） |

也可直接发「帮助」「主线」等自然语言快捷语。

## 渠道配置

### 飞书 Feishu / Lark

1. 创建企业自建应用，开通「接收消息」「发送消息」
2. 事件订阅请求地址：`https://<host>:8790/bot/feishu`
3. 环境变量：

```text
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_VERIFY_TOKEN=   # 可选
```

### Telegram

**Webhook：** 把 BotFather token 配好后，`setWebhook` 到 `https://<host>:8790/bot/telegram`

**或长轮询（内网）：**

```powershell
$env:TELEGRAM_BOT_TOKEN = "123:ABC"
python -m thread_bot telegram-poll
```

### 企业微信 WeCom（推荐作为「微信」场景）

个人微信无稳定官方 Bot API。生产请用**企业微信应用**或自建客服：

```text
WECOM_TOKEN=
WECOM_AES_KEY=   # 加密模式时需要；明文调试可先空
```

回调 URL：`https://<host>:8790/bot/wecom`

### QQ（OneBot / NapCat / Lagrange）

1. 运行 NapCat 等，开启 HTTP 上报到 `https://<host>:8790/bot/qq`
2. 网关返回 `onebot_action`；若使用正向 HTTP，请在中间件把 action 转到 NapCat API

个人号风险自负；优先用机器人平台合规接入。

### 个人微信

不内置 itchat/wechaty puppet（不稳定且易封号）。可选：

- 企业微信 ↔ 微信互通客服
- 自建 Wechaty + padlocal（自行维护，本仓库只提供 `/bot/chat` 协议对接）

```json
POST /bot/chat
{"channel":"wechat","user_id":"u1","chat_id":"c1","text":"/templates"}
```

## 与模板市场

Bot `/templates` `/import` 读写 `content/thread-templates/`（与 Wiki CLI 同一套）。

```powershell
python -m thread_bot seed-templates
python -m wiki_bridge.cli thread-template-list --wiki-root ../..
```
