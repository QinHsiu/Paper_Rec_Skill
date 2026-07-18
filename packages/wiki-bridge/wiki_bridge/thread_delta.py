"""Thread Watch / Delta — Phase B cognitive briefs (not public survey factory)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import thread_store as ts
from .conventions import parse_frontmatter
from .writer import resolve_content_root


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _paper_cards(wiki_root: Path) -> list[dict[str, Any]]:
    pages = resolve_content_root(wiki_root)
    cards: list[dict[str, Any]] = []
    for path in sorted(pages.rglob("README.md")):
        rel_parts = path.relative_to(pages).parts
        if any(p.startswith("_") for p in rel_parts):
            continue
        if len(rel_parts) < 4:  # keyword/year/slug/README.md
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, body = parse_frontmatter(text)
        wiki_path = "/".join(rel_parts[:-1])
        summary = str(meta.get("summary") or "")
        if not summary:
            for line in body.splitlines():
                s = line.strip()
                if s and not s.startswith("#") and not s.startswith(">"):
                    summary = s[:280]
                    break
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        cards.append(
            {
                "path": wiki_path,
                "title": meta.get("title") or rel_parts[-2],
                "summary": summary,
                "tags": tags,
                "keyword": meta.get("keyword") or rel_parts[0],
                "added_at": str(meta.get("added_at") or meta.get("started_at") or "")[:10],
            }
        )
    return cards


def _exp_cards(wiki_root: Path) -> list[dict[str, Any]]:
    workspace = ts.workspace_from_wiki_root(wiki_root)
    root = workspace / "content" / "exp"
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        readme = d / "README.md"
        meta: dict[str, Any] = {"id": d.name}
        if readme.is_file():
            m, _ = parse_frontmatter(readme.read_text(encoding="utf-8"))
            meta.update(m)
        out.append(
            {
                "id": d.name,
                "title": meta.get("title") or d.name,
                "status": meta.get("status") or "",
                "paper_refs": meta.get("paper_refs") or "",
            }
        )
    return out


def run_delta(
    wiki_root: Path,
    thread_id: str,
    *,
    mode: str = "auto",
    threshold: float = 0.45,
    persist: bool = True,
) -> dict[str, Any]:
    """
    Modes:
      - new_digest: no history → top related candidates
      - diff_brief: papers not yet in membership, scored since last_delta
      - gap_focus: prioritize evidence_gaps
      - exp_bridge: relate open claims/gaps to experiments
      - auto: pick among the above
    """
    data = ts.load_thread(wiki_root, thread_id)
    watch = dict(data.get("watch") or {})
    members = set(data.get("paper_paths") or [])
    gaps = data.get("evidence_gaps") or []
    claims = data.get("claims") or []
    last = watch.get("last_delta_at")
    events = ts.list_events(wiki_root, thread_id, limit=500)
    has_delta = any(e.get("kind") == "delta" for e in events)

    if mode == "auto":
        if not has_delta and not members:
            mode = "new_digest"
        elif gaps:
            mode = "gap_focus"
        elif data.get("experiment_ids"):
            mode = "exp_bridge"
        else:
            mode = "diff_brief"

    papers = _paper_cards(wiki_root)
    scored: list[dict[str, Any]] = []
    for p in papers:
        if mode in ("diff_brief", "new_digest") and p["path"] in members:
            continue
        if mode == "diff_brief" and last and p.get("added_at") and p["added_at"] < str(last)[:10]:
            # still allow high-relevance non-members regardless of date
            pass
        s = ts.score_paper_against_thread(
            data,
            title=str(p.get("title") or ""),
            summary=str(p.get("summary") or ""),
            tags=list(p.get("tags") or []),
            keyword=str(p.get("keyword") or ""),
        )
        if mode == "gap_focus":
            # boost gap_match
            s["R"] = round(min(1.0, s["R"] * 0.7 + 0.3 * float(s["factors"].get("gap_match", 0))), 4)
        if s["R"] < threshold and mode != "exp_bridge":
            continue
        scored.append({**p, **s})
    scored.sort(key=lambda x: x.get("R") or 0, reverse=True)
    top = scored[:15]

    exp_notes: list[str] = []
    if mode == "exp_bridge":
        for e in _exp_cards(wiki_root):
            eid = e["id"]
            linked = eid in set(data.get("experiment_ids") or [])
            refs = str(e.get("paper_refs") or "")
            exp_notes.append(
                f"- `{eid}` — {e.get('title')} · linked={linked} · paper_refs={refs or '—'}"
            )

    claim_suggestions = propose_claim_updates(wiki_root, thread_id, apply=False)

    lines = [
        f"# Thread Delta — {data.get('title')} (`{thread_id}`)",
        "",
        f"- mode: `{mode}`",
        f"- generated: `{ts.utc_now_iso()}`",
        f"- hypothesis: {(data.get('hypothesis') or '—')[:200]}",
        "",
        "## Candidates",
        "",
    ]
    if top:
        for p in top:
            lines.append(
                f"- R={p['R']:.2f} `{p['path']}` — {p.get('title')} "
                f"· {', '.join(p.get('rationale') or []) or '—'}"
            )
    else:
        lines.append("- (none above threshold)")

    lines.extend(["", "## Evidence gaps", ""])
    if gaps:
        for g in gaps:
            lines.append(f"- claim `{g.get('claim_id')}` need={g.get('need')}: {g.get('note')}")
    else:
        lines.append("- (none)")

    if exp_notes:
        lines.extend(["", "## Experiments", ""] + exp_notes)

    if claim_suggestions.get("suggestions"):
        lines.extend(["", "## Claim update suggestions (gate=suggested)", ""])
        for s in claim_suggestions["suggestions"]:
            lines.append(
                f"- `{s['claim_id']}` → **{s['status']}** — {s.get('reason', '')}"
            )

    md = "\n".join(lines) + "\n"
    result: dict[str, Any] = {
        "thread_id": thread_id,
        "mode": mode,
        "candidates": [
            {"path": p["path"], "title": p.get("title"), "R": p["R"], "rationale": p.get("rationale")}
            for p in top
        ],
        "claim_suggestions": claim_suggestions.get("suggestions") or [],
        "markdown": md,
        "delta_path": None,
    }

    if persist:
        d = ts.thread_dir(wiki_root, thread_id) / "deltas"
        d.mkdir(parents=True, exist_ok=True)
        out = d / f"{_utc_date()}-{mode}.md"
        out.write_text(md, encoding="utf-8")
        try:
            rel = out.resolve().relative_to(Path(wiki_root).resolve()).as_posix()
        except ValueError:
            rel = f"content/threads/{thread_id}/deltas/{out.name}"
        result["delta_path"] = rel
        watch["last_delta_at"] = ts.utc_now_iso()
        watch["enabled"] = bool(watch.get("enabled", True))
        data["watch"] = watch
        ts.save_thread(wiki_root, data)
        ts.append_event(
            wiki_root,
            thread_id,
            {
                "kind": "delta",
                "mode": mode,
                "added_papers": [p["path"] for p in top[:10]],
                "new_gaps": [],
                "path": rel,
            },
        )
        # also emit claim suggestions as ledger events
        for s in claim_suggestions.get("suggestions") or []:
            ts.append_event(
                wiki_root,
                thread_id,
                {
                    "kind": "claim_update",
                    "claim_id": s["claim_id"],
                    "status": s["status"],
                    "gate": "suggested",
                    "reason": s.get("reason"),
                    "by": "delta",
                },
            )

    return result


def propose_claim_updates(
    wiki_root: Path,
    thread_id: str,
    *,
    apply: bool = False,
    min_support: int = 1,
) -> dict[str, Any]:
    """
    Semi-auto claim status proposals from accepted member papers + scoring.
    Never flips status unless apply=True (explicit gate accept).
    """
    data = ts.load_thread(wiki_root, thread_id)
    papers = {p["path"]: p for p in _paper_cards(wiki_root)}
    suggestions: list[dict[str, Any]] = []
    for claim in data.get("claims") or []:
        cid = str(claim.get("id") or "")
        status = str(claim.get("status") or "open")
        if status not in ("open", ""):
            continue
        support = 0
        reasons: list[str] = []
        for path in data.get("paper_paths") or []:
            p = papers.get(path)
            if not p:
                continue
            scored = ts.score_paper_against_thread(
                data,
                title=str(p.get("title") or ""),
                summary=str(p.get("summary") or ""),
                tags=list(p.get("tags") or []),
                keyword=str(p.get("keyword") or ""),
            )
            if cid in (scored.get("claim_ids") or []) and scored["R"] >= 0.5:
                support += 1
                reasons.append(path)
        if support >= min_support:
            suggestions.append(
                {
                    "claim_id": cid,
                    "status": "supported",
                    "reason": f"{support} member paper(s): {', '.join(reasons[:5])}",
                    "gate": "suggested",
                }
            )
    if apply:
        for s in suggestions:
            accept_claim_update(
                wiki_root,
                thread_id,
                s["claim_id"],
                s["status"],
                by="auto",
                reason=s.get("reason"),
            )
    return {"thread_id": thread_id, "suggestions": suggestions}


def accept_claim_update(
    wiki_root: Path,
    thread_id: str,
    claim_id: str,
    status: str,
    *,
    by: str = "user",
    reason: str = "",
) -> dict[str, Any]:
    data = ts.load_thread(wiki_root, thread_id)
    claims = list(data.get("claims") or [])
    found = False
    for c in claims:
        if str(c.get("id")) == claim_id:
            c["status"] = status
            found = True
            break
    if not found:
        raise KeyError(claim_id)
    data["claims"] = claims
    ts.save_thread(wiki_root, data)
    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "claim_update",
            "claim_id": claim_id,
            "status": status,
            "gate": "accepted",
            "by": by,
            "reason": reason,
        },
    )
    return data
