"""Survey / related-work writer: outline merge + subsection drafts from papers."""
from __future__ import annotations

import re
from typing import Any

from .evidence_ground import abstract_supports_claim


def _title(p: dict[str, Any]) -> str:
    return str(p.get("title") or p.get("paper_path") or "untitled")


def _abstract(p: dict[str, Any]) -> str:
    return str(p.get("abstract") or p.get("summary") or p.get("quote") or "")[:800]


def draft_outline_chunks(papers: list[dict[str, Any]], *, chunk_size: int = 8) -> list[dict[str, Any]]:
    """Split papers into batches; each batch yields coarse section headings."""
    chunks: list[dict[str, Any]] = []
    batch: list[dict[str, Any]] = []
    for p in papers or []:
        if not isinstance(p, dict):
            continue
        batch.append(p)
        if len(batch) >= chunk_size:
            chunks.append(_outline_from_batch(batch))
            batch = []
    if batch:
        chunks.append(_outline_from_batch(batch))
    return chunks


def _outline_from_batch(batch: list[dict[str, Any]]) -> dict[str, Any]:
    # Heuristic sections from keyword buckets
    buckets: dict[str, list[dict[str, Any]]] = {
        "Foundations": [],
        "Methods": [],
        "Applications": [],
        "Evaluation & Benchmarks": [],
    }
    for p in batch:
        text = f"{_title(p)} {_abstract(p)}".lower()
        if any(k in text for k in ("benchmark", "dataset", "evaluation", "leaderboard")):
            buckets["Evaluation & Benchmarks"].append(p)
        elif any(k in text for k in ("survey", "review", "taxonomy", "foundation")):
            buckets["Foundations"].append(p)
        elif any(k in text for k in ("application", "clinical", "robot", "industry")):
            buckets["Applications"].append(p)
        else:
            buckets["Methods"].append(p)
    sections = []
    for name, items in buckets.items():
        if not items:
            continue
        sections.append(
            {
                "title": name,
                "description": f"Papers on {name.lower()} in this batch ({len(items)}).",
                "paper_keys": [_title(p) for p in items[:12]],
            }
        )
    return {"sections": sections, "paper_n": len(batch)}


def merge_outlines(outlines: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge section titles; dedupe overlapping subsections by normalized title."""
    merged: dict[str, dict[str, Any]] = {}
    for ol in outlines or []:
        for sec in ol.get("sections") or []:
            title = str(sec.get("title") or "").strip()
            key = re.sub(r"\s+", " ", title.lower())
            if key not in merged:
                merged[key] = {
                    "title": title,
                    "description": sec.get("description") or "",
                    "paper_keys": list(sec.get("paper_keys") or []),
                }
            else:
                keys = merged[key]["paper_keys"]
                for pk in sec.get("paper_keys") or []:
                    if pk not in keys:
                        keys.append(pk)
                if len(str(sec.get("description") or "")) > len(str(merged[key]["description"])):
                    merged[key]["description"] = sec.get("description")
    sections = list(merged.values())
    return {"sections": sections, "section_n": len(sections)}


def edit_final_outline(outline: dict[str, Any]) -> dict[str, Any]:
    """Drop empty / near-duplicate sections."""
    seen: set[str] = set()
    kept = []
    for sec in outline.get("sections") or []:
        title = str(sec.get("title") or "")
        norm = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", title.lower())
        if not norm or norm in seen:
            continue
        if not sec.get("paper_keys"):
            continue
        seen.add(norm)
        kept.append(sec)
    return {"sections": kept, "section_n": len(kept)}


def write_subsection(
    section: dict[str, Any],
    papers: list[dict[str, Any]],
    *,
    rag_k: int = 5,
) -> dict[str, Any]:
    """Draft a subsection paragraph from top-k papers matching section description."""
    desc = str(section.get("description") or section.get("title") or "")
    ranked = []
    for p in papers or []:
        if not isinstance(p, dict):
            continue
        r = abstract_supports_claim(desc, _abstract(p), min_overlap=2)
        ranked.append((int(r.get("overlap_n") or 0), p))
    ranked.sort(key=lambda x: x[0], reverse=True)
    chosen = [p for _, p in ranked[:rag_k] if _abstract(p) or _title(p)]
    if not chosen:
        # fallback to paper_keys titles
        keys = set(section.get("paper_keys") or [])
        chosen = [p for p in papers if _title(p) in keys][:rag_k]

    lines = [
        f"### {section.get('title')}",
        "",
        str(section.get("description") or ""),
        "",
    ]
    cites = []
    for i, p in enumerate(chosen, start=1):
        key = f"P{i}"
        cites.append(key)
        abs_ = _abstract(p)[:220] or "(no abstract)"
        lines.append(f"- [{key}] **{_title(p)}** ({p.get('year') or 'n.d.'}): {abs_}")
    lines.append("")
    synth = (
        f"Work in this area includes {', '.join('['+c+']' for c in cites)}. "
        f"Compared to adjacent lines, these papers emphasize {section.get('title')}."
    )
    lines.append(synth)
    lines.append("")
    return {
        "title": section.get("title"),
        "markdown": "\n".join(lines),
        "paper_n": len(chosen),
        "cite_keys": cites,
    }


def build_survey_draft(papers: list[dict[str, Any]], *, chunk_size: int = 8, rag_k: int = 5) -> dict[str, Any]:
    raw = draft_outline_chunks(papers, chunk_size=chunk_size)
    merged = merge_outlines(raw)
    final = edit_final_outline(merged)
    sections_md = []
    meta = []
    for sec in final.get("sections") or []:
        sub = write_subsection(sec, papers, rag_k=rag_k)
        sections_md.append(sub["markdown"])
        meta.append({"title": sub["title"], "paper_n": sub["paper_n"], "cite_keys": sub["cite_keys"]})
    md = "# Related Work (survey draft)\n\n" + "\n".join(sections_md)
    return {
        "outline_chunks": len(raw),
        "section_n": final.get("section_n"),
        "sections": meta,
        "markdown": md,
    }
