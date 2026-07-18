# Chart catalog · skill-draw/lib (self-contained)

| chart id (`/draw <id>`) | lib function | When to use |
|-------------------------|--------------|-------------|
| `line` | `charts.plot_line` | Training / metric curves vs step |
| `broken_line` | `charts.plot_broken_line` | Close curves, broken y-axis |
| `bar` | `charts.plot_bar` | Single metric × categories |
| `multi_bar` | `charts.plot_multi_bar` | Methods × categories |
| `bar_line` | `charts.plot_bar_and_line` | Dual metrics |
| `ablation` | `charts.plot_ablation` | Base / −A / Ours style |
| `scatter` | `charts.plot_scatter` | Trade-off (quality vs cost) |
| `heatmap` | `charts.plot_heatmap` | Matrix / confusion |
| `box` / `violin` | `charts.plot_box_or_violin` | Distributions |
| `hist2d` | `charts.plot_hist2d` | 2D density |
| `tsne` | `charts.plot_tsne` | 2D embedding scatter |

## Run

```bash
cd skill-draw
pip install -r requirements.txt
python -m lib.cli --data ../content/exp/.../curves.json --desc "loss curves" --out ../content/exp/.../figures/curves
```

Or from agent: `from lib.draw import draw`.
