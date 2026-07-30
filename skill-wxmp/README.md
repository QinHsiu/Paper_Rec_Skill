<div align="center">

# wxmp-draft

**Paper_Rec · WeChat Draft Skill · `/wxmp`**  
**论文读书笔记 → 微信公众号草稿箱**

[![Version](https://img.shields.io/badge/version-1.2.0-1f5c55?style=flat)](VERSION)
[![Scope](https://img.shields.io/badge/scope-publish%20only-1A2332?style=flat)](SKILL.md)

</div>

---

## Overview

独立于 paper-rec 的发布模块：只推**热点·新颖·可借鉴**的论文解读进草稿箱（人审后发）。

选文与解读结构见 [`references/editorial.md`](references/editorial.md)。

检索 / 精读 / 组会 PPT → [`../skill/`](../skill/)  
本目录 → 排版 + 草稿箱 API

```powershell
pip install -r skill-wxmp/requirements.txt
python skill-wxmp/scripts/config_manager.py add main <AppID> <AppSecret>
python skill-wxmp/scripts/paper_note_publish.py create --account main --md note.md --auto-cover
```

---

## Commands

| 命令 | 说明 |
|------|------|
| `/wxmp note` | 写公众号体笔记 |
| `/wxmp draft` | 推入草稿箱 |
| `/wxmp publish` | 正式发布（默认不用） |
| `/wxmp daily` | 与 paper-rec 编排选文 |

Walkthrough：[examples.md](examples.md) · 原则：[references/editorial.md](references/editorial.md) · 契约：[SKILL.md](SKILL.md)

---

## Install

```bash
mkdir -p .agents/skills/wxmp-draft
cp -r skill-wxmp/* .agents/skills/wxmp-draft/
```

---

## Note

实现调用[微信公众平台开放接口](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add.html)；流程与案例为 Paper_Rec 工作区自用编排，与第三方「草稿发布 Skill」仓库无代码/文案从属关系。
