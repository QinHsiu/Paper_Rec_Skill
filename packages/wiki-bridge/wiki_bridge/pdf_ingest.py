"""Light PDF / text ingest → section Markdown beside a wiki paper page."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .conventions import parse_frontmatter
from .writer import resolve_content_root


SECTION_HINTS = (
    ("abstract", re.compile(r"^\s*(abstract|摘要)\b", re.I)),
    ("introduction", re.compile(r"^\s*(1[\.\s]+)?(introduction|引言)\b", re.I)),
    ("method", re.compile(r"^\s*(\d[\.\s]+)?(method|approach|methodology|方法)\b", re.I)),
    ("experiments", re.compile(r"^\s*(\d[\.\s]+)?(experiment|evaluation|结果|实验)\b", re.I)),
    ("conclusion", re.compile(r"^\s*(\d[\.\s]+)?(conclusion|讨论|结论)\b", re.I)),
)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text; prefers pymupdf, falls back to raw bytes decode for .txt."""
    if pdf_path.suffix.lower() in {".txt", ".md"}:
        return pdf_path.read_text(encoding="utf-8", errors="ignore")
    try:
        import fitz  # pymupdf

        doc = fitz.open(pdf_path)
        parts = []
        for page in doc:
            parts.append(page.get_text("text"))
        doc.close()
        return "\n".join(parts)
    except ImportError as e:
        raise RuntimeError(
            "PDF ingest requires pymupdf: pip install pymupdf "
            "(or pass a .txt/.md extraction instead of .pdf)"
        ) from e


def split_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    sections: dict[str, list[str]] = {"body": []}
    current = "body"
    for line in lines:
        hit = None
        for name, pat in SECTION_HINTS:
            if pat.search(line.strip()[:80]):
                hit = name
                break
        if hit:
            current = hit
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "".join(v).strip()}


def render_fulltext_md(title: str, sections: dict[str, str], *, source: str = "") -> str:
    parts = [
        "---",
        f'title: "{title} fulltext"',
        "type: fulltext",
        f'source: "{source}"',
        "---",
        "",
        f"# {title} — Fulltext (auto)",
        "",
        "> Auto-extracted. Review before accepting claim/evidence candidates.",
        "",
    ]
    order = ["abstract", "introduction", "method", "experiments", "conclusion", "body"]
    seen = set()
    for key in order:
        if key in sections and key not in seen:
            parts.append(f"## {key.title()}")
            parts.append("")
            parts.append(sections[key][:20000])
            parts.append("")
            seen.add(key)
    for key, val in sections.items():
        if key in seen:
            continue
        parts.append(f"## {key}")
        parts.append("")
        parts.append(val[:20000])
        parts.append("")
    return "\n".join(parts)


def paper_dir(wiki_root: Path, paper_path: str) -> Path:
    pages = resolve_content_root(wiki_root)
    return pages / paper_path.strip("/")


def ingest_pdf(
    wiki_root: Path,
    pdf_path: Path,
    paper_path: str,
    *,
    title: str = "",
) -> dict[str, Any]:
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    d = paper_dir(wiki_root, paper_path)
    if not d.is_dir():
        raise FileNotFoundError(f"wiki paper path not found: {paper_path}")
    text = extract_pdf_text(pdf_path)
    sections = split_sections(text)
    readme = d / "README.md"
    if not title and readme.is_file():
        meta, _ = parse_frontmatter(readme.read_text(encoding="utf-8"))
        title = str(meta.get("title") or paper_path.split("/")[-1])
    title = title or paper_path.split("/")[-1]
    out = d / "fulltext.md"
    out.write_text(
        render_fulltext_md(title, sections, source=str(pdf_path.name)),
        encoding="utf-8",
    )
    return {
        "paper_path": paper_path.strip("/"),
        "fulltext_path": f"{paper_path.strip('/')}/fulltext.md",
        "sections": list(sections.keys()),
        "chars": len(text),
    }


def suggest_claims_from_fulltext(
    wiki_root: Path,
    paper_path: str,
    *,
    max_claims: int = 5,
) -> list[dict[str, Any]]:
    """Heuristic claim candidates from abstract/conclusion (gate=suggested only)."""
    d = paper_dir(wiki_root, paper_path)
    ft = d / "fulltext.md"
    if not ft.is_file():
        raise FileNotFoundError(f"fulltext.md missing for {paper_path}; run pdf-ingest first")
    _, body = parse_frontmatter(ft.read_text(encoding="utf-8"))
    # Prefer abstract + conclusion blocks
    chunks: list[str] = []
    for sec in ("Abstract", "Conclusion", "Experiments", "Method"):
        m = re.search(rf"## {sec}\s*\n(.*?)(?=\n## |\Z)", body, re.S | re.I)
        if m:
            chunks.append(m.group(1))
    blob = "\n".join(chunks) or body
    sents = re.split(r"(?<=[。.!?])\s+", blob)
    cands: list[dict[str, Any]] = []
    verbs = re.compile(
        r"\b(show|demonstrate|propose|achieve|outperform|find|suggest|indicate|"
        r"证明|提出|优于|表明|发现)\b",
        re.I,
    )
    for s in sents:
        s = s.strip()
        if len(s) < 40 or len(s) > 280:
            continue
        if not verbs.search(s):
            continue
        cands.append(
            {
                "text": s,
                "paper_path": paper_path.strip("/"),
                "source_section": "fulltext",
                "gate": "suggested",
            }
        )
        if len(cands) >= max_claims:
            break
    return cands


def apply_claim_suggestions(
    wiki_root: Path,
    thread_id: str,
    paper_path: str,
    *,
    max_claims: int = 3,
    also_evidence: bool = True,
) -> dict[str, Any]:
    """Append suggested claims (+ optional quote evidences) to thread. Never auto-accept."""
    from . import thread_store as ts
    from . import thread_evidence as te

    cands = suggest_claims_from_fulltext(wiki_root, paper_path, max_claims=max_claims)
    data = ts.load_thread(wiki_root, thread_id)
    claims = list(data.get("claims") or [])
    existing_ids = {str(c.get("id")) for c in claims}
    n = 0
    for c in claims:
        m = re.match(r"^C(\d+)$", str(c.get("id") or ""), re.I)
        if m:
            n = max(n, int(m.group(1)))
    added_claims = []
    added_ev = []
    for cand in cands:
        n += 1
        cid = f"C{n}"
        while cid in existing_ids:
            n += 1
            cid = f"C{n}"
        existing_ids.add(cid)
        rec = {
            "id": cid,
            "text": cand["text"],
            "status": "open",
            "evidence_ids": [],
            "gate": "suggested",
            "source": "pdf_suggest",
            "paper_path": paper_path.strip("/"),
        }
        claims.append(rec)
        added_claims.append(rec)
        if also_evidence:
            ev = te.add_evidence(
                wiki_root,
                thread_id,
                claim_id=cid,
                kind="quote",
                paper_path=paper_path.strip("/"),
                quote=cand["text"][:500],
                stance="supports",
                gate="suggested",
                by="pdf_suggest",
            )
            added_ev.append(ev)
            rec["evidence_ids"] = [ev["evidence_id"]]
    data["claims"] = claims
    ts.save_thread(wiki_root, data)
    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "claim_suggest",
            "paper_path": paper_path.strip("/"),
            "count": len(added_claims),
            "claim_ids": [c["id"] for c in added_claims],
            "by": "pdf_suggest",
        },
    )
    return {"claims": added_claims, "evidences": added_ev}
