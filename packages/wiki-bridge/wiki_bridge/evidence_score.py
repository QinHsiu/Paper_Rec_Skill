"""Map-reduce evidence: score chunks 0–10 vs question, drop below cutoff."""
from __future__ import annotations

import math
import re
from typing import Any

_TOKEN = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")
_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "been", "will", "can", "may", "not", "but", "also", "into",
}


def tokenize(text: str) -> list[str]:
    return [
        t.lower()
        for t in _TOKEN.findall(text or "")
        if len(t) > 1 and t.lower() not in _STOP
    ]


def chunk_text(text: str, *, max_chars: int = 1200, overlap: int = 100) -> list[dict[str, Any]]:
    """Split on page markers / paragraphs into scored-ready chunks."""
    text = text or ""
    parts: list[tuple[int | None, str]] = []
    if "<!-- page:" in text:
        pages = re.split(r"<!--\s*page:\s*(\d+)\s*-->", text)
        # pages[0]=preamble, then (num, body, num, body, ...)
        i = 1
        while i + 1 < len(pages):
            try:
                pno = int(pages[i])
            except ValueError:
                pno = None
            parts.append((pno, pages[i + 1]))
            i += 2
        if pages and pages[0].strip():
            parts.insert(0, (None, pages[0]))
    else:
        parts = [(None, text)]

    chunks: list[dict[str, Any]] = []
    idx = 0
    for page, body in parts:
        paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        buf = ""
        for para in paras:
            if len(buf) + len(para) + 1 <= max_chars:
                buf = f"{buf}\n\n{para}".strip() if buf else para
            else:
                if buf:
                    idx += 1
                    chunks.append({"chunk_id": f"C{idx}", "text": buf, "page": page})
                if len(para) <= max_chars:
                    buf = para
                else:
                    start = 0
                    while start < len(para):
                        end = min(len(para), start + max_chars)
                        idx += 1
                        chunks.append({"chunk_id": f"C{idx}", "text": para[start:end], "page": page})
                        start = max(end - overlap, end) if end < len(para) else end
                    buf = ""
        if buf:
            idx += 1
            chunks.append({"chunk_id": f"C{idx}", "text": buf, "page": page})
    return chunks


def relevance_score(question: str, chunk: str) -> float:
    """Heuristic 0–10 relevance (no LLM). Overlap + coverage of query terms."""
    q = tokenize(question)
    c = tokenize(chunk)
    if not q or not c:
        return 0.0
    qset, cset = set(q), set(c)
    hit = qset & cset
    if not hit:
        return 0.0
    coverage = len(hit) / max(1, len(qset))
    density = len(hit) / max(1, math.sqrt(len(cset)))
    # map to 0–10
    score = 10.0 * min(1.0, 0.65 * coverage + 0.35 * min(1.0, density * 2))
    return round(score, 2)


def score_chunks(
    question: str,
    chunks: list[dict[str, Any]],
    *,
    cutoff: float = 3.0,
) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    for ch in chunks or []:
        if not isinstance(ch, dict):
            continue
        text = str(ch.get("text") or ch.get("quote") or ch.get("abstract") or "")
        s = relevance_score(question, text)
        row = dict(ch)
        row["relevance_score"] = s
        row["summary"] = text[:240].replace("\n", " ")
        scored.append(row)
        if s >= cutoff:
            kept.append(row)
    scored.sort(key=lambda r: float(r.get("relevance_score") or 0), reverse=True)
    kept.sort(key=lambda r: float(r.get("relevance_score") or 0), reverse=True)
    return {
        "question": question,
        "cutoff": cutoff,
        "input_n": len(chunks or []),
        "kept_n": len(kept),
        "dropped_n": max(0, len(scored) - len(kept)),
        "chunks": scored,
        "kept": kept,
    }


def gather_evidence(
    question: str,
    documents: list[dict[str, Any]],
    *,
    cutoff: float = 3.0,
    max_chars: int = 1200,
) -> dict[str, Any]:
    """Chunk each document, score, return evidence list ready for answer-ground."""
    all_chunks: list[dict[str, Any]] = []
    for i, doc in enumerate(documents or [], start=1):
        if not isinstance(doc, dict):
            continue
        text = str(
            doc.get("fulltext")
            or doc.get("text")
            or doc.get("abstract")
            or doc.get("summary")
            or doc.get("quote")
            or ""
        )
        if not text:
            continue
        for ch in chunk_text(text, max_chars=max_chars):
            ch["paper_path"] = doc.get("paper_path") or doc.get("title") or f"doc{i}"
            ch["source_doc"] = i
            all_chunks.append(ch)
    scored = score_chunks(question, all_chunks, cutoff=cutoff)
    evidences = []
    for j, ch in enumerate(scored["kept"], start=1):
        evidences.append(
            {
                "eid": f"E{j}",
                "id": f"E{j}",
                "paper_path": ch.get("paper_path"),
                "page": ch.get("page"),
                "quote": ch.get("text"),
                "summary": ch.get("summary"),
                "relevance_score": ch.get("relevance_score"),
                "support_status": "supports",
                "confidence": min(1.0, float(ch.get("relevance_score") or 0) / 10.0),
            }
        )
    return {
        **{k: scored[k] for k in ("question", "cutoff", "input_n", "kept_n", "dropped_n")},
        "chunk_n": len(all_chunks),
        "evidences": evidences,
        "cannot_answer": len(evidences) == 0,
    }
