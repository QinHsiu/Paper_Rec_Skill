"""Thread store for wiki-api — delegates to wiki_bridge.thread_store."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from app.services import content_root

_BRIDGE = content_root.workspace_root() / "packages" / "wiki-bridge"
if _BRIDGE.is_dir() and str(_BRIDGE) not in sys.path:
    sys.path.insert(0, str(_BRIDGE))

from wiki_bridge import thread_store as _ts  # noqa: E402


def wiki_root() -> Path:
    return content_root.workspace_root()


def list_threads() -> list[dict[str, Any]]:
    return _ts.list_threads(wiki_root())


def get_thread(thread_id: str) -> dict[str, Any]:
    from wiki_bridge import thread_evidence as _ev

    data = _ts.load_thread(wiki_root(), thread_id)
    events = _ts.list_events(wiki_root(), thread_id, limit=100)
    readme = _ts.thread_dir(wiki_root(), thread_id) / "README.md"
    notes = ""
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        if "## Notes" in text:
            notes = text.split("## Notes", 1)[1].strip()
    evidences = _ev.list_evidences(wiki_root(), thread_id)
    emap = _ev.evidence_map_summary(wiki_root(), thread_id)
    return {
        **data,
        "events": events,
        "notes": notes,
        "evidences": evidences,
        "evidence_map": emap,
    }


def create_thread(payload: dict[str, Any]) -> dict[str, Any]:
    return _ts.create_thread(
        wiki_root(),
        str(payload.get("title") or ""),
        thread_id=str(payload.get("thread_id") or payload.get("id") or ""),
        hypothesis=str(payload.get("hypothesis") or ""),
        keywords=list(payload.get("keywords") or []),
        tags=list(payload.get("tags") or []),
        seed_queries=list(payload.get("seed_queries") or []),
        seed_terms=list(payload.get("seed_terms") or []),
        notes=str(payload.get("notes") or ""),
    )


def patch_thread(thread_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _ts.update_thread(wiki_root(), thread_id, payload)


def link_paper(thread_id: str, path: str, source: str = "api") -> dict[str, Any]:
    return _ts.link_paper(wiki_root(), thread_id, path, source=source, gate="accepted", by="user")


def unlink_paper(thread_id: str, path: str) -> dict[str, Any]:
    return _ts.unlink_paper(wiki_root(), thread_id, path)


def link_exp(thread_id: str, experiment_id: str, source: str = "api") -> dict[str, Any]:
    return _ts.link_exp(
        wiki_root(), thread_id, experiment_id, source=source, gate="accepted", by="user"
    )


def timeline(thread_id: str, limit: int = 100) -> list[dict[str, Any]]:
    return _ts.list_events(wiki_root(), thread_id, limit=limit)


def reverse_index() -> dict[str, Any]:
    return _ts.reverse_index(wiki_root())


def threads_for_paper(path: str) -> list[str]:
    return reverse_index().get("by_paper", {}).get(path.strip("/"), [])


def threads_for_exp(exp_id: str) -> list[str]:
    return reverse_index().get("by_exp", {}).get(exp_id, [])


def run_delta(thread_id: str, mode: str = "auto", threshold: float = 0.45, persist: bool = True):
    from wiki_bridge.thread_delta import run_delta as _run

    return _run(wiki_root(), thread_id, mode=mode, threshold=threshold, persist=persist)


def propose_claims(thread_id: str):
    from wiki_bridge.thread_delta import propose_claim_updates

    return propose_claim_updates(wiki_root(), thread_id, apply=False)


def accept_claim(thread_id: str, claim_id: str, status: str, reason: str = ""):
    from wiki_bridge.thread_delta import accept_claim_update

    return accept_claim_update(wiki_root(), thread_id, claim_id, status, by="user", reason=reason)


def score_papers(thread_id: str, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = _ts.load_thread(wiki_root(), thread_id)
    out = []
    for p in papers:
        scored = _ts.score_paper_against_thread(
            data,
            title=str(p.get("title") or ""),
            summary=str(p.get("summary") or p.get("core_idea") or ""),
            tags=list(p.get("tags") or []),
            keyword=str(p.get("keyword") or ""),
        )
        out.append({"path": p.get("path"), "title": p.get("title"), **scored})
    return out


def search_context(thread_id: str) -> dict[str, Any]:
    """Compact context for Thread-conditioned retrieval (MCP / Skill)."""
    data = get_thread(thread_id)
    return {
        "thread_id": data.get("thread_id"),
        "title": data.get("title"),
        "hypothesis": data.get("hypothesis"),
        "claims": data.get("claims") or [],
        "open_questions": data.get("open_questions") or [],
        "evidence_gaps": data.get("evidence_gaps") or [],
        "seed_queries": data.get("seed_queries") or [],
        "seed_terms": data.get("seed_terms") or [],
        "keywords": data.get("keywords") or [],
        "paper_paths": (data.get("paper_paths") or [])[:20],
        "experiment_ids": data.get("experiment_ids") or [],
        "evidences": (data.get("evidences") or [])[:30],
    }


def list_evidences(thread_id: str, claim_id: str = "", gate: str = ""):
    from wiki_bridge import thread_evidence as _ev

    return _ev.list_evidences(wiki_root(), thread_id, claim_id=claim_id, gate=gate)


def add_evidence(thread_id: str, payload: dict[str, Any]):
    from wiki_bridge import thread_evidence as _ev

    return _ev.add_evidence(
        wiki_root(),
        thread_id,
        claim_id=str(payload.get("claim_id") or ""),
        kind=str(payload.get("kind") or "quote"),
        paper_path=str(payload.get("paper_path") or ""),
        quote=str(payload.get("quote") or ""),
        quote_loc=payload.get("quote_loc") if isinstance(payload.get("quote_loc"), dict) else {},
        exp_id=payload.get("exp_id"),
        metric_key=payload.get("metric_key"),
        metric_value=payload.get("metric_value"),
        stance=str(payload.get("stance") or "supports"),
        support_status=str(payload.get("support_status") or ""),
        confidence=payload.get("confidence"),
        gate=str(payload.get("gate") or "accepted"),
        by=str(payload.get("by") or "user"),
    )


def patch_evidence(thread_id: str, evidence_id: str, payload: dict[str, Any]):
    from wiki_bridge import thread_evidence as _ev

    return _ev.patch_evidence(
        wiki_root(),
        thread_id,
        evidence_id,
        support_status=payload.get("support_status"),
        confidence=payload.get("confidence"),
        stance=payload.get("stance"),
        by="user",
    )


def set_evidence_gate(thread_id: str, evidence_id: str, gate: str):
    from wiki_bridge import thread_evidence as _ev

    return _ev.set_evidence_gate(wiki_root(), thread_id, evidence_id, gate, by="user")


def recommend_evidence(thread_id: str, text: str, limit: int = 8) -> dict[str, Any]:
    """Rank thread evidences/claims for a writing selection (P2 writing assist)."""
    from wiki_bridge import thread_evidence as _ev

    text_l = (text or "").lower()
    tokens = {t for t in re.findall(r"[a-zA-Z\u4e00-\u9fff]{2,}", text_l)}
    data = _ts.load_thread(wiki_root(), thread_id)
    evs = _ev.list_evidences(wiki_root(), thread_id)
    scored = []
    for e in evs:
        blob = " ".join(
            [
                str(e.get("quote") or ""),
                str(e.get("claim_id") or ""),
                str(e.get("paper_path") or ""),
                str(e.get("stance") or ""),
            ]
        ).lower()
        hits = sum(1 for t in tokens if t in blob)
        score = hits / max(len(tokens), 1)
        if e.get("gate") == "accepted":
            score += 0.15
        conf = float(e.get("confidence") or 0.5)
        score += 0.1 * conf
        scored.append({**e, "recommend_score": round(score, 4)})
    scored.sort(key=lambda x: x["recommend_score"], reverse=True)
    claims = []
    for c in data.get("claims") or []:
        blob = str(c.get("text") or "").lower()
        hits = sum(1 for t in tokens if t in blob)
        claims.append(
            {
                "id": c.get("id"),
                "text": c.get("text"),
                "status": c.get("status"),
                "recommend_score": round(hits / max(len(tokens), 1), 4),
            }
        )
    claims.sort(key=lambda x: x["recommend_score"], reverse=True)
    return {
        "thread_id": thread_id,
        "evidences": scored[:limit],
        "claims": claims[:limit],
    }


def ingest_paper_file(paper_path: str, file_path: Path, thread_id: str = "", apply_suggest: bool = True):
    from wiki_bridge.pdf_ingest import apply_claim_suggestions, ingest_pdf

    out = ingest_pdf(wiki_root(), file_path, paper_path)
    suggest = None
    if apply_suggest and thread_id:
        suggest = apply_claim_suggestions(
            wiki_root(), thread_id, paper_path, max_claims=3, also_evidence=True
        )
    elif apply_suggest:
        from wiki_bridge.pdf_ingest import suggest_claims_from_fulltext

        suggest = {"candidates": suggest_claims_from_fulltext(wiki_root(), paper_path, max_claims=3)}
    return {"ingest": out, "suggest": suggest}


def evidence_map(thread_id: str):
    from wiki_bridge import thread_evidence as _ev

    return _ev.evidence_map_summary(wiki_root(), thread_id)


def append_query_trace(thread_id: str, rounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _ts.append_query_trace(wiki_root(), thread_id, rounds, by="api")


def thread_graph(thread_id: str) -> dict[str, Any]:
    from wiki_bridge.thread_graph import build_thread_graph, group_timeline

    g = build_thread_graph(wiki_root(), thread_id)
    events = _ts.list_events(wiki_root(), thread_id, limit=200)
    g["timeline"] = group_timeline(events)
    return g


def related_work(thread_id: str) -> dict[str, Any]:
    from wiki_bridge.related_work import build_related_work_outline

    return build_related_work_outline(wiki_root(), thread_id)


def bibtex_for_paths(paths: list[str]) -> dict[str, Any]:
    from wiki_bridge.bibtex_export import export_bibtex

    return export_bibtex(wiki_root(), paths)


def pdf_ingest(pdf: str, paper_path: str, title: str = "") -> dict[str, Any]:
    from wiki_bridge.pdf_ingest import ingest_pdf

    return ingest_pdf(wiki_root(), Path(pdf), paper_path, title=title)


def claim_suggest(paper_path: str, thread_id: str = "", apply: bool = False, max_claims: int = 5):
    from wiki_bridge.pdf_ingest import apply_claim_suggestions, suggest_claims_from_fulltext

    if apply and thread_id:
        return apply_claim_suggestions(wiki_root(), thread_id, paper_path, max_claims=max_claims)
    return {"candidates": suggest_claims_from_fulltext(wiki_root(), paper_path, max_claims=max_claims)}
