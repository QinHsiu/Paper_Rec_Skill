"""Related Work outline from Cognitive Thread (not a manuscript)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import thread_evidence as te
from . import thread_store as ts
from .conventions import parse_frontmatter
from .writer import resolve_content_root


def _paper_title(wiki_root: Path, path: str) -> str:
    readme = resolve_content_root(wiki_root) / path.strip("/") / "README.md"
    if readme.is_file():
        meta, _ = parse_frontmatter(readme.read_text(encoding="utf-8"))
        return str(meta.get("title") or path)
    return path


def build_related_work_outline(wiki_root: Path, thread_id: str) -> dict[str, Any]:
    wiki_root = Path(wiki_root).resolve()
    data = ts.load_thread(wiki_root, thread_id)
    evidences = te.list_evidences(wiki_root, thread_id)
    by_claim: dict[str, list[dict[str, Any]]] = {}
    for e in evidences:
        if str(e.get("gate")) not in ("accepted", "suggested"):
            continue
        by_claim.setdefault(str(e.get("claim_id") or ""), []).append(e)

    lines = [
        f"# Related Work Outline — {data.get('title') or thread_id}",
        "",
        f"> Auto-generated from Cognitive Thread `{thread_id}`. Edit before use in a paper.",
        "",
        "## Hypothesis",
        "",
        data.get("hypothesis") or "_(none)_",
        "",
    ]

    claims = data.get("claims") or []
    if claims:
        lines.append("## By claim")
        lines.append("")
        for c in claims:
            cid = c.get("id")
            lines.append(f"### {cid}: {c.get('text')}")
            lines.append("")
            lines.append(f"- Status: `{c.get('status')}`")
            for e in by_claim.get(str(cid), []):
                pp = e.get("paper_path") or ""
                title = _paper_title(wiki_root, pp) if pp else "(no paper)"
                quote = (e.get("quote") or "")[:160]
                lines.append(
                    f"- [{e.get('evidence_id')}] ({e.get('stance')}, {e.get('gate')}) "
                    f"**{title}** (`{pp}`): {quote}"
                )
            lines.append("")
    else:
        lines.append("## Papers (membership only)")
        lines.append("")
        for pp in data.get("paper_paths") or []:
            lines.append(f"- {_paper_title(wiki_root, pp)} (`{pp}`)")
        lines.append("")

    gaps = data.get("evidence_gaps") or []
    if gaps:
        lines.append("## Open gaps (for positioning)")
        lines.append("")
        for g in gaps:
            lines.append(f"- claim `{g.get('claim_id')}` · {g.get('need')}: {g.get('note')}")
        lines.append("")

    qs = data.get("open_questions") or []
    if qs:
        lines.append("## Open questions")
        lines.append("")
        for q in qs:
            lines.append(f"- `{q.get('id')}` {q.get('text')}")
        lines.append("")

    md = "\n".join(lines)
    out_dir = ts.thread_dir(wiki_root, thread_id) / "drafts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "related_work_outline.md"
    out_path.write_text(md, encoding="utf-8")
    ts.append_event(
        wiki_root,
        thread_id,
        {"kind": "related_work_outline", "path": "drafts/related_work_outline.md"},
    )
    return {
        "thread_id": thread_id,
        "path": str(out_path.relative_to(wiki_root)).replace("\\", "/"),
        "markdown": md,
    }
