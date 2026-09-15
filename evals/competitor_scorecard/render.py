# evals/competitor_scorecard/render.py
from __future__ import annotations

from pathlib import Path

from schema import CLOSED_COMPETITORS, DIMENSIONS, OSS_COMPETITORS


def render_scorecard(data: dict) -> str:
    lines = [
        "# Competitor Scorecard",
        "",
        f"As of: {data.get('as_of', '')}",
        "",
        "Cell = Paper_Rec relative to competitor: 领先 / 持平 / 落后 / 不适用.",
        "",
    ]
    for axis, title in (
        ("A", "Retrieval & recommendation"),
        ("B", "Deep research & trust"),
        ("C", "Thread & workflow"),
    ):
        dims = [d for d in DIMENSIONS if d["axis"] == axis]
        lines.append(f"## {axis} — {title}")
        lines.append("")
        header = ["Competitor"] + [d["id"] for d in dims]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for name in list(OSS_COMPETITORS) + list(CLOSED_COMPETITORS):
            row = data["competitors"][name]
            cells = row["cells"]
            vals = [name] + [cells[d["id"]]["state"] for d in dims]
            lines.append("| " + " | ".join(vals) + " |")
        lines.append("")
    lines.append("## Notes (selected gaps)")
    lines.append("")
    for name in list(OSS_COMPETITORS) + list(CLOSED_COMPETITORS):
        row = data["competitors"][name]
        for did, cell in row["cells"].items():
            if cell["state"] == "落后":
                ev = cell.get("evidence", "code")
                lines.append(f"- **{name} / {did}**: {cell['note']} `({ev})`")
    lines.append("")
    return "\n".join(lines)


def write_docs(repo_root: Path, data: dict) -> Path:
    out = repo_root / "docs" / "COMPETITOR_SCORECARD.md"
    out.write_text(render_scorecard(data), encoding="utf-8")
    return out
