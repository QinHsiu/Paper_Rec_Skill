"""Research brief artifact between clarify and Module 1 rewrite."""
from __future__ import annotations

from typing import Any


def build_research_brief(
    *,
    topic: str,
    must_answer: list[str] | None = None,
    out_of_scope: list[str] | None = None,
    packs: list[str] | None = None,
    constraints: list[str] | None = None,
    language: str = "en",
) -> dict[str, Any]:
    topic = (topic or "").strip()
    must = [m.strip() for m in (must_answer or []) if m and str(m).strip()]
    oos = [m.strip() for m in (out_of_scope or []) if m and str(m).strip()]
    pack_list = [p.strip() for p in (packs or []) if p and str(p).strip()]
    cons = [c.strip() for c in (constraints or []) if c and str(c).strip()]
    if not must and topic:
        must = [f"What are the main methods and open gaps for: {topic}?"]
    md_lines = [
        f"# Research brief",
        "",
        f"**Topic**: {topic}",
        "",
        "## Must answer",
    ]
    md_lines.extend(f"- {q}" for q in must)
    md_lines.extend(["", "## Out of scope"])
    if oos:
        md_lines.extend(f"- {q}" for q in oos)
    else:
        md_lines.append("- (none specified)")
    md_lines.extend(["", "## Suggested packs"])
    md_lines.extend(f"- {p}" for p in (pack_list or ["A", "H"]))
    if cons:
        md_lines.extend(["", "## Constraints"])
        md_lines.extend(f"- {c}" for c in cons)
    md_lines.extend(
        [
            "",
            "## Think checkpoint",
            "- Before each refine wave: log what is still unknown vs must-answer list.",
            "- Exit when each must-answer has ≥1 grounded evidence or MATERIAL GAP.",
        ]
    )
    return {
        "topic": topic,
        "must_answer": must,
        "out_of_scope": oos,
        "packs": pack_list or ["A", "H"],
        "constraints": cons,
        "language": language,
        "markdown": "\n".join(md_lines) + "\n",
    }
