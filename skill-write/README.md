# aigc-write

Writing skill：`/write` → 自动选型 → `methods/*.md` → 成稿。

| | |
|--|--|
| Version | [1.1.1](VERSION) |
| Select | [`lib/select_framework.py`](lib/select_framework.py) |
| Methods | [`methods/`](methods/) |
| Spec | [`SKILL.md`](SKILL.md) |
| Examples | [`examples.md`](examples.md) |

```bash
python lib/select_framework.py --json 帮我写一篇小红书种草文
```

安装：将本目录内容复制到 `.agents/skills/aigc-write/` 或 `.claude/skills/aigc-write/`。
