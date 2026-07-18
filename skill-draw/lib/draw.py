"""Dispatch /draw → lib.charts (fully self-contained)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np

from . import charts, io_data
from .select_chart import DataSchema, infer_schema_from_obj, select_chart


def draw(
    data_path: str | Path,
    desc: str,
    *,
    chart: Optional[str] = None,
    out_stem: str | Path,
    formats: Sequence[str] = ("pdf", "png"),
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    venue: Optional[str] = None,
) -> dict[str, Any]:
    from . import style, venues

    preset = venues.apply_venue(venue)
    style.set_preset(preset)

    obj = io_data.load_any(data_path)
    schema = infer_schema_from_obj(obj)
    decision = select_chart(schema, desc, forced=chart)
    cid = decision.chart_id
    paths: list[Path]

    if cid in ("line", "broken_line"):
        series = io_data.as_curves(obj)
        if not series:
            raise ValueError("expected curves JSON {name:{steps,values}}")
        if cid == "broken_line":
            ys = np.concatenate([y for _, y in series.values()])
            mid = float(np.median(ys))
            paths = charts.plot_broken_line(
                series,
                y_low=(float(ys.min()) * 0.95, mid),
                y_high=(mid, float(ys.max()) * 1.05),
                xlabel=xlabel,
                ylabel=ylabel or "value",
                title=title or desc[:40],
                out_stem=out_stem,
                formats=formats,
            )
        else:
            paths = charts.plot_line(
                series,
                xlabel=xlabel or "step",
                ylabel=ylabel or "value",
                title=title or desc[:40],
                out_stem=out_stem,
                formats=formats,
            )
    elif cid == "heatmap":
        m = io_data.as_matrix(obj)
        paths = charts.plot_heatmap(
            m, xlabel=xlabel, ylabel=ylabel, title=title or desc[:40], out_stem=out_stem, formats=formats
        )
    elif cid in ("box", "violin"):
        groups = _as_groups(obj)
        paths = charts.plot_box_or_violin(
            groups, kind=cid, ylabel=ylabel, title=title or desc[:40], out_stem=out_stem, formats=formats
        )
    elif cid == "multi_bar":
        cats, methods = _as_multi_bar(obj)
        paths = charts.plot_multi_bar(
            cats, methods, ylabel=ylabel, title=title or desc[:40], out_stem=out_stem, formats=formats
        )
    elif cid in ("bar", "ablation"):
        labels, values = _as_bar(obj)
        if cid == "ablation":
            paths = charts.plot_ablation(
                labels, values, ylabel=ylabel, title=title or desc[:40], out_stem=out_stem, formats=formats
            )
        else:
            paths = charts.plot_bar(
                labels, values, ylabel=ylabel, title=title or desc[:40], out_stem=out_stem, formats=formats
            )
    elif cid == "scatter":
        pts = _as_scatter(obj)
        paths = charts.plot_scatter(
            pts, xlabel=xlabel, ylabel=ylabel, title=title or desc[:40], out_stem=out_stem, formats=formats
        )
    elif cid == "hist2d":
        x, y = _as_xy(obj)
        paths = charts.plot_hist2d(
            x, y, xlabel=xlabel, ylabel=ylabel, title=title or desc[:40], out_stem=out_stem, formats=formats
        )
    elif cid == "tsne":
        xy, lab = _as_tsne(obj)
        paths = charts.plot_tsne(xy, lab, title=title or desc[:40], out_stem=out_stem, formats=formats)
    else:
        series = io_data.as_curves(obj)
        if series:
            paths = charts.plot_line(
                series,
                xlabel=xlabel or "step",
                ylabel=ylabel or "value",
                title=title or desc[:40],
                out_stem=out_stem,
                formats=formats,
            )
            cid = "line"
        else:
            labels, values = _as_bar(obj)
            paths = charts.plot_bar(
                labels, values, ylabel=ylabel, title=title or desc[:40], out_stem=out_stem, formats=formats
            )
            cid = "bar"

    return {
        "chart": cid,
        "reason": decision.reason,
        "lib_fn": decision.lib_fn,
        "files": [str(p) for p in paths],
        "data": str(data_path),
        "venue": preset.get("id"),
        "venue_label": preset.get("label"),
    }


def _as_bar(obj: Any) -> tuple[list[str], list[float]]:
    if isinstance(obj, dict) and "labels" in obj and "values" in obj:
        return list(map(str, obj["labels"])), list(map(float, obj["values"]))
    if isinstance(obj, dict) and all(isinstance(v, (int, float)) for v in obj.values()):
        return list(map(str, obj.keys())), list(map(float, obj.values()))
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        keys, cols = io_data.table_columns(obj)
        lab_k = keys[0]
        val_k = keys[1] if len(keys) > 1 else keys[0]
        return list(map(str, cols[lab_k])), list(map(float, cols[val_k]))
    raise ValueError("cannot parse bar data")


def _as_multi_bar(obj: Any) -> tuple[list[str], dict[str, list[float]]]:
    if isinstance(obj, dict) and "categories" in obj and "methods" in obj:
        cats = list(map(str, obj["categories"]))
        methods = {str(k): list(map(float, v)) for k, v in obj["methods"].items()}
        return cats, methods
    raise ValueError("multi_bar needs {categories:[], methods:{name:[...]}}")


def _as_groups(obj: Any) -> dict[str, list[float]]:
    if isinstance(obj, dict) and "groups" in obj:
        return {str(k): list(map(float, v)) for k, v in obj["groups"].items()}
    if isinstance(obj, dict):
        return {str(k): list(map(float, v)) for k, v in obj.items() if isinstance(v, (list, tuple))}
    raise ValueError("box/violin needs {groups:{name:[...]}}")


def _as_scatter(obj: Any) -> list[tuple[float, float, str]]:
    if isinstance(obj, dict) and "points" in obj:
        return [(float(p["x"]), float(p["y"]), str(p.get("name", i))) for i, p in enumerate(obj["points"])]
    raise ValueError("scatter needs {points:[{x,y,name}]}")


def _as_xy(obj: Any) -> tuple[list[float], list[float]]:
    if isinstance(obj, dict):
        return list(map(float, obj["x"])), list(map(float, obj["y"]))
    raise ValueError("hist2d needs {x:[], y:[]}")


def _as_tsne(obj: Any) -> tuple[np.ndarray, np.ndarray]:
    if isinstance(obj, dict):
        xy = np.asarray(obj["xy"], dtype=float)
        lab = np.asarray(obj.get("labels", [0] * len(xy)))
        return xy, lab
    raise ValueError("tsne needs {xy:[[x,y],...], labels:[...]}")
