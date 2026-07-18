---
name: plot-draw
version: 1.2.0
description: >-
  Publication-quality chart drawing skill. Activated by /draw. Infers best chart
  type from data path + text description (or uses a user-specified type), applies
  academic color/marker styles via self-contained skill-draw/lib, venue presets
  (cvpr/icml/neurips/acl/nature), and exports PNG/PDF.
  Use for 画图/可视化/折线柱状热力箱线/ablation plots, experiment curves, and
  when /exp_analysis /exp_training /exp_eval need figures.
---

# Plot Draw Skill / 图表绘制技能

Dedicated skill for **beautiful, paper-ready charts**. Implementation lives entirely under [`lib/`](lib/) (matplotlib + numpy). No external `plot_demo` / `../` import.

Do **not** invent data. Load only paths the user provides (or paths produced by `/exp_*` under `content/exp/`).

---

## Activation / 启用

| Command | Behavior |
|---------|----------|
| `/draw` | Draw from data + description; auto-pick chart if type omitted |
| `/draw line` · `/draw bar` · … | Force a chart class (see [chart-catalog.md](chart-catalog.md)) |

### Usage

```text
/draw
data: content/exp/demo-ocr-handwriting-v1/metrics/curves.json
desc: 训练 loss 与 val F1 随 step 变化，论文插图风格
venue: cvpr

/draw multi_bar
data: ./results/ablation.csv
desc: 四方法在五个数据量上的 HR@20 对比，突出 Ours
venue: icml

/draw
data: /path/to/labels_dist.json
desc: 训练集标签分布
```

Strip `/draw` and optional type token; remaining text is context. Pass `venue:` / `style:` (`cvpr|icml|neurips|acl|nature|default`) into `lib.draw(..., venue=...)` or CLI `--venue`. Presets: [`lib/venues.py`](lib/venues.py).

If the user asks to plot **without** `/draw` but clearly wants a figure, suggest `/draw` or apply this skill when already in an `/exp_*` turn that needs figures.

---

## Inputs

Collect (ask if missing):

| Field | Required | Notes |
|-------|----------|-------|
| `data` | yes | File/dir: `.json` `.csv` `.tsv` `.npy` `.npz` or `content/exp/.../metrics/*` |
| `desc` | yes | What to show / claim (Chinese or English) |
| `chart` | no | If absent → **auto-select** (Module B) |
| `out` | no | Default `content/exp/<id>/figures/<stem>` or `content/figures/<stamp>/` |
| `format` | no | Prefer `pdf` + `png` (PDF for TeX) |
| `title` / `xlabel` / `ylabel` | no | Infer from `desc` when omitted |
| `palette` | no | Default academic (see [color-palettes.md](color-palettes.md)) |
| `venue` / `style` | no | Venue preset: `cvpr` · `icml` · `neurips` · `acl` · `nature` · `default` |

---

## Workflow

```
Task Progress:
- [ ] Parse /draw + load data schema (shape, dtypes, columns)
- [ ] Resolve chart type (user | auto via lib.select_chart)
- [ ] Render with lib.draw / lib.charts (headless Agg)
- [ ] Save pdf+png; report paths + one-line why this chart
```

### Module A — Inspect data

Summarize: n_rows, columns, numeric vs categorical, time-like index, matrix shape, series count.  
Never plot before a short schema note.

### Module B — Auto chart selection

If user did not specify type, pick **one primary** chart via `lib.select_chart`:

| Signal in data / desc | Chart id | lib function |
|-----------------------|----------|--------------|
| 1–N numeric series vs ordered x (epoch/step) | `line` | `charts.plot_line` |
| Truncated y-axis (close values) | `broken_line` | `charts.plot_broken_line` |
| Categories × one metric | `bar` | `charts.plot_bar` |
| Categories × several methods | `multi_bar` | `charts.plot_multi_bar` |
| Bar + second metric line | `bar_line` | `charts.plot_bar_and_line` |
| Ablation / variant blocks | `ablation` | `charts.plot_ablation` |
| 2D density | `hist2d` | `charts.plot_hist2d` |
| Correlation / confusion / attention | `heatmap` | `charts.plot_heatmap` |
| Distribution compare | `box` / `violin` | `charts.plot_box_or_violin` |
| Metric vs cost / latency | `scatter` | `charts.plot_scatter` |
| Embeddings | `tsne` | `charts.plot_tsne` |

Tie-breakers: prefer **line** for training curves; **multi_bar** for method comparisons; **heatmap** for matrices ≥ 3×3; **violin/box** for per-class score lists.

Announce: `selected_chart=<id> · reason=...`

### Module C — Style (paper-ready)

Applied automatically by `lib.style.apply_style()`:

1. Font: Times New Roman (CJK fallback).
2. `pdf.fonttype = 42`.
3. Grid: light `linestyle="-."` when helpful; not on heatmaps.
4. Markers + linewidth ≥ 2; white edge on bars; hatch for B/W print.
5. Highlight **Ours** with tomato / stronger marker.
6. Export PDF + PNG (dpi=300).

Palettes: [color-palettes.md](color-palettes.md). No rainbow/jet for sequential data.

### Module D — How to render (agent)

**Prefer the bundled library** (do not reach outside the skill for plot code):

```bash
cd skill-draw   # or installed plot-draw skill root
pip install -r requirements.txt
python -m lib.cli --data <path> --desc "..." --out <stem> [--chart line]
```

```python
from lib.draw import draw
draw("metrics/curves.json", "loss curves", out_stem="figures/curves")
```

- Headless Agg is set inside `lib.style`.
- Deps: `matplotlib`, `numpy` (optional `seaborn` for some aesthetics — not required).

---

## Integration with exp-sandbox

When running `/exp_analysis`, `/exp_training`, or `/exp_eval`, **figures must go through this skill** (`lib.draw` / `/draw`):

| Exp mode | Typical charts |
|----------|----------------|
| `/exp_analysis train` | label `bar`/`violin`, length hist `bar` |
| `/exp_analysis eval` | badcase cluster `bar`/`multi_bar`, confusion `heatmap` |
| `/exp_training` | loss/metric `line`, optional `broken_line` |
| `/exp_eval` | method compare `multi_bar`/`bar_line` |

Save under `content/exp/<experiment_id>/figures/` and mention paths in the exp report / `sync-exp` payload when publishing to Wiki.

---

## Output checklist

```markdown
## Draw result
- chart: <id>
- reason: <one sentence>
- data: <path>
- files: <pdf>, <png>
- notes: <palette / highlight Ours / …>
```

---

## Related

- Catalog: [chart-catalog.md](chart-catalog.md)
- Colors: [color-palettes.md](color-palettes.md)
- Examples: [examples.md](examples.md)
- Code: [`lib/`](lib/) (`draw.py`, `charts.py`, `style.py`, `select_chart.py`)
- Exp skill: [`../skill-exp/SKILL.md`](../skill-exp/SKILL.md)
