"""Feedback → rewrite → re-retrieve loop for grounded answers."""
from __future__ import annotations

import re
from typing import Any

from .evidence_ground import abstract_supports_claim, extract_e_ids, ground_answer
from .evidence_score import relevance_score, tokenize

_CLAIMISH = re.compile(
    r"(?i)\b(show[s]?|demonstrat\w*|find\w*|suggest\w*|indicate\w*|prove\w*|"
    r"achieve\w*|outperform\w*|表明|显示|证明|优于)\b"
)


def _ev_text(e: dict[str, Any]) -> str:
    return str(e.get("quote") or e.get("summary") or e.get("abstract") or e.get("text") or "")


def critique_answer(
    question: str,
    answer: str,
    evidences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Heuristic reviewer: unsupported claim sentences + missing evidence coverage."""
    feedbacks: list[dict[str, Any]] = []
    idx = {f"E{i}": e for i, e in enumerate(evidences or [], start=1) if isinstance(e, dict)}
    for i, e in enumerate(evidences or [], start=1):
        if isinstance(e, dict):
            for alt in (e.get("eid"), e.get("id")):
                if alt:
                    idx[str(alt).upper()] = e

    cited = set(extract_e_ids(answer or ""))
    for sent in re.split(r"(?<=[.!?。！？])\s+", answer or ""):
        sent = sent.strip()
        if len(sent) < 30 or not _CLAIMISH.search(sent):
            continue
        eids = extract_e_ids(sent)
        if not eids:
            feedbacks.append(
                {
                    "feedback": f"Claim lacks citation: {sent[:160]}",
                    "question": f"{question} evidence for: {sent[:80]}",
                    "severity": "high",
                    "sentence": sent[:300],
                }
            )
            continue
        supported = False
        for eid in eids:
            ev = idx.get(eid.upper()) or idx.get(eid)
            if not ev:
                feedbacks.append(
                    {
                        "feedback": f"Unknown citation {eid} in: {sent[:120]}",
                        "question": f"{question} {eid}",
                        "severity": "high",
                        "sentence": sent[:300],
                    }
                )
                continue
            chk = abstract_supports_claim(sent, _ev_text(ev), min_overlap=2)
            if chk.get("supported"):
                supported = True
            else:
                feedbacks.append(
                    {
                        "feedback": f"{eid} does not support: {sent[:140]}",
                        "question": f"{question} {' '.join(tokenize(sent)[:8])}",
                        "severity": "medium",
                        "sentence": sent[:300],
                    }
                )
        if eids and not supported:
            # already added per-eid; ensure at least one retrieve cue
            pass

    # coverage: question terms poorly covered by cited evidence
    qtoks = set(tokenize(question))
    cited_text = " ".join(_ev_text(idx[c]) for c in cited if c in idx)
    if qtoks and cited:
        cov = len(qtoks & set(tokenize(cited_text))) / max(1, len(qtoks))
        if cov < 0.35:
            missing = sorted(qtoks - set(tokenize(cited_text)))[:6]
            feedbacks.append(
                {
                    "feedback": f"Answer under-covers question facets: {', '.join(missing)}",
                    "question": f"{question} {' '.join(missing)}",
                    "severity": "medium",
                    "sentence": "",
                }
            )
    return feedbacks


def followup_queries(question: str, feedbacks: list[dict[str, Any]], *, max_n: int = 5) -> list[str]:
    qs: list[str] = []
    for fb in feedbacks:
        q = str(fb.get("question") or "").strip()
        if q and q not in qs:
            qs.append(q)
        if len(qs) >= max_n:
            break
    if not qs and question:
        qs.append(f"{question} additional supporting evidence")
    return qs


def edit_with_feedback(
    answer: str,
    feedbacks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Rewrite: mark unsupported sentences; keep cited supported content."""
    drop_frags = [str(fb.get("sentence") or "") for fb in feedbacks if fb.get("sentence")]
    lines = []
    removed = 0
    for sent in re.split(r"(?<=[.!?。！？])\s+", answer or ""):
        sent = sent.strip()
        if not sent:
            continue
        hit = any(frag and frag[:60] in sent for frag in drop_frags)
        if hit and _CLAIMISH.search(sent):
            # soften rather than delete entirely
            if extract_e_ids(sent):
                lines.append(sent + " [CITATION WEAK — verify]")
            else:
                lines.append(sent + " [CITATION NEEDED]")
            removed += 1
        else:
            lines.append(sent)
    edited = " ".join(lines).strip()
    return {"edited_answer": edited, "marked_n": removed, "original": answer}


def select_retrievable(
    queries: list[str],
    candidate_docs: list[dict[str, Any]],
    *,
    top_k: int = 5,
    cutoff: float = 2.5,
) -> list[dict[str, Any]]:
    """Rank extra docs for re-retrieve given follow-up queries."""
    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in candidate_docs or []:
        if not isinstance(doc, dict):
            continue
        text = " ".join(str(doc.get(k) or "") for k in ("title", "abstract", "summary", "quote", "text"))
        best = max((relevance_score(q, text) for q in queries), default=0.0)
        if best >= cutoff:
            row = dict(doc)
            row["reretrieve_score"] = best
            scored.append((best, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_k]]


def feedback_edit_loop(
    question: str,
    answer: str,
    evidences: list[dict[str, Any]],
    *,
    candidate_docs: list[dict[str, Any]] | None = None,
    lang: str = "en",
) -> dict[str, Any]:
    """One outer cycle: critique → edit → follow-up queries → optional new evidence."""
    feedbacks = critique_answer(question, answer, evidences)
    edited = edit_with_feedback(answer, feedbacks)
    queries = followup_queries(question, feedbacks)
    new_docs = select_retrievable(queries, candidate_docs or [])
    # merge new docs as extra evidences for grounding preview
    merged_ev = list(evidences or [])
    for i, d in enumerate(new_docs, start=len(merged_ev) + 1):
        merged_ev.append(
            {
                "eid": f"E{i}",
                "quote": d.get("abstract") or d.get("summary") or d.get("text") or "",
                "paper_path": d.get("paper_path") or d.get("title"),
                "relevance_score": d.get("reretrieve_score"),
                "support_status": "supports",
            }
        )
    grounded = ground_answer(edited["edited_answer"], merged_ev, lang=lang) if merged_ev else None
    return {
        "feedbacks": feedbacks,
        "feedback_n": len(feedbacks),
        "needs_retrieve": len(queries) > 0 and len(feedbacks) > 0,
        "followup_queries": queries,
        "edited_answer": edited["edited_answer"],
        "marked_n": edited["marked_n"],
        "new_evidence_n": len(new_docs),
        "new_evidences": new_docs,
        "grounded_preview": grounded,
        "ok": len(feedbacks) == 0,
    }
