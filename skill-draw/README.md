<div align="center">

# Plot_Draw

**Publication Chart Skill · `/draw`**  
**论文级图表绘制技能**

[![Version](https://img.shields.io/badge/version-1.1.0-1f5c55?style=flat)](VERSION)
[![Lib](https://img.shields.io/badge/code-skill--draw%2Flib-1A2332?style=flat)](lib/)

</div>

---

## Overview

Agent skill that turns **data path + description** into paper-ready **PDF/PNG** figures.  
All plotting code is **self-contained** in [`lib/`](lib/) — no external `plot_demo` path.

```bash
cd skill-draw
pip install -r requirements.txt
python -m lib.cli --data ../content/exp/.../curves.json --desc "loss" --out ../content/exp/.../figures/curves
```

---

## Command

```text
/draw [chart_id?]
data: <path>
desc: <what to show>
```

See [examples.md](examples.md) · [chart-catalog.md](chart-catalog.md) · [color-palettes.md](color-palettes.md) · [SKILL.md](SKILL.md)

---

## Install

```bash
mkdir -p .agents/skills/plot-draw
cp -r skill-draw/* .agents/skills/plot-draw/
```

---

## Acknowledgement

Chart vocabulary inspired by common academic figure patterns (historically [QinHsiu/plot_demo](https://github.com/QinHsiu/plot_demo)); runtime code is vendored and slimmed inside this skill.
