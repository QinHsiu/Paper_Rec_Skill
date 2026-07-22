"""Figure ↔ caption ↔ body review (heuristic + pluggable VLM semantic pass)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

_FIG_LATEX = re.compile(
    r"(?is)\\begin\{figure\*?\}.*?\\caption\{(?P<cap>[^}]*)\}.*?\\label\{(?P<label>[^}]*)\}"
)
_FIG_MD_IMG = re.compile(r"(?im)^\!\[(?P<mdalt>[^\]]*)\]\((?P<path>[^)]+)\)(?P<mdrest>[^\n]*)")
_FIG_MD_CAPTION = re.compile(r"(?im)^\*\*Figure\s+(?P<fnum>\d+)[\.:]?\*\*\s*(?P<fcaption>.+)$")
_FIG_REF = re.compile(r"(?i)\b(?:Fig\.?|Figure|图)\s*(\d+)\b|\\ref\{(?P<label>[^}]+)\}")

_UP = re.compile(r"(?i)\b(increas|improv|rise|higher|better|gain|上升|提升|提高)\w*")
_DOWN = re.compile(r"(?i)\b(decreas|degrad|drop|lower|worse|fall|下降|降低)\w*")

VLM_PROMPT_TEMPLATE = """You are reviewing a scientific figure for consistency.

Abstract / context:
{abstract}

Caption:
{caption}

Main-text references to this figure:
{main_text_figrefs}

Examine the image and return JSON with keys:
Img_description, Img_review, Caption_review, Figrefs_review,
alignment_ok (bool), issues (list of short strings).
Be critical: flag caption claims the plot does not support.
"""


def extract_figures(text: str) -> list[dict[str, Any]]:
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
    for i, fig in enumerate(figures, start=1):
        if not fig.get("num"):
            fig["num"] = str(i)
    return figures


def _body_figrefs(text: str, fig_num: str) -> str:
    lines = []
    for line in (text or "").splitlines():
        if re.search(rf"(?i)\b(?:Fig\.?|Figure|图)\s*{re.escape(fig_num)}\b", line):
            lines.append(line.strip())
    return "\n".join(lines[:8])


def semantic_offline_review(text: str, figures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Caption↔body polarity / claim consistency without a vision model."""
    reviews = []
    for fig in figures:
        n = str(fig.get("num") or "")
        cap = fig.get("caption") or ""
        refs = _body_figrefs(text, n)
        issues = []
        cap_up, cap_down = bool(_UP.search(cap)), bool(_DOWN.search(cap))
        ref_up, ref_down = bool(_UP.search(refs)), bool(_DOWN.search(refs))
        if cap_up and ref_down:
            issues.append("caption_claims_increase_but_body_claims_decrease")
        if cap_down and ref_up:
            issues.append("caption_claims_decrease_but_body_claims_increase")
        if cap and not refs and re.search(r"(?i)as shown|见图|如图", text or ""):
            issues.append("body_mentions_figures_but_no_ref_to_this_num")
        # caption floats should appear near body refs or be flagged soft
        floats = re.findall(r"\d+\.\d+", cap)
        for f in floats[:3]:
            if refs and f not in refs and f not in (text or ""):
                issues.append(f"caption_float_{f}_missing_from_body")
        reviews.append(
            {
                "figure": n,
                "caption": cap[:200],
                "figrefs": refs[:400],
                "alignment_ok": len(issues) == 0,
                "issues": issues,
                "mode": "offline_semantic",
            }
        )
    return reviews


def vlm_prompt_bundle(
    text: str,
    figures: list[dict[str, Any]],
    *,
    abstract: str = "",
) -> list[dict[str, Any]]:
    """Prompts an agent/VLM can fill; does not call a model."""
    abs_ = abstract or (text or "")[:600]
    out = []
    for fig in figures:
        n = str(fig.get("num") or "")
        prompt = VLM_PROMPT_TEMPLATE.format(
            abstract=abs_,
            caption=fig.get("caption") or "",
            main_text_figrefs=_body_figrefs(text, n) or "(none)",
        )
        out.append(
            {
                "figure": n,
                "path": fig.get("path") or "",
                "prompt": prompt,
                "expects_json_keys": [
                    "Img_description",
                    "Img_review",
                    "Caption_review",
                    "Figrefs_review",
                    "alignment_ok",
                    "issues",
                ],
            }
        )
    return out


def merge_vlm_reviews(
    offline: list[dict[str, Any]],
    vlm_json: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not vlm_json:
        return offline
    by_n = {str(r.get("figure")): r for r in offline}
    merged = []
    for vr in vlm_json:
        n = str(vr.get("figure") or vr.get("num") or "")
        base = dict(by_n.get(n) or {"figure": n, "issues": [], "alignment_ok": True})
        issues = list(base.get("issues") or [])
        issues.extend(vr.get("issues") or [])
        if vr.get("alignment_ok") is False:
            base["alignment_ok"] = False
        if any(
            k in vr and vr[k] and "mismatch" in str(vr[k]).lower()
            for k in ("Caption_review", "Img_review", "Figrefs_review")
        ):
            base["alignment_ok"] = False
            issues.append("vlm_reported_mismatch")
        base["issues"] = issues
        base["vlm"] = {k: vr.get(k) for k in ("Img_description", "Img_review", "Caption_review", "Figrefs_review")}
        base["mode"] = "vlm+offline"
        merged.append(base)
    # keep offline-only figures
    seen = {str(m.get("figure")) for m in merged}
    for o in offline:
        if str(o.get("figure")) not in seen:
            merged.append(o)
    return merged


def review_figures(
    text: str,
    *,
    figure_paths: list[str] | None = None,
    abstract: str = "",
    vlm_reviews: list[dict[str, Any]] | None = None,
    vlm_callback: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    emit_vlm_prompts: bool = False,
) -> dict[str, Any]:
    """Structural + offline semantic (+ optional VLM JSON) figure review."""
    text = text or ""
    figures = extract_figures(text)
    # attach explicit paths if provided and figures lack paths
    if figure_paths:
        for i, p in enumerate(figure_paths):
            if i < len(figures) and not figures[i].get("path"):
                figures[i]["path"] = p

    issues: list[dict[str, str]] = []
    for i, fig in enumerate(figures, start=1):
        if not fig.get("caption"):
            issues.append({"figure": str(fig.get("num") or i), "issue": "missing_caption"})

    nums = {str(f.get("num")) for f in figures if f.get("num")}
    refs = []
    for m in _FIG_REF.finditer(text):
        refs.append({"num": m.group(1), "label": (m.group("label") or "").strip()})
    for r in refs:
        n = r.get("num")
        if n and n not in nums and len(figures) < int(n):
            issues.append({"figure": n, "issue": "ref_without_figure"})

    if re.search(r"(?i)as shown in (?:Fig|Figure|图)", text) and not figures:
        issues.append({"figure": "*", "issue": "body_claims_figure_but_none_defined"})

    for p in figure_paths or []:
        if p and not Path(p).is_file():
            issues.append({"figure": p, "issue": "file_missing"})

    offline = semantic_offline_review(text, figures)
    for rev in offline:
        if not rev.get("alignment_ok"):
            for iss in rev.get("issues") or []:
                issues.append({"figure": str(rev.get("figure")), "issue": str(iss)})

    applied_vlm = vlm_reviews
    if vlm_callback and not applied_vlm:
        applied_vlm = []
        for bundle in vlm_prompt_bundle(text, figures, abstract=abstract):
            try:
                applied_vlm.append(vlm_callback(bundle))
            except Exception as exc:  # noqa: BLE001
                applied_vlm.append(
                    {"figure": bundle["figure"], "alignment_ok": False, "issues": [f"vlm_error:{exc}"]}
                )

    semantic = merge_vlm_reviews(offline, applied_vlm)
    for rev in semantic:
        if rev.get("mode") == "vlm+offline" and not rev.get("alignment_ok"):
            for iss in rev.get("issues") or []:
                key = {"figure": str(rev.get("figure")), "issue": str(iss)}
                if key not in issues:
                    issues.append(key)

    out: dict[str, Any] = {
        "ok": len(issues) == 0,
        "figure_n": len(figures),
        "ref_n": len(refs),
        "figures": figures,
        "issues": issues,
        "issue_n": len(issues),
        "semantic": semantic,
        "vlm_applied": bool(applied_vlm),
    }
    if emit_vlm_prompts:
        out["vlm_prompts"] = vlm_prompt_bundle(text, figures, abstract=abstract)
    return out


def load_vlm_reviews_file(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return list(data.get("reviews") or data.get("vlm_reviews") or [])
