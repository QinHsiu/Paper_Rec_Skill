"""Research Thread (Cognitive Thread v2) — Git-backed store under content/threads/."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .conventions import slugify


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def workspace_from_wiki_root(wiki_root: Path) -> Path:
    root = wiki_root.resolve()
    if (root / "content").is_dir():
        return root
    if root.name == "content":
        return root.parent
    if root.name == "pages" and root.parent.name == "wiki":
        return root.parents[2]
    return root


def threads_dir(wiki_root: Path) -> Path:
    d = workspace_from_wiki_root(wiki_root) / "content" / "threads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def thread_dir(wiki_root: Path, thread_id: str) -> Path:
    tid = slugify(thread_id, max_len=80) if thread_id else ""
    if not tid:
        raise ValueError("thread_id required")
    return threads_dir(wiki_root) / tid


def default_thread(
    thread_id: str,
    title: str,
    *,
    hypothesis: str = "",
    keywords: list[str] | None = None,
    tags: list[str] | None = None,
    seed_queries: list[str] | None = None,
    seed_terms: list[str] | None = None,
) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "type": "research_thread",
        "thread_id": thread_id,
        "title": title or thread_id,
        "status": "active",
        "hypothesis": hypothesis or "",
        "claims": [],
        "open_questions": [],
        "evidence_gaps": [],
        "keywords": list(keywords or []),
        "tags": list(tags or []),
        "seed_queries": list(seed_queries or []),
        "seed_terms": list(seed_terms or []),
        "profile_notes": "",
        "paper_paths": [],
        "experiment_ids": [],
        "watch": {
            "enabled": False,
            "cadence": "weekly",
            "sources_hint": ["arxiv"],
            "last_delta_at": None,
        },
        "created_at": now,
        "updated_at": now,
    }


def _readme_from_thread(data: dict[str, Any], notes: str = "") -> str:
    tid = data.get("thread_id", "")
    title = data.get("title", tid)
    status = data.get("status", "active")
    hyp = (data.get("hypothesis") or "").strip()
    claims = data.get("claims") or []
    questions = data.get("open_questions") or []
    gaps = data.get("evidence_gaps") or []
    claim_lines = "\n".join(
        f"- `{c.get('id', '')}` [{c.get('status', 'open')}] {c.get('text', '')}" for c in claims
    ) or "- (none)"
    q_lines = "\n".join(f"- `{q.get('id', '')}` {q.get('text', '')}" for q in questions) or "- (none)"
    gap_lines = (
        "\n".join(
            f"- claim `{g.get('claim_id', '')}` need={g.get('need', '')}: {g.get('note', '')}"
            for g in gaps
        )
        or "- (none)"
    )
    body_notes = notes.strip() or "_Add freeform research notes here._"
    return (
        f"---\n"
        f"type: research_thread\n"
        f"thread_id: {tid}\n"
        f"title: {title}\n"
        f"status: {status}\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"## Hypothesis\n\n{hyp or '—'}\n\n"
        f"## Claims\n\n{claim_lines}\n\n"
        f"## Open questions\n\n{q_lines}\n\n"
        f"## Evidence gaps\n\n{gap_lines}\n\n"
        f"## Notes\n\n{body_notes}\n"
    )


def save_thread(wiki_root: Path, data: dict[str, Any], *, notes: str | None = None) -> Path:
    tid = str(data.get("thread_id") or "")
    d = thread_dir(wiki_root, tid)
    d.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["type"] = "research_thread"
    data["thread_id"] = d.name
    data["updated_at"] = utc_now_iso()
    if "created_at" not in data or not data["created_at"]:
        data["created_at"] = data["updated_at"]
    (d / "thread.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    existing_notes = ""
    readme = d / "README.md"
    if notes is None and readme.is_file():
        text = readme.read_text(encoding="utf-8")
        if "## Notes" in text:
            existing_notes = text.split("## Notes", 1)[1].strip()
            if existing_notes.startswith("\n"):
                existing_notes = existing_notes.lstrip("\n")
    elif notes is not None:
        existing_notes = notes
    readme.write_text(_readme_from_thread(data, existing_notes), encoding="utf-8")
    events = d / "events.jsonl"
    if not events.is_file():
        events.write_text("", encoding="utf-8")
    return d


def load_thread(wiki_root: Path, thread_id: str) -> dict[str, Any]:
    d = thread_dir(wiki_root, thread_id)
    path = d / "thread.json"
    if not path.is_file():
        raise FileNotFoundError(thread_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid thread.json for {thread_id}")
    data.setdefault("thread_id", d.name)
    return data


def list_threads(wiki_root: Path) -> list[dict[str, Any]]:
    root = threads_dir(wiki_root)
    cards: list[dict[str, Any]] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith(("_", ".")):
            continue
        path = d / "thread.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        cards.append(
            {
                "thread_id": data.get("thread_id") or d.name,
                "title": data.get("title") or d.name,
                "status": data.get("status") or "active",
                "hypothesis": (data.get("hypothesis") or "")[:200],
                "paper_count": len(data.get("paper_paths") or []),
                "exp_count": len(data.get("experiment_ids") or []),
                "claim_count": len(data.get("claims") or []),
                "gap_count": len(data.get("evidence_gaps") or []),
                "updated_at": data.get("updated_at") or "",
                "created_at": data.get("created_at") or "",
            }
        )
    cards.sort(key=lambda c: c.get("updated_at") or "", reverse=True)
    return cards


def append_event(wiki_root: Path, thread_id: str, event: dict[str, Any]) -> None:
    d = thread_dir(wiki_root, thread_id)
    if not (d / "thread.json").is_file():
        raise FileNotFoundError(thread_id)
    payload = dict(event)
    payload.setdefault("ts", utc_now_iso())
    with (d / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_query_iter(
    wiki_root: Path,
    thread_id: str,
    *,
    round: int,
    queries: list[Any] | None = None,
    path_id: str = "",
    raw_hits: int | None = None,
    kept: int | None = None,
    notes: str = "",
    by: str = "agent",
) -> dict[str, Any]:
    """Append a retrieval-trajectory event (kind=query_iter)."""
    event: dict[str, Any] = {
        "kind": "query_iter",
        "round": int(round),
        "queries": list(queries or []),
        "path_id": path_id,
        "by": by,
    }
    if raw_hits is not None:
        event["raw_hits"] = int(raw_hits)
    if kept is not None:
        event["kept"] = int(kept)
    if notes:
        event["notes"] = notes
    append_event(wiki_root, thread_id, event)
    return event


def append_query_trace(
    wiki_root: Path,
    thread_id: str,
    rounds: list[dict[str, Any]],
    *,
    by: str = "agent",
) -> list[dict[str, Any]]:
    """Persist a full retrieval_trace list as query_iter events."""
    written: list[dict[str, Any]] = []
    for row in rounds:
        written.append(
            append_query_iter(
                wiki_root,
                thread_id,
                round=int(row.get("round") if row.get("round") is not None else 0),
                queries=list(row.get("queries") or ([row.get("query")] if row.get("query") else [])),
                path_id=str(row.get("path_id") or row.get("path") or ""),
                raw_hits=row.get("raw_hits"),
                kept=row.get("kept"),
                notes=str(row.get("notes") or ""),
                by=by,
            )
        )
    return written


def record_feedback(
    wiki_root: Path,
    thread_id: str,
    *,
    action: str,
    path: str = "",
    note: str = "",
    by: str = "user",
    bump_seed: bool = True,
) -> dict[str, Any]:
    """Weak feedback loop: accept|skip|read|pin → events + optional seed_terms tweak."""
    action = (action or "").strip().lower()
    if action not in ("accept", "skip", "read", "pin"):
        raise ValueError("action must be accept|skip|read|pin")
    data = load_thread(wiki_root, thread_id)
    path = (path or "").strip().strip("/")
    event = {
        "kind": "feedback",
        "action": action,
        "path": path,
        "note": note,
        "by": by,
    }
    append_event(wiki_root, thread_id, event)

    if action == "accept" and path:
        link_paper(wiki_root, thread_id, path, source="feedback", gate="accepted", by=by)
        data = load_thread(wiki_root, thread_id)

    if bump_seed and path:
        slug = path.split("/")[-1].replace("-", " ")
        tokens = [t for t in re.split(r"\s+", slug) if len(t) > 2][:4]
        seeds = list(data.get("seed_terms") or [])
        if action in ("accept", "pin", "read"):
            for t in tokens:
                if t not in seeds:
                    seeds.append(t)
            data["seed_terms"] = seeds[:40]
            save_thread(wiki_root, data)
        elif action == "skip":
            lower = {t.lower() for t in tokens}
            data["seed_terms"] = [s for s in seeds if s.lower() not in lower] or seeds
            save_thread(wiki_root, data)

    return {"thread_id": thread_id, "event": event, "seed_terms": data.get("seed_terms")}


def list_events(wiki_root: Path, thread_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
    path = thread_dir(wiki_root, thread_id) / "events.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]


def create_thread(
    wiki_root: Path,
    title: str,
    *,
    thread_id: str = "",
    hypothesis: str = "",
    keywords: list[str] | None = None,
    tags: list[str] | None = None,
    seed_queries: list[str] | None = None,
    seed_terms: list[str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    tid = slugify(thread_id or title, max_len=80)
    d = thread_dir(wiki_root, tid)
    if (d / "thread.json").is_file():
        raise FileExistsError(tid)
    terms = list(seed_terms or [])
    if not terms and (keywords or seed_queries):
        bag: list[str] = []
        for x in (keywords or []) + (seed_queries or []):
            bag.extend(_tokenize(x))
        terms = sorted(set(bag))[:40]
    data = default_thread(
        tid,
        title,
        hypothesis=hypothesis,
        keywords=keywords,
        tags=tags,
        seed_queries=seed_queries,
        seed_terms=terms,
    )
    save_thread(wiki_root, data, notes=notes)
    append_event(
        wiki_root,
        tid,
        {"kind": "note", "text": f"thread created: {title}"},
    )
    return data


def update_thread(wiki_root: Path, thread_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    data = load_thread(wiki_root, thread_id)
    allowed = {
        "title",
        "status",
        "hypothesis",
        "claims",
        "open_questions",
        "evidence_gaps",
        "keywords",
        "tags",
        "seed_queries",
        "seed_terms",
        "paper_paths",
        "experiment_ids",
        "watch",
        "profile_notes",
    }
    for k, v in patch.items():
        if k in allowed:
            data[k] = v
    save_thread(wiki_root, data)
    return data


def link_paper(
    wiki_root: Path,
    thread_id: str,
    path: str,
    *,
    source: str = "manual",
    relevance: float | None = None,
    rationale: list[str] | None = None,
    gate: str = "accepted",
    by: str = "user",
) -> dict[str, Any]:
    data = load_thread(wiki_root, thread_id)
    path = path.strip().strip("/")
    papers = list(data.get("paper_paths") or [])
    if gate == "accepted" and path and path not in papers:
        papers.append(path)
        data["paper_paths"] = papers
        save_thread(wiki_root, data)
    append_event(
        wiki_root,
        thread_id,
        {
            "kind": "paper_linked",
            "path": path,
            "source": source,
            "relevance": relevance,
            "rationale": rationale or [],
            "gate": gate,
            "by": by,
        },
    )
    return load_thread(wiki_root, thread_id)


def unlink_paper(wiki_root: Path, thread_id: str, path: str) -> dict[str, Any]:
    data = load_thread(wiki_root, thread_id)
    path = path.strip().strip("/")
    data["paper_paths"] = [p for p in (data.get("paper_paths") or []) if p != path]
    save_thread(wiki_root, data)
    append_event(
        wiki_root,
        thread_id,
        {"kind": "note", "text": f"unlinked paper {path}"},
    )
    return data


def link_exp(
    wiki_root: Path,
    thread_id: str,
    experiment_id: str,
    *,
    source: str = "manual",
    gate: str = "accepted",
    by: str = "user",
) -> dict[str, Any]:
    data = load_thread(wiki_root, thread_id)
    eid = experiment_id.strip()
    exps = list(data.get("experiment_ids") or [])
    if gate == "accepted" and eid and eid not in exps:
        exps.append(eid)
        data["experiment_ids"] = exps
        save_thread(wiki_root, data)
    append_event(
        wiki_root,
        thread_id,
        {
            "kind": "exp_linked",
            "experiment_id": eid,
            "source": source,
            "gate": gate,
            "by": by,
        },
    )
    return load_thread(wiki_root, thread_id)


def reverse_index(wiki_root: Path) -> dict[str, Any]:
    """paper_path -> thread_ids[]; experiment_id -> thread_ids[]."""
    by_paper: dict[str, list[str]] = {}
    by_exp: dict[str, list[str]] = {}
    for card in list_threads(wiki_root):
        tid = card["thread_id"]
        try:
            data = load_thread(wiki_root, tid)
        except FileNotFoundError:
            continue
        for p in data.get("paper_paths") or []:
            by_paper.setdefault(p, []).append(tid)
        for e in data.get("experiment_ids") or []:
            by_exp.setdefault(e, []).append(tid)
    return {"by_paper": by_paper, "by_exp": by_exp}


# --- Relevance (MVP: term bag; no embedding) ---

_STOP = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "be",
    "as",
    "by",
    "from",
    "at",
    "this",
    "that",
    "的",
    "了",
    "与",
    "和",
    "在",
    "是",
    "对",
    "及",
}


def _tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    parts = re.findall(r"[\w\u4e00-\u9fff]+", text, flags=re.UNICODE)
    return [p for p in parts if len(p) > 1 and p not in _STOP]


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def thread_term_bag(data: dict[str, Any]) -> set[str]:
    chunks: list[str] = [
        str(data.get("title") or ""),
        str(data.get("hypothesis") or ""),
    ]
    for c in data.get("claims") or []:
        chunks.append(str(c.get("text") or ""))
    for q in data.get("open_questions") or []:
        chunks.append(str(q.get("text") or ""))
    for g in data.get("evidence_gaps") or []:
        chunks.append(str(g.get("note") or ""))
    for x in data.get("seed_terms") or []:
        chunks.append(str(x))
    for x in data.get("seed_queries") or []:
        chunks.append(str(x))
    for x in data.get("keywords") or []:
        chunks.append(str(x))
    for x in data.get("tags") or []:
        chunks.append(str(x))
    bag: set[str] = set()
    for ch in chunks:
        bag.update(_tokenize(ch))
    return bag


def score_paper_against_thread(
    data: dict[str, Any],
    *,
    title: str = "",
    summary: str = "",
    tags: list[str] | None = None,
    keyword: str = "",
) -> dict[str, Any]:
    """Return R in [0,1], rationale[], claim/gap hints."""
    paper_text = " ".join(
        [title, summary, " ".join(tags or []), keyword]
    )
    paper_bag = set(_tokenize(paper_text))
    thread_bag = thread_term_bag(data)
    term_overlap = _jaccard(paper_bag, thread_bag)

    claim_hits: list[str] = []
    claim_score = 0.0
    claims = data.get("claims") or []
    if claims:
        hits = 0
        for c in claims:
            cbag = set(_tokenize(str(c.get("text") or "")))
            if cbag and _jaccard(paper_bag, cbag) >= 0.15:
                hits += 1
                claim_hits.append(str(c.get("id") or ""))
        claim_score = hits / len(claims)

    gap_hits: list[str] = []
    gap_score = 0.0
    gaps = data.get("evidence_gaps") or []
    if gaps:
        gh = 0
        for g in gaps:
            gbag = set(_tokenize(f"{g.get('need', '')} {g.get('note', '')}"))
            if gbag and _jaccard(paper_bag, gbag) >= 0.12:
                gh += 1
                gap_hits.append(str(g.get("claim_id") or g.get("need") or ""))
        gap_score = gh / len(gaps)

    member_tags: set[str] = set()
    for t in data.get("tags") or []:
        member_tags.update(_tokenize(str(t)))
    paper_tag_bag = set(_tokenize(" ".join(tags or [])))
    member_j = _jaccard(paper_tag_bag, member_tags) if member_tags else 0.0

    kw_hit = 0.0
    tkw = {slugify(str(k), max_len=40) for k in (data.get("keywords") or [])}
    if keyword and slugify(keyword, max_len=40) in tkw:
        kw_hit = 1.0

    r = (
        0.30 * term_overlap
        + 0.30 * claim_score
        + 0.20 * gap_score
        + 0.15 * member_j
        + 0.05 * kw_hit
    )
    rationale: list[str] = []
    if term_overlap >= 0.08:
        shared = sorted(paper_bag & thread_bag)[:8]
        if shared:
            rationale.append("terms:" + ",".join(shared))
    if claim_hits:
        rationale.append("supports:" + ",".join(claim_hits))
    if gap_hits:
        rationale.append("gaps:" + ",".join(gap_hits))
    if kw_hit:
        rationale.append(f"keyword:{keyword}")

    return {
        "R": round(float(r), 4),
        "rationale": rationale,
        "claim_ids": claim_hits,
        "gap_refs": gap_hits,
        "factors": {
            "term_overlap": round(term_overlap, 4),
            "claim_support": round(claim_score, 4),
            "gap_match": round(gap_score, 4),
            "member_jaccard": round(member_j, 4),
            "keyword_hit": kw_hit,
        },
    }


def sync_papers_to_thread(
    wiki_root: Path,
    thread_id: str,
    papers: list[dict[str, Any]],
    *,
    auto_link: bool = False,
    threshold: float = 0.75,
    source: str = "sync-report",
) -> list[dict[str, Any]]:
    """Score papers; append events; optionally accept into paper_paths."""
    data = load_thread(wiki_root, thread_id)
    results: list[dict[str, Any]] = []
    for p in papers:
        path = str(p.get("path") or p.get("wiki_path") or "").strip()
        title = str(p.get("title") or "")
        scored = score_paper_against_thread(
            data,
            title=title,
            summary=str(p.get("summary") or p.get("core_idea") or ""),
            tags=list(p.get("tags") or []),
            keyword=str(p.get("keyword") or ""),
        )
        gate = "suggested"
        if auto_link and scored["R"] >= threshold and path:
            gate = "accepted"
            link_paper(
                wiki_root,
                thread_id,
                path,
                source=source,
                relevance=scored["R"],
                rationale=scored["rationale"],
                gate="accepted",
                by="auto",
            )
        else:
            append_event(
                wiki_root,
                thread_id,
                {
                    "kind": "paper_scored",
                    "path": path,
                    "title": title,
                    "R": scored["R"],
                    "rationale": scored["rationale"],
                    "gate": gate,
                },
            )
        results.append({"path": path, "title": title, **scored, "gate": gate})
    return results
