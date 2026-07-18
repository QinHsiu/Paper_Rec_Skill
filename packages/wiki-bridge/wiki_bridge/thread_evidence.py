"""Claim–Evidence Map — quote/metric evidence bound to thread claims."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import thread_store as ts

STANCES = ("supports", "refutes", "related")
SUPPORT_STATUSES = ("supports", "refutes", "related", "insufficient")
KINDS = ("quote", "metric", "figure", "note")
GATES = ("suggested", "accepted")


def _normalize_confidence(value: Any, default: float = 0.6) -> float:
    try:
        c = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, c))


def _normalize_support_status(value: str, stance: str) -> str:
    v = (value or "").strip().lower()
    if v in SUPPORT_STATUSES:
        return v
    return stance if stance in SUPPORT_STATUSES else "related"


def evidences_path(wiki_root: Path, thread_id: str) -> Path:
    return ts.thread_dir(wiki_root, thread_id) / "evidences.jsonl"


def _next_evidence_id(rows: list[dict[str, Any]]) -> str:
    n = 0
    for r in rows:
        eid = str(r.get("evidence_id") or "")
        m = re.match(r"^E(\d+)$", eid, re.I)
        if m:
            n = max(n, int(m.group(1)))
    return f"E{n + 1}"


def list_evidences(
    wiki_root: Path,
    thread_id: str,
    *,
    claim_id: str = "",
    gate: str = "",
) -> list[dict[str, Any]]:
    path = evidences_path(wiki_root, thread_id)
    if not path.is_file():
        # ensure thread exists
        ts.load_thread(wiki_root, thread_id)
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
    if claim_id:
        rows = [r for r in rows if str(r.get("claim_id")) == claim_id]
    if gate:
        rows = [r for r in rows if str(r.get("gate")) == gate]
    return rows


def _rewrite_evidences(wiki_root: Path, thread_id: str, rows: list[dict[str, Any]]) -> None:
    path = evidences_path(wiki_root, thread_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")


def get_evidence(wiki_root: Path, thread_id: str, evidence_id: str) -> dict[str, Any]:
    for r in list_evidences(wiki_root, thread_id):
        if str(r.get("evidence_id")) == evidence_id:
            return r
    raise FileNotFoundError(evidence_id)


def add_evidence(
    wiki_root: Path,
    thread_id: str,
    *,
    claim_id: str,
    kind: str = "quote",
    paper_path: str = "",
    quote: str = "",
    quote_loc: dict[str, Any] | None = None,
    exp_id: str | None = None,
    metric_key: str | None = None,
    metric_value: Any = None,
    stance: str = "supports",
    support_status: str = "",
    confidence: float | None = None,
    gate: str = "accepted",
    by: str = "user",
    evidence_id: str = "",
    citation_key: str = "",
    page: int | None = None,
    page_from: int | None = None,
    page_to: int | None = None,
    evidence_level: str = "",
) -> dict[str, Any]:
    data = ts.load_thread(wiki_root, thread_id)
    claim_id = (claim_id or "").strip()
    if not claim_id:
        raise ValueError("claim_id required")
    claims = data.get("claims") or []
    if claims and not any(str(c.get("id")) == claim_id for c in claims):
        raise KeyError(f"claim not found: {claim_id}")
    kind = kind if kind in KINDS else "quote"
    stance = stance if stance in STANCES else "supports"
    support_status = _normalize_support_status(support_status, stance)
    conf = _normalize_confidence(0.6 if confidence is None else confidence)
    gate = gate if gate in GATES else "accepted"
    rows = list_evidences(wiki_root, thread_id)
    eid = evidence_id.strip() or _next_evidence_id(rows)
    if any(str(r.get("evidence_id")) == eid for r in rows):
        raise FileExistsError(eid)
    paper_path = (paper_path or "").strip().strip("/")
    loc = dict(quote_loc or {})
    if page is not None and "page" not in loc:
        loc["page"] = page
    if page_from is not None:
        loc["page_from"] = page_from
    if page_to is not None:
        loc["page_to"] = page_to
    rec: dict[str, Any] = {
        "evidence_id": eid,
        "claim_id": claim_id,
        "kind": kind,
        "paper_path": paper_path,
        "quote": (quote or "").strip(),
        "quote_loc": loc,
        "citation_key": (citation_key or "").strip() or None,
        "page": page if page is not None else loc.get("page"),
        "evidence_level": (evidence_level or "").strip() or None,
        "exp_id": exp_id or None,
        "metric_key": metric_key or None,
        "metric_value": metric_value,
        "stance": stance,
        "support_status": support_status,
        "confidence": conf,
        "gate": gate,
        "created_at": ts.utc_now_iso(),
        "by": by,
    }
    rows.append(rec)
    _rewrite_evidences(wiki_root, thread_id, rows)

    # keep membership in sync when accepted
    if gate == "accepted" and paper_path:
        ts.link_paper(
            wiki_root,
            thread_id,
            paper_path,
            source="evidence",
            gate="accepted",
            by=by,
        )
    if gate == "accepted" and exp_id:
        ts.link_exp(
            wiki_root,
            thread_id,
            str(exp_id),
            source="evidence",
            gate="accepted",
            by=by,
        )

    # index on claim
    updated_claims = []
    for c in claims:
        c = dict(c)
        if str(c.get("id")) == claim_id:
            ids = list(c.get("evidence_ids") or [])
            if eid not in ids:
                ids.append(eid)
            c["evidence_ids"] = ids
        updated_claims.append(c)
    if updated_claims:
        data["claims"] = updated_claims
        ts.save_thread(wiki_root, data)

    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "evidence_added",
            "evidence_id": eid,
            "claim_id": claim_id,
            "stance": stance,
            "support_status": support_status,
            "confidence": conf,
            "gate": gate,
            "paper_path": paper_path,
            "by": by,
        },
    )
    return rec


def patch_evidence(
    wiki_root: Path,
    thread_id: str,
    evidence_id: str,
    *,
    support_status: str | None = None,
    confidence: float | None = None,
    stance: str | None = None,
    by: str = "user",
) -> dict[str, Any]:
    rows = list_evidences(wiki_root, thread_id)
    found = None
    for r in rows:
        if str(r.get("evidence_id")) == evidence_id:
            if stance is not None:
                r["stance"] = stance if stance in STANCES else r.get("stance")
            if support_status is not None:
                r["support_status"] = _normalize_support_status(
                    support_status, str(r.get("stance") or "supports")
                )
            elif "support_status" not in r:
                r["support_status"] = _normalize_support_status("", str(r.get("stance") or "supports"))
            if confidence is not None:
                r["confidence"] = _normalize_confidence(confidence)
            found = r
            break
    if not found:
        raise FileNotFoundError(evidence_id)
    _rewrite_evidences(wiki_root, thread_id, rows)
    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "evidence_patch",
            "evidence_id": evidence_id,
            "support_status": found.get("support_status"),
            "confidence": found.get("confidence"),
            "by": by,
        },
    )
    return found


def set_evidence_gate(    wiki_root: Path,
    thread_id: str,
    evidence_id: str,
    gate: str,
    *,
    by: str = "user",
) -> dict[str, Any]:
    if gate not in GATES:
        raise ValueError(f"gate must be one of {GATES}")
    rows = list_evidences(wiki_root, thread_id)
    found = None
    for r in rows:
        if str(r.get("evidence_id")) == evidence_id:
            r["gate"] = gate
            found = r
            break
    if not found:
        raise FileNotFoundError(evidence_id)
    _rewrite_evidences(wiki_root, thread_id, rows)
    if gate == "accepted":
        if found.get("paper_path"):
            ts.link_paper(
                wiki_root,
                thread_id,
                str(found["paper_path"]),
                source="evidence",
                gate="accepted",
                by=by,
            )
        if found.get("exp_id"):
            ts.link_exp(
                wiki_root,
                thread_id,
                str(found["exp_id"]),
                source="evidence",
                gate="accepted",
                by=by,
            )
    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "evidence_gate",
            "evidence_id": evidence_id,
            "gate": gate,
            "by": by,
        },
    )
    return found


def evidences_by_claim(wiki_root: Path, thread_id: str) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for r in list_evidences(wiki_root, thread_id):
        cid = str(r.get("claim_id") or "")
        out.setdefault(cid, []).append(r)
    return out


def hypothesis_evidence_coverage(
    wiki_root: Path,
    thread_id: str,
    *,
    high_threshold: float = 0.8,
) -> dict[str, Any]:
    """UX helper: per-claim high/low confidence counts + advice for the hypothesis."""
    data = ts.load_thread(wiki_root, thread_id)
    evs = list_evidences(wiki_root, thread_id)
    by_claim = evidences_by_claim(wiki_root, thread_id)
    claim_rows = []
    total_high = total_low = 0
    for c in data.get("claims") or []:
        cid = str(c.get("id") or "")
        rows = by_claim.get(cid) or []
        high = low = 0
        for e in rows:
            try:
                conf = float(e.get("confidence") if e.get("confidence") is not None else 0.6)
            except (TypeError, ValueError):
                conf = 0.6
            if conf >= high_threshold:
                high += 1
            else:
                low += 1
        total_high += high
        total_low += low
        advice = ""
        if high == 0 and low == 0:
            advice = "尚无证据，建议挂接论文片段或实验指标。"
        elif high == 0:
            advice = f"仅有 {low} 条低置信证据，建议补充高置信引用或实验。"
        elif low > high:
            advice = f"有 {high} 条高置信、{low} 条低置信证据，可优先核实低置信项。"
        else:
            advice = f"有 {high} 条高置信证据支持，{low} 条低置信可作补充。"
        claim_rows.append(
            {
                "claim_id": cid,
                "text": c.get("text"),
                "status": c.get("status"),
                "high_confidence": high,
                "low_confidence": low,
                "advice": advice,
            }
        )
    hyp_advice = (
        f"此假设关联 {len(claim_rows)} 条主张：高置信证据 {total_high} 条，"
        f"低置信 {total_low} 条。"
    )
    if total_high == 0:
        hyp_advice += " 建议补充实验或高置信文献证据。"
    elif total_low > total_high:
        hyp_advice += " 低置信偏多，建议筛选或补强。"
    return {
        "thread_id": thread_id,
        "hypothesis": data.get("hypothesis"),
        "high_threshold": high_threshold,
        "high_confidence_total": total_high,
        "low_confidence_total": total_low,
        "advice": hyp_advice,
        "claims": claim_rows,
        "evidence_count": len(evs),
    }


def evidence_map_summary(wiki_root: Path, thread_id: str) -> dict[str, Any]:
    """Compact graph for UI: claims ↔ evidences ↔ papers/exps."""
    data = ts.load_thread(wiki_root, thread_id)
    evs = list_evidences(wiki_root, thread_id)
    nodes = [
        {
            "id": f"claim:{c.get('id')}",
            "type": "claim",
            "label": f"{c.get('id')} {(c.get('text') or '')[:40]}",
            "status": c.get("status"),
        }
        for c in (data.get("claims") or [])
    ]
    edges = []
    for e in evs:
        eid = f"evidence:{e.get('evidence_id')}"
        nodes.append(
            {
                "id": eid,
                "type": "evidence",
                "label": e.get("evidence_id"),
                "stance": e.get("stance"),
                "gate": e.get("gate"),
                "kind": e.get("kind"),
            }
        )
        edges.append(
            {
                "source": f"claim:{e.get('claim_id')}",
                "target": eid,
                "kind": "has_evidence",
            }
        )
        if e.get("paper_path"):
            pid = f"paper:{e['paper_path']}"
            if not any(n["id"] == pid for n in nodes):
                nodes.append({"id": pid, "type": "paper", "label": e["paper_path"], "path": e["paper_path"]})
            edges.append({"source": eid, "target": pid, "kind": "cites"})
        if e.get("exp_id"):
            xid = f"exp:{e['exp_id']}"
            if not any(n["id"] == xid for n in nodes):
                nodes.append({"id": xid, "type": "experiment", "label": e["exp_id"], "exp_id": e["exp_id"]})
            edges.append({"source": eid, "target": xid, "kind": "measures"})
    return {"thread_id": thread_id, "nodes": nodes, "edges": edges, "evidence_count": len(evs)}
