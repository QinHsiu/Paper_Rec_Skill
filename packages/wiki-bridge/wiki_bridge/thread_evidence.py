"""Claim–Evidence Map — quote/metric evidence bound to thread claims."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import thread_store as ts

STANCES = ("supports", "refutes", "related")
KINDS = ("quote", "metric", "figure", "note")
GATES = ("suggested", "accepted")


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
    gate: str = "accepted",
    by: str = "user",
    evidence_id: str = "",
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
    gate = gate if gate in GATES else "accepted"
    rows = list_evidences(wiki_root, thread_id)
    eid = evidence_id.strip() or _next_evidence_id(rows)
    if any(str(r.get("evidence_id")) == eid for r in rows):
        raise FileExistsError(eid)
    paper_path = (paper_path or "").strip().strip("/")
    rec: dict[str, Any] = {
        "evidence_id": eid,
        "claim_id": claim_id,
        "kind": kind,
        "paper_path": paper_path,
        "quote": (quote or "").strip(),
        "quote_loc": quote_loc or {},
        "exp_id": exp_id or None,
        "metric_key": metric_key or None,
        "metric_value": metric_value,
        "stance": stance,
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
            "gate": gate,
            "paper_path": paper_path,
            "by": by,
        },
    )
    return rec


def set_evidence_gate(
    wiki_root: Path,
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
