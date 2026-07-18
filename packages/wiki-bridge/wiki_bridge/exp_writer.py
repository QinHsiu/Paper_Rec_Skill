"""Sync experiment final results into content/exp + wiki pages/_exp."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .writer import resolve_content_root


def ascii_sparkline(values: list[float], width: int = 32) -> str:
    if not values:
        return "(empty)"
    blocks = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    pts = values if len(values) <= width else values[:: max(1, len(values) // width)][:width]
    idxs = [int((v - lo) / span * (len(blocks) - 1)) for v in pts]
    return "".join(blocks[i] for i in idxs)


def load_exp_payload(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("exp JSON must be an object")
    return data


def workspace_from_wiki_root(wiki_root: Path) -> Path:
    root = wiki_root.resolve()
    if (root / "content").is_dir():
        return root
    if root.name == "content":
        return root.parent
    if root.name == "pages" and root.parent.name == "wiki":
        return root.parents[2]
    return root


def write_exp_artifacts(workspace: Path, payload: dict[str, Any]) -> Path:
    exp_id = str(payload.get("experiment_id") or payload.get("id") or "unnamed-exp")
    root = workspace / "content" / "exp" / exp_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "metrics").mkdir(exist_ok=True)
    (root / "rounds").mkdir(exist_ok=True)
    (root / "plans").mkdir(exist_ok=True)

    metrics = payload.get("metrics") or {}
    curves = payload.get("curves") or {}
    (root / "metrics" / "summary.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if curves:
        (root / "metrics" / "curves.json").write_text(
            json.dumps(curves, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    # Optional multi-run: curve_runs: [{run_id, curves}]
    for run in payload.get("curve_runs") or []:
        if not isinstance(run, dict):
            continue
        rid = str(run.get("run_id") or run.get("name") or "run").strip()
        rcurves = run.get("curves") or {}
        if not rid or not isinstance(rcurves, dict) or not rcurves:
            continue
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in rid)
        (root / "metrics" / f"curves_{safe}.json").write_text(
            json.dumps(rcurves, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    readme = render_exp_readme(payload, curves)
    (root / "README.md").write_text(readme, encoding="utf-8")
    final = render_final_report(payload, curves)
    (root / "final_report.md").write_text(final, encoding="utf-8")

    for i, round_md in enumerate(payload.get("rounds") or [], start=1):
        if isinstance(round_md, dict):
            text = round_md.get("markdown") or json.dumps(round_md, ensure_ascii=False, indent=2)
        else:
            text = str(round_md)
        (root / "rounds" / f"round-{i:02d}.md").write_text(text, encoding="utf-8")

    return root


def write_wiki_exp_page(
    wiki_root: Path,
    payload: dict[str, Any],
    curves: dict[str, Any] | None = None,
    *,
    figure_paths: list[str] | None = None,
) -> Path:
    pages = resolve_content_root(wiki_root)
    exp_id = str(payload.get("experiment_id") or payload.get("id") or "unnamed-exp")
    out = pages / "_exp" / exp_id / "README.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    curves = curves if curves is not None else (payload.get("curves") or {})
    out.write_text(render_wiki_exp_page(payload, curves, figure_paths=figure_paths), encoding="utf-8")
    # index
    index = pages / "_exp" / "README.md"
    _update_exp_index(index, exp_id, payload)
    return out


def list_exp_figure_rels(exp_dir: Path) -> list[str]:
    """Relative paths under figures/ suitable for Wiki <img> (prefer PNG)."""
    fig = exp_dir / "figures"
    if not fig.is_dir():
        return []
    rels: list[str] = []
    for p in sorted(fig.rglob("*")):
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            rels.append(p.relative_to(exp_dir).as_posix())
    return rels


def sync_experiment(wiki_root: Path, payload: dict[str, Any]) -> dict[str, Path]:
    workspace = workspace_from_wiki_root(Path(wiki_root))
    exp_dir = write_exp_artifacts(workspace, payload)
    figures = list_exp_figure_rels(exp_dir)
    wiki_page = write_wiki_exp_page(
        wiki_root, payload, payload.get("curves") or {}, figure_paths=figures
    )
    return {"exp_dir": exp_dir, "wiki_page": wiki_page}


def render_exp_readme(payload: dict[str, Any], curves: dict[str, Any]) -> str:
    exp_id = payload.get("experiment_id") or payload.get("id")
    title = payload.get("title") or exp_id
    target = payload.get("target_score") or {}
    papers = payload.get("paper_refs") or []
    papers_s = ", ".join(papers) if isinstance(papers, list) else str(papers)
    met = payload.get("target_met", False)
    return (
        f"---\n"
        f"title: {title}\n"
        f"type: experiment\n"
        f"experiment_id: {exp_id}\n"
        f"status: {payload.get('status', 'done')}\n"
        f"target_met: {str(met).lower()}\n"
        f"paper_refs: {papers_s}\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"- task: `{target.get('task', '')}`\n"
        f"- eval_set: `{target.get('eval_set', '')}`\n"
        f"- metric: `{target.get('metric', '')}` ≥ `{target.get('threshold', '')}`\n"
        f"- target_met: **{met}**\n"
        f"- paper_refs: {papers_s or '—'}\n\n"
        f"{_curves_md(curves)}\n"
        f"{_metrics_md(payload.get('metrics') or {})}\n"
    )


def render_final_report(payload: dict[str, Any], curves: dict[str, Any]) -> str:
    exp_id = payload.get("experiment_id") or payload.get("id")
    met = payload.get("target_met", False)
    metrics = payload.get("metrics") or {}
    future = payload.get("future_optimizations") or []
    future_md = "\n".join(f"{i+1}. {x}" for i, x in enumerate(future)) or "1. (none)"
    return (
        f"# Final Experiment Report — {exp_id}\n\n"
        f"## Outcome\n"
        f"- target_score met? {'yes' if met else 'no'}\n"
        f"- best metrics / run: `{json.dumps(metrics.get('primary') or metrics, ensure_ascii=False)}`\n\n"
        f"## Curves\n{_curves_md(curves)}\n"
        f"## Metrics\n{_metrics_md(metrics)}\n"
        f"## Future optimizations\n{future_md}\n\n"
        f"## Artifacts\n"
        f"- content/exp/{exp_id}/\n"
        f"- wiki: `_exp/{exp_id}`\n"
    )


def render_wiki_exp_page(
    payload: dict[str, Any],
    curves: dict[str, Any],
    *,
    figure_paths: list[str] | None = None,
) -> str:
    """Wiki experiment module page (under pages/_exp/<id>/)."""
    exp_id = payload.get("experiment_id") or payload.get("id")
    title = payload.get("title") or exp_id
    papers = payload.get("paper_refs") or []
    links = []
    for p in papers if isinstance(papers, list) else []:
        links.append(f"- [[{p}]]")
    paper_block = "\n".join(links) or "- (none)"
    summary = payload.get("summary") or payload.get("analysis_takeaways") or ""
    return (
        f"---\n"
        f"title: {title}\n"
        f"type: experiment\n"
        f"experiment_id: {exp_id}\n"
        f"status: {payload.get('status', 'done')}\n"
        f"target_met: {str(payload.get('target_met', False)).lower()}\n"
        f"---\n\n"
        f"# 实验 · {title}\n\n"
        f"> 由 `/exp_*` 沙箱同步。原始产物：`content/exp/{exp_id}/`\n\n"
        f"## 关联论文（人工阅读标记后可挂接）\n{paper_block}\n\n"
        f"## 目标与结果\n"
        f"{_target_md(payload)}\n\n"
        f"## 图表（/draw）\n{_figures_md(exp_id, figure_paths or [])}\n"
        f"## 训练曲线（loss / metrics）\n{_curves_md(curves)}\n"
        f"## 指标表\n{_metrics_md(payload.get('metrics') or {})}\n"
        f"## 分析摘要\n{summary or '—'}\n\n"
        f"## 后续优化\n"
        + (
            "\n".join(f"- {x}" for x in (payload.get("future_optimizations") or []))
            or "- —"
        )
        + "\n"
    )


def _figures_md(exp_id: str, figure_paths: list[str]) -> str:
    if not figure_paths:
        return "_（暂无 `figures/*.png`；可用 `/draw` 生成后重新 sync-exp）_\n"
    parts: list[str] = []
    for rel in figure_paths:
        name = Path(rel).stem
        url = f"/api/exp/{exp_id}/asset/{rel}"
        parts.append(f"### {name}\n\n![{name}]({url})\n")
    return "\n".join(parts)


def _target_md(payload: dict[str, Any]) -> str:
    t = payload.get("target_score") or {}
    met = payload.get("target_met", False)
    return (
        f"| 字段 | 值 |\n|---|---|\n"
        f"| task | {t.get('task', '')} |\n"
        f"| eval_set | {t.get('eval_set', '')} |\n"
        f"| metric | {t.get('metric', '')} |\n"
        f"| threshold | {t.get('threshold', '')} |\n"
        f"| target_met | {'✅' if met else '❌'} |\n"
    )


def _metrics_md(metrics: dict[str, Any]) -> str:
    primary = metrics.get("primary") or metrics
    if not isinstance(primary, dict):
        return f"```\n{primary}\n```\n"
    rows = ["| Metric | Value |", "|---|---|"]
    for k, v in primary.items():
        if k in ("summary",):
            continue
        rows.append(f"| {k} | {v} |")
    return "\n".join(rows) + "\n"


def _curves_md(curves: dict[str, Any]) -> str:
    if not curves:
        return "_（无曲线数据）_\n"
    parts: list[str] = []
    for name, series in curves.items():
        if isinstance(series, dict):
            vals = series.get("values") or series.get("y") or []
            steps = series.get("steps") or series.get("x") or list(range(1, len(vals) + 1))
        elif isinstance(series, list):
            vals = series
            steps = list(range(1, len(vals) + 1))
        else:
            continue
        vals_f = [float(v) for v in vals]
        parts.append(f"### {name}\n")
        parts.append(f"- sparkline: `{ascii_sparkline(vals_f)}`\n")
        parts.append(f"- points: {list(zip(steps, vals_f))[:12]}{'…' if len(vals_f) > 12 else ''}\n")
        # mermaid xychart (short)
        if len(vals_f) <= 16:
            xs = ", ".join(str(s) for s in steps[: len(vals_f)])
            ys = ", ".join(f"{v:.4g}" for v in vals_f)
            parts.append(
                "```mermaid\n"
                f"xychart-beta\n"
                f'  title "{name}"\n'
                f"  x-axis [{xs}]\n"
                f"  line [{ys}]\n"
                "```\n"
            )
    return "\n".join(parts) if parts else "_（无曲线数据）_\n"


def _update_exp_index(index: Path, exp_id: str, payload: dict[str, Any]) -> None:
    title = payload.get("title") or exp_id
    line = f"- [[{exp_id}]] — {title} · met={payload.get('target_met', False)}\n"
    if index.is_file():
        text = index.read_text(encoding="utf-8")
        if f"[[{exp_id}]]" in text:
            return
        index.write_text(text.rstrip() + "\n" + line, encoding="utf-8")
    else:
        index.write_text(
            "---\ntitle: Experiments\ntype: meta\n---\n\n# 实验索引\n\n" + line,
            encoding="utf-8",
        )
