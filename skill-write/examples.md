# Examples

```bash
python lib/select_framework.py --json 帮我写一篇小红书咖啡种草文
# costar → methods/costar.md

python lib/select_framework.py --json 把这段译成英文摘要不超过100词
# icio → methods/icio.md

python lib/select_framework.py --json star 口播介绍 LoRA
# star (forced) → methods/star.md
```

| User | Agent |
|------|--------|
| `/write` + 种草文 | 选型 costar → Read `methods/costar.md` → 填槽 → 成稿 → `framework: CO-STAR` |
| `/write star` + 口播 | Read `methods/star.md` → 成稿 → `framework: STAR` |
| `/write prompt costar …` | 只交【CO-STAR】填槽块 |
