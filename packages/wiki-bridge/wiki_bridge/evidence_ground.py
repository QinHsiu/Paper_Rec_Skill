"""Ground answers to opaque evidence ids (paper-qa inspired).

Answers may only cite ``(E12)`` / ``[E12]`` keys present in an evidence list;
expand to human References; emit cannot-answer when nothing usable.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CANNOT_ANSWER_PHRASE = "I cannot answer"
CANNOT_ANSWER_PHRASE_ZH = "依据不足，无法回答"

_E_ID = re.compile(r"(?:\(\s*E(\d+)\s*\)|\[\s*E(\d+)\s*\])", re.I)


def _eid(n: int | str) -> str:
    return f"E{int(n)}"


def index_evidences(evidences: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map E1..En (1-based list order) and optional explicit ``id`` / ``eid``."""
    out: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(evidences or [], start=1):
        if not isinstance(row, dict):
            continue
        key = _eid(i)
        out[key] = dict(row)
        out[key]["_eid"] = key
        for alt in (row.get("id"), row.get("eid"), row.get("evidence_id")):
            if alt:
                out[str(alt).strip().upper().replace(" ", "")] = out[key]
    return out


def extract_e_ids(text: str) -> list[str]:
    found: list[str] = []
    for m in _E_ID.finditer(text or ""):
        n = m.group(1) or m.group(2)
        found.append(_eid(n))
    return list(dict.fromkeys(found))


def format_reference(row: dict[str, Any]) -> str:
    paper = str(row.get("paper_path") or row.get("title") or "source").strip()
    page = row.get("page") or (row.get("quote_loc") or {}).get("page") if isinstance(row.get("quote_loc"), dict) else None
    section = row.get("source_section") or row.get("section") or ""
    quote = str(row.get("quote") or row.get("text") or "")[:160]
    loc = f"p.{page}" if page not in (None, "") else (section or "loc?")
    return f"{paper} ({loc}): {quote}"


def abstract_supports_claim(claim: str, abstract: str, *, min_overlap: int = 3) -> dict[str, Any]:
    """AutoSurvey-style Yes/No faithfulness heuristic (no LLM): token overlap gate.

    Returns ``supported`` True/False plus overlap terms. Use before inventing cites.
    """
    def toks(s: str) -> set[str]:
        return {
            t.lower()
            for t in re.findall(r"[A-Za-z0-9\u4e00-\u9fff]{3,}", s or "")
            if t.lower() not in {"the", "and", "for", "with", "that", "this", "from", "are", "was"}
        }

    ct, at = toks(claim), toks(abstract)
    if not ct or not at:
        return {"supported": False, "label": "No", "overlap": [], "reason": "empty"}
    overlap = sorted(ct & at)
    ok = len(overlap) >= min_overlap
    return {
        "supported": ok,
        "label": "Yes" if ok else "No",
        "overlap": overlap[:12],
        "overlap_n": len(overlap),
    }


def check_claims_against_abstracts(
    claims: list[dict[str, Any]],
    papers: list[dict[str, Any]],
) -> dict[str, Any]:
    """For each claim with citations, Yes/No support vs cited paper abstracts."""
    by_key: dict[str, dict[str, Any]] = {}
    for i, p in enumerate(papers or [], start=1):
        if not isinstance(p, dict):
            continue
        keys = [
            str(p.get("citation_key") or p.get("key") or ""),
            f"E{i}",
            str(p.get("paper_path") or ""),
        ]
        for k in keys:
            if k:
                by_key[k] = p
    rows = []
    yes = no = 0
    for c in claims or []:
        if not isinstance(c, dict):
            continue
        text = str(c.get("text") or c.get("claim") or "")
        cites = list(c.get("citations") or [])
        supports = []
        for ck in cites:
            paper = by_key.get(str(ck)) or by_key.get(str(ck).upper())
            if not paper:
                supports.append({"key": ck, "label": "No", "reason": "unknown_key"})
                no += 1
                continue
            abs_ = str(paper.get("abstract") or paper.get("summary") or paper.get("quote") or "")
            r = abstract_supports_claim(text, abs_)
            supports.append({"key": ck, **r})
            if r["supported"]:
                yes += 1
            else:
                no += 1
        rows.append({"claim_id": c.get("claim_id"), "text": text[:240], "checks": supports})
    return {"yes": yes, "no": no, "claims": rows}


def ground_answer(
    raw_answer: str,
    evidences: list[dict[str, Any]],
    *,
    lang: str = "en",
    min_positive: int = 1,
    relevance_cutoff: float = 0.0,
) -> dict[str, Any]:
    """Expand E-ids; strip unknown cites; cannot-answer if empty evidence or none used.

    When evidences carry ``relevance_score``, drop those below ``relevance_cutoff``
    (default 0 keeps all; gather_evidence typically uses 3.0).
    """
    if relevance_cutoff > 0:
        evidences = [
            e
            for e in (evidences or [])
            if isinstance(e, dict)
            and float(e.get("relevance_score") if e.get("relevance_score") is not None else 10) >= relevance_cutoff
        ]
    idx = index_evidences(evidences)
    usable = [
        r
        for r in evidences
        if isinstance(r, dict)
        and str(r.get("support_status") or "") != "insufficient"
        and float(r.get("relevance_score") if r.get("relevance_score") is not None else r.get("confidence") or 1) > 0
    ]
    if len(usable) < min_positive or not (raw_answer or "").strip():
        phrase = CANNOT_ANSWER_PHRASE_ZH if lang.startswith("zh") else CANNOT_ANSWER_PHRASE
        return {
            "has_successful_answer": False,
            "cannot_answer": True,
            "answer": phrase,
            "used_evidences": [],
            "unknown_citations": [],
            "references": [],
            "grounded_answer": phrase,
        }

    cited = extract_e_ids(raw_answer)
    used: list[str] = []
    unknown: list[str] = []
    for eid in cited:
        if eid in idx:
            used.append(eid)
        else:
            unknown.append(eid)

    grounded = raw_answer
    for eid in cited:
        row = idx.get(eid)
        if not row:
            grounded = re.sub(rf"\(\s*{eid}\s*\)|\[\s*{eid}\s*\]", "", grounded, flags=re.I)
            continue
        page = row.get("page") or (
            (row.get("quote_loc") or {}).get("page") if isinstance(row.get("quote_loc"), dict) else None
        )
        paper = str(row.get("paper_path") or "paper").split("/")[-1]
        repl = f"({paper}" + (f" p.{page}" if page not in (None, "") else "") + ")"
        grounded = re.sub(rf"\(\s*{eid}\s*\)|\[\s*{eid}\s*\]", repl, grounded, flags=re.I)

    if not used and cited:
        # all cites hallucinated
        phrase = CANNOT_ANSWER_PHRASE_ZH if lang.startswith("zh") else CANNOT_ANSWER_PHRASE
        return {
            "has_successful_answer": False,
            "cannot_answer": True,
            "answer": phrase,
            "used_evidences": [],
            "unknown_citations": unknown,
            "references": [],
            "grounded_answer": phrase,
            "raw_answer": raw_answer,
        }

    refs = [format_reference(idx[e]) for e in used if e in idx]
    if used:
        grounded = grounded.rstrip() + "\n\nReferences:\n" + "\n".join(f"- ({e}) {r}" for e, r in zip(used, refs))

    return {
        "has_successful_answer": bool(used) or not cited,
        "cannot_answer": False,
        "answer": grounded,
        "grounded_answer": grounded,
        "used_evidences": used,
        "unknown_citations": unknown,
        "references": refs,
        "raw_answer": raw_answer,
    }


def ground_from_files(
    answer_path: Path,
    evidences_path: Path,
    *,
    lang: str = "en",
    relevance_cutoff: float = 0.0,
) -> dict[str, Any]:
    raw = answer_path.read_text(encoding="utf-8")
    data = json.loads(evidences_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        evs = list(data.get("evidences") or data.get("contexts") or [])
    else:
        evs = list(data)
    return ground_answer(raw, evs, lang=lang, relevance_cutoff=relevance_cutoff)
