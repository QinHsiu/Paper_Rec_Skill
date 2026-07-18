"""Paper-ready matplotlib style (plot_demo conventions, self-contained)."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Academic cycle (Ours last / tomato highlight)
COLORS = [
    "#1f77b4",  # blue
    "#2ca02c",  # green
    "#ff7f0e",  # orange
    "#FF6347",  # tomato — Ours
    "#4169E1",  # royalblue
    "#CD853F",  # peru
    "#7f7f7f",  # gray
    "#800000",  # maroon
]
MARKERS = ["s", "o", "D", "X", "^", "v", "p", "*", "+", "<", ">"]
HATCHES = [".", "/", "\\", "x", "-", "+", "|", "o"]


def apply_style(*, font: str = "Times New Roman", chinese_fallback: bool = True) -> None:
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    families = [font]
    if chinese_fallback:
        families += ["Noto Serif SC", "SimHei", "DejaVu Sans"]
    plt.rcParams["font.family"] = families
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["axes.grid"] = False


def color_cycle(n: int, *, ours_last: bool = True) -> list[str]:
    if n <= 0:
        return []
    if n == 1:
        return [COLORS[3]]  # tomato
    base = COLORS[:3] + COLORS[4:]
    out = [base[i % len(base)] for i in range(n - (1 if ours_last else 0))]
    if ours_last:
        out.append(COLORS[3])
    return out[:n]


def save_fig(fig: plt.Figure, out_stem: str | Path, formats: Sequence[str] = ("pdf", "png")) -> list[Path]:
    stem = Path(out_stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for fmt in formats:
        p = stem.with_suffix(f".{fmt}")
        kw = {"bbox_inches": "tight"}
        if fmt == "png":
            kw["dpi"] = 300
        fig.savefig(p, format=fmt, **kw)
        paths.append(p)
    plt.close(fig)
    return paths
