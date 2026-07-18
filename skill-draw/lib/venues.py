"""Venue / journal style presets for /draw (Phase D)."""
from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt

# Self-contained presets — approximate submission-friendly defaults
VENUE_PRESETS: dict[str, dict[str, Any]] = {
    "default": {
        "label": "Paper_Rec academic default",
        "font": "Times New Roman",
        "figsize": (6.0, 4.0),
        "linewidth": 1.8,
        "markersize": 6,
        "grid": False,
        "spine_width": 1.0,
    },
    "cvpr": {
        "label": "CVPR-like (compact, high DPI)",
        "font": "Times New Roman",
        "figsize": (5.5, 3.8),
        "linewidth": 1.6,
        "markersize": 5,
        "grid": False,
        "spine_width": 1.1,
        "axes_labelsize": 11,
        "legend_fontsize": 9,
    },
    "icml": {
        "label": "ICML-like",
        "font": "Times New Roman",
        "figsize": (5.5, 3.6),
        "linewidth": 1.7,
        "markersize": 5.5,
        "grid": False,
        "spine_width": 1.0,
        "axes_labelsize": 10,
        "legend_fontsize": 8,
    },
    "neurips": {
        "label": "NeurIPS-like",
        "font": "Times New Roman",
        "figsize": (5.8, 3.8),
        "linewidth": 1.8,
        "markersize": 6,
        "grid": False,
        "spine_width": 1.0,
        "axes_labelsize": 10,
        "legend_fontsize": 8,
    },
    "acl": {
        "label": "ACL-like",
        "font": "Times New Roman",
        "figsize": (5.2, 3.5),
        "linewidth": 1.5,
        "markersize": 5,
        "grid": False,
        "spine_width": 0.9,
        "axes_labelsize": 10,
        "legend_fontsize": 8,
    },
    "nature": {
        "label": "Nature-family-ish (clean)",
        "font": "Arial",
        "figsize": (6.2, 4.2),
        "linewidth": 1.4,
        "markersize": 5,
        "grid": False,
        "spine_width": 0.8,
        "axes_labelsize": 9,
        "legend_fontsize": 8,
    },
}

ALIASES = {
    "cvpr": "cvpr",
    "iccv": "cvpr",
    "eccv": "cvpr",
    "icml": "icml",
    "iclr": "icml",
    "neurips": "neurips",
    "nips": "neurips",
    "acl": "acl",
    "emnlp": "acl",
    "naacl": "acl",
    "nature": "nature",
    "default": "default",
    "academic": "default",
}


def resolve_venue(name: str | None) -> str:
    key = (name or "default").strip().lower()
    return ALIASES.get(key, key if key in VENUE_PRESETS else "default")


def list_venues() -> list[dict[str, str]]:
    return [{"id": k, "label": str(v.get("label") or k)} for k, v in VENUE_PRESETS.items()]


def apply_venue(name: str | None = None) -> dict[str, Any]:
    """Apply matplotlib rc + return preset dict for chart helpers."""
    vid = resolve_venue(name)
    preset = dict(VENUE_PRESETS[vid])
    from .style import apply_style

    apply_style(font=str(preset.get("font") or "Times New Roman"))
    plt.rcParams["axes.linewidth"] = float(preset.get("spine_width") or 1.0)
    if preset.get("axes_labelsize"):
        plt.rcParams["axes.labelsize"] = preset["axes_labelsize"]
        plt.rcParams["xtick.labelsize"] = preset["axes_labelsize"]
        plt.rcParams["ytick.labelsize"] = preset["axes_labelsize"]
    if preset.get("legend_fontsize"):
        plt.rcParams["legend.fontsize"] = preset["legend_fontsize"]
    plt.rcParams["axes.grid"] = bool(preset.get("grid"))
    preset["id"] = vid
    return preset
