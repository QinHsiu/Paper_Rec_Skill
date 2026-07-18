"""Build interactive Claim–Evidence cognitive graph for a thread."""
from __future__ import annotations

import math
from typing import Any

from . import thread_evidence as te
from . import thread_store as ts


_COLORS = {
    "thread": "#0f766e",
    "claim": "#c45c26",
    "evidence": "#2d6a4f",
    "paper": "#1a6b7c",
    "experiment": "#6b4c9a",
}


def build_thread_graph(wiki_root, thread_id: str) -> dict[str, Any]:
    data = ts.load_thread(wiki_root, thread_id)
    evidences = te.list_evidences(wiki_root, thread_id)
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    tid = data.get("thread_id") or thread_id
    nodes[f"thread:{tid}"] = {
        "id": f"thread:{tid}",
        "type": "thread",
        "label": data.get("title") or tid,
        "detail": (data.get("hypothesis") or "")[:120],
        "color": _COLORS["thread"],
    }

    for c in data.get("claims") or []:
        cid = str(c.get("id") or "")
        if not cid:
            continue
        nid = f"claim:{cid}"
        nodes[nid] = {
            "id": nid,
            "type": "claim",
            "label": cid,
            "detail": str(c.get("text") or "")[:160],
            "status": c.get("status") or "open",
            "color": _COLORS["claim"],
        }
        edges.append({"source": f"thread:{tid}", "target": nid, "kind": "has_claim"})

    for e in evidences:
        eid = str(e.get("evidence_id") or "")
        if not eid:
            continue
        nid = f"evidence:{eid}"
        nodes[nid] = {
            "id": nid,
            "type": "evidence",
            "label": eid,
            "detail": str(e.get("quote") or e.get("metric_key") or "")[:160],
            "stance": e.get("stance"),
            "gate": e.get("gate"),
            "color": _COLORS["evidence"],
        }
        cid = str(e.get("claim_id") or "")
        if cid:
            edges.append(
                {
                    "source": f"claim:{cid}",
                    "target": nid,
                    "kind": "evidence",
                    "stance": e.get("stance"),
                }
            )
        pp = str(e.get("paper_path") or "").strip("/")
        if pp:
            pid = f"paper:{pp}"
            if pid not in nodes:
                nodes[pid] = {
                    "id": pid,
                    "type": "paper",
                    "label": pp.split("/")[-1],
                    "detail": pp,
                    "path": pp,
                    "color": _COLORS["paper"],
                    "href": f"/page/{pp}",
                }
            edges.append({"source": nid, "target": pid, "kind": "from_paper"})
        exp = str(e.get("exp_id") or "").strip()
        if exp:
            xid = f"experiment:{exp}"
            if xid not in nodes:
                nodes[xid] = {
                    "id": xid,
                    "type": "experiment",
                    "label": exp,
                    "detail": exp,
                    "color": _COLORS["experiment"],
                    "href": f"/experiments/{exp}",
                }
            edges.append({"source": nid, "target": xid, "kind": "from_exp"})

    for pp in data.get("paper_paths") or []:
        pp = str(pp).strip("/")
        if not pp:
            continue
        pid = f"paper:{pp}"
        if pid not in nodes:
            nodes[pid] = {
                "id": pid,
                "type": "paper",
                "label": pp.split("/")[-1],
                "detail": pp,
                "path": pp,
                "color": _COLORS["paper"],
                "href": f"/page/{pp}",
            }
        edges.append({"source": f"thread:{tid}", "target": pid, "kind": "member_paper"})

    for exp in data.get("experiment_ids") or []:
        exp = str(exp).strip()
        if not exp:
            continue
        xid = f"experiment:{exp}"
        if xid not in nodes:
            nodes[xid] = {
                "id": xid,
                "type": "experiment",
                "label": exp,
                "detail": exp,
                "color": _COLORS["experiment"],
                "href": f"/experiments/{exp}",
            }
        edges.append({"source": f"thread:{tid}", "target": xid, "kind": "member_exp"})

    # Layout: concentric rings by type
    typed: dict[str, list[str]] = {}
    for nid, n in nodes.items():
        typed.setdefault(str(n["type"]), []).append(nid)
    order = ["thread", "claim", "evidence", "paper", "experiment"]
    for i, t in enumerate(order):
        ids = typed.get(t) or []
        r = 0.15 + i * 0.18
        for j, nid in enumerate(ids):
            ang = (2 * math.pi * j / max(len(ids), 1)) - math.pi / 2
            nodes[nid]["x"] = round(0.5 + r * math.cos(ang), 4)
            nodes[nid]["y"] = round(0.5 + r * math.sin(ang), 4)

    return {
        "thread_id": tid,
        "nodes": list(nodes.values()),
        "edges": edges,
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "claims": len(typed.get("claim") or []),
            "evidences": len(typed.get("evidence") or []),
        },
    }


def group_timeline(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group ledger events by calendar day (UTC date prefix of ts)."""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        ts = str(ev.get("ts") or "")
        day = ts[:10] if len(ts) >= 10 else "unknown"
        buckets.setdefault(day, []).append(ev)
    out = []
    for day in sorted(buckets.keys(), reverse=True):
        out.append({"day": day, "events": list(reversed(buckets[day]))})
    return out
