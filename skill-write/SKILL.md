---
name: aigc-write
version: 1.1.1
description: >-
  AIGC writing skill. Activated by /write. Auto-selects a plugged-in methodology
  (ICIO/STAR/CO-STAR/CRISPE/BROKE/RASCEF/RACEF/SPF) via lib/select_framework.py,
  loads methods/<id>.md, fills slots, then drafts. Use for 写作/文案/文章/脚本/
  小红书/提示词/copywriting. Not for paper search, WeChat draft publish, or charts.
---

# AIGC Write · `/write`

选型 → **Read `methods/<id>.md`** → 填槽 → 成稿。规则与槽位以 method 文件为准，禁止跳过。

选型器：[`lib/select_framework.py`](lib/select_framework.py)  
原则：[`references/principles.md`](references/principles.md)

| 做 | 不做 |
|----|------|
| 选型并加载对应 method 后成稿 | 凭记忆填槽、不读 method |
| `/write <framework>` 强制框架 | 编造事实/指标/引用 |
| 页脚标注 `framework: …` | 论文检索 / 公众号草稿 API / 画图 |

---

## Methods

| id | Name | File |
|----|------|------|
| `icio` | ICIO | [`methods/icio.md`](methods/icio.md) |
| `star` | STAR | [`methods/star.md`](methods/star.md) |
| `costar` | CO-STAR | [`methods/costar.md`](methods/costar.md) |
| `crispe` | CRISPE | [`methods/crispe.md`](methods/crispe.md) |
| `broke` | BROKE | [`methods/broke.md`](methods/broke.md) |
| `rascef` | RASCEF | [`methods/rascef.md`](methods/rascef.md) |
| `racef` | RACEF | [`methods/racef.md`](methods/racef.md) |
| `spf` | SPF | [`methods/spf.md`](methods/spf.md) |

---

## Commands

| Command | Behavior |
|---------|----------|
| `/write` | 自动选型 → 加载 method → 成稿 |
| `/write costar` · `star` · `icio` · … | 强制对应 method |
| `/write prompt [framework]` | 只输出填槽块 |
| `/write help` | 本表 + Methods |

```text
/write
帮我写一篇云南精品咖啡的小红书种草文，偏治愈，300字左右

/write star
给新人 2 分钟口播：什么是 LoRA，别用黑话

/write icio
把下面译成英文摘要，≤100词：
...
```

去掉 `/write` 与可选 framework token，其余为 brief。

---

## Workflow

```
Task Progress:
- [ ] Parse brief / optional framework token
- [ ] Select (CLI or same rules in lib/select_framework.py)
- [ ] Announce: 选用 <NAME>：<reason>
- [ ] Read methods/<id>.md
- [ ] Fill template → draft (or stop at template if /write prompt)
- [ ] Footer: framework: <NAME>
```

```bash
python lib/select_framework.py --json <brief...>
python lib/select_framework.py --json costar <brief...>
python lib/select_framework.py -f star --json <brief...>
```

输出字段：`framework_id` · `name` · `method_file` · `reason` · `source`。  
自动规则只维护在 `lib/select_framework.py`，此处不重复。

同框架迭代时收紧约束；任务类型变了再重新选型。

---

## Mistakes

| Mistake | Fix |
|---------|-----|
| 不读 method 文件 | 选型后立即 Read |
| 混用他框槽位 | 只用当前 method 槽位 |
| 无 framework 页脚 | 每稿标注 |
