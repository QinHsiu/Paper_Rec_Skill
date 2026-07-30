---
name: wxmp-draft
version: 1.2.0
description: >-
  Paper_Rec WeChat draft skill. Activated by /wxmp. Publishes Markdown reading
  notes to 微信公众号草稿箱 (AppID/Secret, cover upload, multi-account). Editorial
  gate: hot/novel/actionable papers only; structured解读 with keywords, 3-sentence
  takeaways, framework figure, core method, metrics, lessons. Not for literature
  search — use paper-rec /query_* /wiki /ppt /rebuttal instead.
---

# wxmp-draft · 微信草稿技能

Paper_Rec 工作区的**发布侧** skill：把**推荐级**论文解读写入微信公众号**草稿箱**。

| 做 | 不做 |
|----|------|
| 选文门槛 + 结构化解读 + 草稿箱 | `/query_*` 检索本体 |
| MD → 微信 HTML、封面、框架图素材 | `/ppt` 组会精读全文 |
| 人审后可选 freepublish | 发水货凑日更 |

**默认只建草稿**；`/wxmp publish` 仅在用户明确要求时执行。

选文与板块：**[`references/editorial.md`](references/editorial.md)**（必读）

---

## Commands

| Command | Action |
|---------|--------|
| `/wxmp` · `help` | 配置与命令速查 |
| `/wxmp config` | 账号 add / list / set_default |
| `/wxmp note <paper>` | 按模板写解读 → `content/wxmp/notes/` |
| `/wxmp draft <md>` | 上传草稿 → `media_id` |
| `/wxmp publish <media_id>` | 提交发布（慎用） |
| `/wxmp daily <topic>` | paper-rec 选文 → **editorial 门** → note → draft |

```text
/wxmp note https://arxiv.org/abs/2106.09685
/wxmp draft content/wxmp/notes/2026-07-30-lora.md
/wxmp daily 多模态检索
```

模板与案例：[assets/paper_note_template.md](assets/paper_note_template.md) · [examples.md](examples.md) · [references/workflow.md](references/workflow.md)

---

## Boundary

```text
paper-rec (skill/)          skill-wxmp/
  候选论文 / wiki / ppt  →   门槛筛选 + 公众号解读 + 草稿箱
```

---

## Setup

```powershell
pip install -r skill-wxmp/requirements.txt
python skill-wxmp/scripts/config_manager.py add main <AppID> <AppSecret> "Paper_Rec 日更"
python skill-wxmp/scripts/config_manager.py set_default main
```

- IP 白名单；密钥 `scripts/wxmp_accounts.json` 或 `WXMP_ACCOUNTS_JSON`
- 封面：`MODELSCOPE_API_KEY` 可选；否则 `assets/default_cover.jpg`
- [draft/add](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add.html)

---

## Agent steps

1. **Selection gate** — 热点 · 新颖 · 可借鉴；不过则换文/停（见 editorial）
2. **Note** — 模板必含：基本信息（含开源）· 关键词 · 三句话看点 · 框架图 · 关键讲解 · 指标 · 借鉴 · 启发
3. 框架图有则上传微信素材后嵌入；无则声明「原文未提供框架图」
4. **Draft**：

```powershell
python skill-wxmp/scripts/paper_note_publish.py create `
  --account main `
  --md content/wxmp/notes/<slug>.md `
  --title "今日论文｜短标题" `
  --source-url "https://arxiv.org/abs/…" `
  --auto-cover
```

5. 回报 `media_id`；仅当用户要求时 `publish`

封面：[`references/covers.md`](references/covers.md) · API：[`references/wechat_api.md`](references/wechat_api.md)

---

## Safety

- 不提交密钥；不默认群发；不编造开源/指标；正文图须为微信素材 URL
