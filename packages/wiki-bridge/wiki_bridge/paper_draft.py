"""Multi-chapter Markdown paper draft pack from Cognitive Thread (not LaTeX)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import thread_evidence as te
from . import thread_store as ts
from .bibtex_export import export_bibtex
from .conventions import parse_frontmatter
from .related_work import build_related_work_outline
from .writer import resolve_content_root

VENUE_HINTS = {
    "cvpr": "Aim ~8 pages equivalent; keep Method/Experiments dense; Related Work concise.",
    "icml": "Emphasize problem setup + theory/algorithm clarity; Experiments with ablations.",
    "neurips": "Balance novelty statement with evidence; checklist-friendly claims.",
    "acl": "Related Work + positioning matter; cite threads of prior NLP work.",
    "generic": "Markdown frame only — paste into Overleaf / venue template yourself.",
}

CHAPTERS = (
    "abstract",
    "introduction",
    "related_work",
    "methodology",
    "experiments",
    "conclusion",
)


def _paper_title(wiki_root: Path, path: str) -> str:
    readme = resolve_content_root(wiki_root) / path.strip("/") / "README.md"
    if readme.is_file():
        meta, _ = parse_frontmatter(readme.read_text(encoding="utf-8"))
        return str(meta.get("title") or path)
    return path


def _ev_conf(e: dict[str, Any]) -> float:
    try:
        return float(e.get("confidence") if e.get("confidence") is not None else 0.6)
    except (TypeError, ValueError):
        return 0.6


def _cite_claim(cid: str) -> str:
    return f"[Claim: {cid}]"


def _cite_exp(eid: str) -> str:
    return f"[Exp: {eid}]"


def _cite_ev(eid: str) -> str:
    return f"[E: {eid}]"


def _hypothesis_block(data: dict[str, Any]) -> list[str]:
    return [
        "## Hypothesis anchor",
        "",
        data.get("hypothesis") or "_(none)_",
        "",
    ]


def _claims_with_evidence(
    wiki_root: Path,
    data: dict[str, Any],
    by_claim: dict[str, list[dict[str, Any]]],
    *,
    min_conf: float = 0.0,
) -> list[str]:
    lines: list[str] = []
    for c in data.get("claims") or []:
        cid = str(c.get("id") or "")
        lines.append(f"### {cid}: {c.get('text')} {_cite_claim(cid)}")
        lines.append("")
        lines.append(f"- Status: `{c.get('status')}`")
        evs = sorted(by_claim.get(cid, []), key=_ev_conf, reverse=True)
        if not evs:
            lines.append("- _(no evidence yet — fill gap)_")
        for e in evs:
            if _ev_conf(e) < min_conf:
                continue
            pp = e.get("paper_path") or ""
            title = _paper_title(wiki_root, pp) if pp else "(no paper)"
            quote = (e.get("quote") or "")[:200]
            conf = e.get("confidence")
            conf_s = f", conf={conf}" if conf is not None else ""
            exp = e.get("exp_id")
            exp_s = f" {_cite_exp(exp)}" if exp else ""
            lines.append(
                f"- {_cite_ev(e.get('evidence_id'))} ({e.get('support_status') or e.get('stance')}"
                f"{conf_s}) **{title}** (`{pp}`): {quote}{exp_s}"
            )
        lines.append("")
    return lines


def build_paper_draft(
    wiki_root: Path,
    thread_id: str,
    *,
    venue: str = "generic",
) -> dict[str, Any]:
    """Write drafts/paper_draft/*.md with inline [Claim:]/[Exp:]/[E:] citations."""
    wiki_root = Path(wiki_root).resolve()
    data = ts.load_thread(wiki_root, thread_id)
    evidences = te.list_evidences(wiki_root, thread_id)
    by_claim: dict[str, list[dict[str, Any]]] = {}
    for e in evidences:
        if str(e.get("gate")) not in ("accepted", "suggested"):
            continue
        by_claim.setdefault(str(e.get("claim_id") or ""), []).append(e)

    venue_key = (venue or "generic").lower().strip()
    venue_hint = VENUE_HINTS.get(venue_key, VENUE_HINTS["generic"])
    title = data.get("title") or thread_id
    out_dir = ts.thread_dir(wiki_root, thread_id) / "drafts" / "paper_draft"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Related work: reuse outline body under chapter file
    rw = build_related_work_outline(wiki_root, thread_id)
    rw_body = rw.get("markdown") or ""

    chapters: dict[str, str] = {}

    # abstract
    abs_lines = [
        f"# Abstract — {title}",
        "",
        f"> Traceable Markdown draft from Thread `{thread_id}`. Not a submission manuscript.",
        f"> Venue hint ({venue_key}): {venue_hint}",
        "",
        "One-paragraph sketch:",
        "",
        f"We investigate: {data.get('hypothesis') or '…'} "
        + " ".join(_cite_claim(str(c.get("id"))) for c in (data.get("claims") or [])[:3]),
        "",
        "Key claims:",
        "",
    ]
    for c in data.get("claims") or []:
        abs_lines.append(f"- {c.get('text')} {_cite_claim(c.get('id'))}")
    abs_lines.append("")
    chapters["abstract"] = "\n".join(abs_lines)

    # introduction
    intro = [
        f"# Introduction — {title}",
        "",
        f"> Auto frame · Thread `{thread_id}` · edit freely; keep citation tags for provenance.",
        "",
        *_hypothesis_block(data),
        "## Motivation",
        "",
        "State the problem and why existing work falls short (see Related Work).",
        "",
        "## Contributions (mapped to claims)",
        "",
    ]
    for c in data.get("claims") or []:
        intro.append(f"1. {c.get('text')} {_cite_claim(c.get('id'))}")
    intro.append("")
    gaps = data.get("evidence_gaps") or []
    if gaps:
        intro.extend(["## Open gaps motivating this work", ""])
        for g in gaps:
            intro.append(f"- claim `{g.get('claim_id')}` · {g.get('need')}: {g.get('note')}")
        intro.append("")
    chapters["introduction"] = "\n".join(intro)

    # related_work — chapter wrapper + outline
    chapters["related_work"] = (
        f"# Related Work — {title}\n\n"
        f"> Sourced from Thread evidences. Inline tags: [Claim:] / [E:].\n\n"
        + rw_body
    )

    # methodology
    method = [
        f"# Methodology — {title}",
        "",
        f"> Frame only. Venue: {venue_key}.",
        "",
        *_hypothesis_block(data),
        "## Approach overview",
        "",
        "Describe the method so each claim below is testable.",
        "",
        *_claims_with_evidence(wiki_root, data, by_claim, min_conf=0.0),
        "## Implementation notes",
        "",
        "1. Problem setup tied to gaps",
        "2. Model / algorithm steps",
        "3. Training / inference details",
        "",
    ]
    chapters["methodology"] = "\n".join(method)

    # experiments
    exp_lines = [
        f"# Experiments — {title}",
        "",
        f"> Link metrics to claims via {_cite_claim('C*')} / {_cite_exp('id')}.",
        "",
        "## Linked experiments",
        "",
    ]
    eids = data.get("experiment_ids") or []
    if eids:
        for eid in eids:
            exp_lines.append(f"- `{eid}` {_cite_exp(eid)}")
    else:
        exp_lines.append("- _(no experiments linked — sync-exp --thread)_")
    exp_lines.extend(["", "## Protocol sketch", ""])
    exp_lines.extend(
        [
            "1. Datasets / splits",
            "2. Metrics & target_score",
            "3. Ablations mapped to claims",
            "4. Failure cases still open",
            "",
            "## Evidence-backed claims",
            "",
        ]
    )
    exp_lines.extend(_claims_with_evidence(wiki_root, data, by_claim, min_conf=0.5))
    # metric evidences
    metric_ev = [e for e in evidences if e.get("kind") == "metric" or e.get("exp_id")]
    if metric_ev:
        exp_lines.extend(["## Metric evidences", ""])
        for e in metric_ev:
            exp_lines.append(
                f"- {_cite_ev(e.get('evidence_id'))} claim `{e.get('claim_id')}` "
                f"{e.get('metric_key')}={e.get('metric_value')} "
                f"{_cite_exp(e['exp_id']) if e.get('exp_id') else ''}"
            )
        exp_lines.append("")
    chapters["experiments"] = "\n".join(exp_lines)

    # conclusion
    conc = [
        f"# Conclusion — {title}",
        "",
        "Summarize supported claims and remaining gaps.",
        "",
        "## Supported / open",
        "",
    ]
    for c in data.get("claims") or []:
        conc.append(f"- `{c.get('status')}` {c.get('text')} {_cite_claim(c.get('id'))}")
    conc.append("")
    qs = data.get("open_questions") or []
    if qs:
        conc.extend(["## Open questions", ""])
        for q in qs:
            conc.append(f"- `{q.get('id')}` {q.get('text')}")
        conc.append("")
    high = [e for e in evidences if _ev_conf(e) >= 0.8]
    if high:
        conc.extend(["## High-confidence evidence to cite", ""])
        for e in high[:8]:
            conc.append(
                f"- {_cite_ev(e.get('evidence_id'))} → {_cite_claim(e.get('claim_id'))} "
                f"(conf={e.get('confidence')})"
            )
        conc.append("")
    chapters["conclusion"] = "\n".join(conc)

    paths: dict[str, str] = {}
    for name in CHAPTERS:
        fp = out_dir / f"{name}.md"
        fp.write_text(chapters[name], encoding="utf-8")
        paths[name] = str(fp.relative_to(wiki_root)).replace("\\", "/")

    # refs.bib
    paper_paths = list(data.get("paper_paths") or [])
    bib = export_bibtex(wiki_root, paper_paths)
    bib_path = out_dir / "refs.bib"
    bib_path.write_text(bib.get("bibtex") or "", encoding="utf-8")
    paths["refs.bib"] = str(bib_path.relative_to(wiki_root)).replace("\\", "/")

    readme = "\n".join(
        [
            f"# Paper draft pack — {title}",
            "",
            f"Thread: `{thread_id}` · venue hint: `{venue_key}`",
            "",
            "## Important",
            "",
            "This is a **traceable Markdown frame**, not a camera-ready LaTeX manuscript.",
            "Paste chapters into Overleaf / venue templates; keep `[Claim: …]` / `[Exp: …]` / `[E: …]` tags while editing so provenance stays visible.",
            "",
            f"Venue length hint: {venue_hint}",
            "",
            "## Files",
            "",
            *[f"- `{c}.md`" for c in CHAPTERS],
            "- `refs.bib`",
            "",
            "## Regenerate",
            "",
            "```bash",
            f"python -m wiki_bridge.cli paper-draft --wiki-root . --thread {thread_id} --venue {venue_key}",
            "```",
            "",
        ]
    )
    readme_path = out_dir / "README.md"
    readme_path.write_text(readme, encoding="utf-8")
    paths["README"] = str(readme_path.relative_to(wiki_root)).replace("\\", "/")

    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "paper_draft",
            "path": "drafts/paper_draft/",
            "venue": venue_key,
            "chapters": list(CHAPTERS),
        },
    )
    return {
        "thread_id": thread_id,
        "venue": venue_key,
        "dir": str(out_dir.relative_to(wiki_root)).replace("\\", "/"),
        "paths": paths,
        "chapters": {k: chapters[k] for k in CHAPTERS},
        "bibtex_count": bib.get("count", 0),
        "warnings": bib.get("warnings") or [],
    }
