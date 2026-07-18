"""Chart auto-selection (self-contained inside skill-draw)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class DataSchema:
    kind: str  # series | table | matrix | embeddings | unknown
    n_series: int = 0
    n_categories: int = 0
    has_time_x: bool = False
    matrix_shape: tuple[int, int] | None = None
    columns: list[str] | None = None


@dataclass
class ChartDecision:
    chart_id: str
    reason: str
    lib_fn: str  # charts.plot_* name


def select_chart(
    schema: DataSchema,
    desc: str,
    forced: Optional[str] = None,
) -> ChartDecision:
    if forced:
        return ChartDecision(forced, "user-specified", f"charts.plot_{forced}")

    d = (desc or "").lower()
    if schema.kind == "embeddings" or "tsne" in d or "embedding" in d:
        return ChartDecision("tsne", "embedding / t-SNE mentioned", "charts.plot_tsne")
    if schema.kind == "matrix" or (schema.matrix_shape and min(schema.matrix_shape) >= 3):
        return ChartDecision("heatmap", "2D matrix data", "charts.plot_heatmap")
    if schema.has_time_x or any(k in d for k in ("loss", "curve", "epoch", "step", "收敛")):
        if "截断" in d or "broken" in d:
            return ChartDecision("broken_line", "close curves need broken axis", "charts.plot_broken_line")
        return ChartDecision("line", "ordered x + metric series", "charts.plot_line")
    if schema.n_series >= 2 and schema.n_categories >= 2:
        if "ablation" in d or "消融" in d:
            return ChartDecision("ablation", "ablation study", "charts.plot_ablation")
        return ChartDecision("multi_bar", "methods × categories", "charts.plot_multi_bar")
    if schema.n_categories >= 2 and schema.n_series <= 1:
        return ChartDecision("bar", "single metric by category", "charts.plot_bar")
    if "violin" in d or "分布" in d:
        return ChartDecision("violin", "distribution compare", "charts.plot_box_or_violin")
    if "box" in d or "箱线" in d:
        return ChartDecision("box", "distribution compare", "charts.plot_box_or_violin")
    if "scatter" in d or "pareto" in d or "时延" in d or "latency" in d:
        return ChartDecision("scatter", "trade-off scatter", "charts.plot_scatter")
    return ChartDecision("line", "fallback for numeric series", "charts.plot_line")


def infer_schema_from_obj(obj: Any) -> DataSchema:
    if isinstance(obj, dict):
        if "curves" in obj and isinstance(obj["curves"], dict):
            obj = obj["curves"]
        if obj and all(isinstance(v, dict) and ("values" in v or "y" in v) for v in obj.values()):
            return DataSchema(kind="series", n_series=len(obj), has_time_x=True)
        if "matrix" in obj or "confusion" in obj:
            m = obj.get("matrix") or obj.get("confusion")
            if isinstance(m, list) and m and isinstance(m[0], list):
                return DataSchema(kind="matrix", matrix_shape=(len(m), len(m[0])))
        if "categories" in obj and "methods" in obj:
            methods = obj["methods"]
            return DataSchema(
                kind="table",
                n_series=len(methods),
                n_categories=len(obj["categories"]),
            )
        if "labels" in obj and "values" in obj:
            return DataSchema(kind="table", n_categories=len(obj["labels"]), n_series=1)
        if all(isinstance(v, (int, float)) for v in obj.values()):
            return DataSchema(kind="table", n_categories=len(obj), n_series=1)
    if isinstance(obj, list) and obj and isinstance(obj[0], list):
        return DataSchema(kind="matrix", matrix_shape=(len(obj), len(obj[0])))
    return DataSchema(kind="unknown")
