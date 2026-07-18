"""
Compact chart primitives for /draw.

API adapted from QinHsiu/plot_demo ideas (line/bar/heatmap/鈥? but parameterized 鈥?
no demo hardcoding, no pylustrator, headless Agg only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from . import style

style.apply_style()
import matplotlib.pyplot as plt


def plot_line(
    series: dict[str, tuple[np.ndarray, np.ndarray]],
    *,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
    grid: bool = True,
) -> list[Path]:
    fig, ax = plt.subplots(figsize=style.get_figsize((5.2, 4.0)))
    if grid:
        ax.grid(linestyle="-.", alpha=0.45)
    colors = style.color_cycle(len(series))
    for i, (name, (x, y)) in enumerate(series.items()):
        mk = style.MARKERS[i % len(style.MARKERS)]
        ax.plot(x, y, marker=mk, markersize=7, linewidth=2.0, color=colors[i], label=name)
    ax.set_xlabel(xlabel, fontsize=13)
    ax.set_ylabel(ylabel, fontsize=13)
    if title:
        ax.set_title(title, fontsize=14)
    ax.tick_params(labelsize=11)
    ax.legend(loc=0, fontsize=11, ncol=min(2, max(1, len(series))))
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_bar(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    ylabel: str = "",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
    color: str | None = None,
) -> list[Path]:
    fig, ax = plt.subplots(figsize=style.get_figsize((5.0, 4.0)))
    c = color or style.COLORS[3]
    x = np.arange(len(labels))
    ax.bar(x, values, width=0.55, color=c, edgecolor="w", hatch="..")
    ax.set_xticks(x, list(labels), fontsize=11)
    ax.set_ylabel(ylabel, fontsize=13)
    if title:
        ax.set_title(title, fontsize=14)
    ax.tick_params(axis="y", labelsize=11)
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_multi_bar(
    categories: Sequence[str],
    methods: dict[str, Sequence[float]],
    *,
    ylabel: str = "",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
) -> list[Path]:
    fig, ax = plt.subplots(figsize=style.get_figsize((7.0, 4.0)))
    n_m = len(methods)
    total_w, width = 0.8, 0.8 / max(n_m, 1)
    x0 = np.arange(len(categories)) - (total_w - width) / max(n_m, 1)
    colors = style.color_cycle(n_m)
    for i, (name, vals) in enumerate(methods.items()):
        ax.bar(
            x0 + i * width,
            vals,
            width=width,
            color=colors[i],
            edgecolor="w",
            hatch=style.HATCHES[i % len(style.HATCHES)],
            label=name,
        )
    ax.set_xticks(np.arange(len(categories)), list(categories), fontsize=11)
    ax.set_ylabel(ylabel, fontsize=13)
    if title:
        ax.set_title(title, fontsize=14)
    ax.legend(ncol=min(2, n_m), fontsize=11)
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_bar_and_line(
    categories: Sequence[str],
    bar_values: Sequence[float],
    line_values: Sequence[float],
    *,
    bar_label: str = "metric_a",
    line_label: str = "metric_b",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
) -> list[Path]:
    fig, ax1 = plt.subplots(figsize=style.get_figsize((5.5, 4.0)))
    x = np.arange(len(categories))
    ax1.bar(x, bar_values, alpha=0.35, color=style.COLORS[0], label=bar_label)
    ax1.set_xticks(x, list(categories), fontsize=11)
    ax2 = ax1.twinx()
    ax2.plot(x, line_values, "o-", color=style.COLORS[2], linewidth=2.0, label=line_label)
    if title:
        ax1.set_title(title, fontsize=14)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc=0, fontsize=10)
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_scatter(
    points: Sequence[tuple[float, float, str]],
    *,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
    ours_name: str = "Ours",
) -> list[Path]:
    fig, ax = plt.subplots(figsize=style.get_figsize((5.2, 4.0)))
    colors = style.color_cycle(len(points), ours_last=False)
    for i, (xv, yv, name) in enumerate(points):
        is_ours = name.lower() == ours_name.lower() or name == "Ours"
        c = style.COLORS[3] if is_ours else colors[i % len(colors)]
        mk = "*" if is_ours else style.MARKERS[i % len(style.MARKERS)]
        ax.scatter([xv], [yv], s=55 if is_ours else 40, marker=mk, color=c, label=name)
    ax.set_xlabel(xlabel, fontsize=13)
    ax.set_ylabel(ylabel, fontsize=13)
    if title:
        ax.set_title(title, fontsize=14)
    ax.legend(loc=0, fontsize=9, bbox_to_anchor=(1.02, 1.0))
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_heatmap(
    matrix: np.ndarray,
    *,
    xticklabels: Optional[Sequence[str]] = None,
    yticklabels: Optional[Sequence[str]] = None,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    cmap: str = "YlOrRd",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
) -> list[Path]:
    import seaborn as sns

    fig, ax = plt.subplots(figsize=style.get_figsize((5.0, 4.2)))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".3f",
        cmap=cmap,
        square=True,
        linewidths=0.5,
        ax=ax,
        annot_kws={"size": 11},
    )
    if xticklabels is not None:
        ax.set_xticklabels(list(xticklabels), rotation=0, fontsize=11)
    if yticklabels is not None:
        ax.set_yticklabels(list(yticklabels), rotation=0, fontsize=11)
    ax.xaxis.tick_top()
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    if title:
        ax.set_title(title, fontsize=14, pad=12)
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_box_or_violin(
    groups: dict[str, Sequence[float]],
    *,
    kind: str = "box",
    ylabel: str = "",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
) -> list[Path]:
    fig, ax = plt.subplots(figsize=style.get_figsize((5.5, 4.0)))
    data = [list(map(float, v)) for v in groups.values()]
    labels = list(groups.keys())
    if kind == "violin":
        parts = ax.violinplot(data, showmeans=True, showmedians=True)
        for i, b in enumerate(parts.get("bodies", [])):
            b.set_facecolor(style.color_cycle(len(labels))[i])
            b.set_alpha(0.75)
    else:
        bp = ax.boxplot(data, labels=labels, patch_artist=True)
        cols = style.color_cycle(len(labels))
        for patch, c in zip(bp["boxes"], cols):
            patch.set_facecolor(c)
            patch.set_alpha(0.75)
    if kind != "box":
        ax.set_xticks(np.arange(1, len(labels) + 1), labels, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=13)
    if title:
        ax.set_title(title, fontsize=14)
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_hist2d(
    x: Sequence[float],
    y: Sequence[float],
    *,
    bins: int = 30,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
) -> list[Path]:
    fig, ax = plt.subplots(figsize=style.get_figsize((5.0, 4.0)))
    h = ax.hist2d(x, y, bins=bins, cmap="Blues")
    fig.colorbar(h[3], ax=ax)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    if title:
        ax.set_title(title, fontsize=14)
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_ablation(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    ylabel: str = "",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
    base_idx: int = 0,
    ours_idx: int = -1,
) -> list[Path]:
    """Base / ablations / Ours with hatch groups (plot_demo ablation style)."""
    fig, ax = plt.subplots(figsize=style.get_figsize((6.0, 4.0)))
    ours_idx = ours_idx if ours_idx >= 0 else len(values) - 1
    colors, hatches = [], []
    for i in range(len(values)):
        if i == base_idx:
            colors.append(style.COLORS[0])
            hatches.append("\\")
        elif i == ours_idx:
            colors.append(style.COLORS[3])
            hatches.append("/")
        else:
            colors.append(style.COLORS[1])
            hatches.append(".")
    x = np.arange(len(values))
    for i, v in enumerate(values):
        ax.bar([i], [v], width=0.55, color=colors[i], hatch=hatches[i], edgecolor="w")
    ax.set_xticks(x, list(labels), fontsize=11)
    ax.set_ylabel(ylabel, fontsize=13)
    if title:
        ax.set_title(title, fontsize=14)
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)


def plot_broken_line(
    series: dict[str, tuple[np.ndarray, np.ndarray]],
    *,
    y_low: tuple[float, float],
    y_high: tuple[float, float],
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
) -> list[Path]:
    """Two-panel broken y-axis line chart (simplified from broken_plot.py)."""
    fig, (ax2, ax1) = plt.subplots(
        2, 1, sharex=True, figsize=style.get_figsize((5.5, 5.0)), gridspec_kw={"height_ratios": [1, 1], "hspace": 0.08}
    )
    colors = style.color_cycle(len(series))
    for i, (name, (x, y)) in enumerate(series.items()):
        mk = style.MARKERS[i % len(style.MARKERS)]
        ax1.plot(x, y, marker=mk, color=colors[i], linewidth=2.0, label=name)
        ax2.plot(x, y, marker=mk, color=colors[i], linewidth=2.0, label=name)
    ax1.set_ylim(*y_low)
    ax2.set_ylim(*y_high)
    ax1.spines["top"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)
    ax2.tick_params(labeltop=False)
    d = 0.015
    kwargs = dict(transform=ax2.transAxes, color="k", clip_on=False, linewidth=1)
    ax2.plot((-d, +d), (-d, +d), **kwargs)
    ax2.plot((1 - d, 1 + d), (-d, +d), **kwargs)
    kwargs.update(transform=ax1.transAxes)
    ax1.plot((-d, +d), (1 - d, 1 + d), **kwargs)
    ax1.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)
    ax1.set_xlabel(xlabel, fontsize=12)
    ax1.set_ylabel(ylabel, fontsize=12)
    if title:
        ax2.set_title(title, fontsize=14)
    ax2.legend(loc=0, fontsize=10)
    return style.save_fig(fig, out_stem, formats)


def plot_tsne(
    xy: np.ndarray,
    labels: Sequence[int] | np.ndarray,
    *,
    title: str = "",
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
) -> list[Path]:
    labels = np.asarray(labels)
    fig, ax = plt.subplots(figsize=style.get_figsize((5.0, 4.5)))
    palette = np.array(style.COLORS)
    colors = palette[labels % len(palette)]
    ax.scatter(xy[:, 0], xy[:, 1], c=colors, s=18, alpha=0.85)
    ax.set_xticks([])
    ax.set_yticks([])
    if title:
        ax.set_title(title, fontsize=14)
    fig.tight_layout()
    return style.save_fig(fig, out_stem, formats)

