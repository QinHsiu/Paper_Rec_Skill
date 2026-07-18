"""Section outlines for writing assist (not LaTeX manuscripts)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import thread_store as ts
from .related_work import build_related_work_outline


def build_section_outline(wiki_root: Path, thread_id: str, section: str = "method") -> dict[str, Any]:
    """Write drafts/{section}_outline.md from thread state."""
    section = (section or "method").lower().strip()
    if section in ("related", "related_work", "related-work"):
        return build_related_work_outline(wiki_root, thread_id)

    data = ts.load_thread(wiki_root, thread_id)
    title = data.get("title") or thread_id
    lines = [
        f"# {section.title()} Outline — {title}",
        "",
        f"> Auto frame from Thread `{thread_id}`. Not a manuscript.",
        "",
        "## Hypothesis anchor",
        "",
        data.get("hypothesis") or "_(none)_",
        "",
        "## Claims to address",
        "",
    ]
    for c in data.get("claims") or []:
        lines.append(f"- `{c.get('id')}` [{c.get('status')}] {c.get('text')}")
    lines.append("")
    lines.append("## Suggested bullets")
    lines.append("")
    if section == "method":
        lines.extend(
            [
                "1. Problem setup tied to open gaps",
                "2. Approach overview (link supporting papers)",
                "3. Training / inference details (link experiments)",
                "4. Comparison protocol vs baselines in membership list",
            ]
        )
    elif section in ("experiments", "experiment", "exp"):
        section = "experiments"
        lines.extend(
            [
                "1. Datasets / splits",
                "2. Metrics & target_score",
                "3. Ablations mapped to claims",
                "4. Failure cases / evidence gaps still open",
            ]
        )
        for eid in data.get("experiment_ids") or []:
            lines.append(f"- Linked exp: `{eid}`")
    else:
        lines.append(f"- Fill `{section}` using accepted evidences and member papers.")
    lines.append("")
    md = "\n".join(lines)
    out_dir = ts.thread_dir(wiki_root, thread_id) / "drafts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{section}_outline.md"
    out_path.write_text(md, encoding="utf-8")
    ts.append_event(
        wiki_root,
        thread_id,
        {"kind": "section_outline", "section": section, "path": f"drafts/{section}_outline.md"},
    )
    return {
        "thread_id": thread_id,
        "section": section,
        "path": str(out_path.relative_to(wiki_root)).replace("\\", "/"),
        "markdown": md,
    }
