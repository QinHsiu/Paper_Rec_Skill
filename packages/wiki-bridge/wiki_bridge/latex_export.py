"""Markdown draft → Overleaf-ready LaTeX pack (thin export).

Inspired by AutoResearchClaw templates/converter — Markdown stays source of truth.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_VENUE_CLASS = {
    "neurips": "article",
    "icml": "article",
    "iclr": "article",
    "cvpr": "article",
    "acl": "article",
    "generic": "article",
}


def _escape_tex(s: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out = []
    for ch in s:
        out.append(repl.get(ch, ch))
    return "".join(out)


def markdown_to_latex(md: str, *, title: str = "", venue: str = "generic") -> str:
    """Very small MD→LaTeX converter for draft packs (headings, paragraphs, cites)."""
    lines = (md or "").splitlines()
    body: list[str] = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            body.append(r"\begin{verbatim}" if in_code else r"\end{verbatim}")
            continue
        if in_code:
            body.append(line)
            continue
        if line.startswith("# "):
            body.append(r"\section{" + _escape_tex(line[2:].strip()) + "}")
        elif line.startswith("## "):
            body.append(r"\subsection{" + _escape_tex(line[3:].strip()) + "}")
        elif line.startswith("### "):
            body.append(r"\subsubsection{" + _escape_tex(line[4:].strip()) + "}")
        elif not line.strip():
            body.append("")
        else:
            cites: list[str] = []

            def _protect(m: re.Match[str]) -> str:
                cites.append(m.group(1))
                return f"@@CITE{len(cites) - 1}@@"

            protected = re.sub(r"\[([A-Za-z][A-Za-z0-9_:\-]*)\]", _protect, line)
            text = _escape_tex(protected)
            for i, k in enumerate(cites):
                text = text.replace(f"@@CITE{i}@@", f"\\cite{{{k}}}")
            body.append(text)

    cls = _VENUE_CLASS.get(venue.lower(), "article")
    title_tex = _escape_tex(title or "Paper draft")
    return "\n".join(
        [
            f"% Auto-exported by Paper_Rec latex-export (venue={venue})",
            f"\\documentclass{{{cls}}}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage{hyperref}",
            r"\usepackage{graphicx}",
            r"\usepackage{booktabs}",
            r"\begin{document}",
            r"\title{" + title_tex + "}",
            r"\author{Paper\_Rec draft}",
            r"\maketitle",
            "",
            *body,
            "",
            r"\bibliographystyle{plain}",
            r"\bibliography{references}",
            r"\end{document}",
            "",
        ]
    )


def export_latex_pack(
    draft_dir: Path,
    *,
    venue: str = "generic",
    title: str = "",
    bib_path: Path | None = None,
) -> dict[str, Any]:
    """Write main.tex (+ copy references.bib) under draft_dir/latex/."""
    draft_dir = Path(draft_dir)
    md_files = sorted(draft_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"no markdown drafts in {draft_dir}")
    # Prefer 00_outline / README / concatenated chapters
    preferred = None
    for name in ("paper.md", "00_outline.md", "README.md"):
        p = draft_dir / name
        if p.is_file():
            preferred = p
            break
    if preferred is None:
        # concatenate numbered chapters
        chunks = []
        for p in md_files:
            chunks.append(f"# {p.stem}\n\n" + p.read_text(encoding="utf-8"))
        md = "\n\n".join(chunks)
        title = title or draft_dir.parent.name
    else:
        md = preferred.read_text(encoding="utf-8")
        title = title or preferred.stem

    out = draft_dir / "latex"
    out.mkdir(parents=True, exist_ok=True)
    tex = markdown_to_latex(md, title=title, venue=venue)
    main = out / "main.tex"
    main.write_text(tex, encoding="utf-8")

    bib_src = bib_path or (draft_dir / "references.bib")
    bib_dst = out / "references.bib"
    if bib_src.is_file():
        bib_dst.write_text(bib_src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        bib_dst.write_text("% empty — run bibtex-export / citation-verify first\n", encoding="utf-8")

    readme = out / "README.md"
    readme.write_text(
        "# LaTeX export\n\n"
        f"- venue: `{venue}`\n"
        "- Open `main.tex` in Overleaf or local TeX.\n"
        "- Run `citation-verify` on `references.bib` before submit.\n",
        encoding="utf-8",
    )
    return {
        "latex_dir": str(out),
        "main_tex": str(main),
        "references_bib": str(bib_dst),
        "venue": venue,
    }
