"""Figure ↔ caption ↔ body consistency checks (heuristic; VLM optional hook)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_FIG_LATEX = re.compile(
    r"(?is)\\begin\{figure\*?\}.*?\\caption\{(?P<cap>[^}]*)\}.*?\\label\{(?P<label>[^}]*)\}"
)
_FIG_MD_IMG = re.compile(r"(?im)^\!\[(?P<mdalt>[^\]]*)\]\((?P<path>[^)]+)\)(?P<mdrest>[^\n]*)")
_FIG_MD_CAPTION = re.compile(r"(?im)^\*\*Figure\s+(?P<fnum>\d+)[\.:]?\*\*\s*(?P<fcaption>.+)$")
_FIG_REF = re.compile(r"(?i)\b(?:Fig\.?|Figure|图)\s*(\d+)\b|\\ref\{(?P<label>[^}]+)\}")


def review_figures(text: str, *, figure_paths: list[str] | None = None) -> dict[str, Any]:
    """Detect missing captions, orphan refs, and empty alts — no VLM required."""
    text = text or ""
    figures: list[dict[str, Any]] = []
    for m in _FIG_LATEX.finditer(text):
        gd = m.groupdict()
        figures.append(
            {
                "caption": (gd.get("cap") or "").strip(),
                "label": (gd.get("label") or "").strip(),
                "path": "",
                "num": None,
            }
        )
    for m in _FIG_MD_IMG.finditer(text):
        gd = m.groupdict()
        figures.append(
            {
                "caption": (gd.get("mdalt") or "").strip(),
                "label": "",
                "path": (gd.get("path") or "").strip(),
                "num": None,
            }
        )
    for m in _FIG_MD_CAPTION.finditer(text):
        gd = m.groupdict()
        figures.append(
            {
                "caption": (gd.get("fcaption") or "").strip(),
                "label": "",
                "path": "",
                "num": gd.get("fnum"),
            }
        )
    refs = []
    for m in _FIG_REF.finditer(text):
        refs.append({"num": m.group(1), "label": (m.group("label") or "").strip()})

    issues: list[dict[str, str]] = []
    for i, fig in enumerate(figures, start=1):
        if not fig.get("caption"):
            issues.append({"figure": str(i), "issue": "missing_caption"})
        if fig.get("path") and figure_paths is not None:
            # existence check if paths provided
            pass
    # orphan refs: referenced number with no figure
    nums = {str(f.get("num")) for f in figures if f.get("num")}
    # also assign implicit numbers
    if not nums and figures:
        nums = {str(i) for i in range(1, len(figures) + 1)}
    for r in refs:
        n = r.get("num")
        if n and n not in nums and len(figures) < int(n):
            issues.append({"figure": n, "issue": "ref_without_figure"})

    # body claims "as shown in Fig" without any figure
    if re.search(r"(?i)as shown in (?:Fig|Figure|图)", text) and not figures:
        issues.append({"figure": "*", "issue": "body_claims_figure_but_none_defined"})

    missing_files = []
    for p in figure_paths or []:
        if p and not Path(p).is_file():
            missing_files.append(p)
            issues.append({"figure": p, "issue": "file_missing"})

    return {
        "ok": len(issues) == 0,
        "figure_n": len(figures),
        "ref_n": len(refs),
        "figures": figures,
        "issues": issues,
        "issue_n": len(issues),
        "vlm_hook": "optional — attach vision model later for caption↔plot semantic check",
    }
