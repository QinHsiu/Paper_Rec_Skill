"""Knowledge graph: papers + keyword / team / company / venue / tag entities with links."""
from __future__ import annotations

import math
import re
from collections import defaultdict

from app.services.pages_index import list_all_papers

# Heuristic: org/company markers in author strings
_ORG_HINT = re.compile(
    r"(Inc\.?|Ltd\.?|LLC|Corp\.?|Company|Labs?|Laboratory|Institute|University|"
    r"AI|Team|Research|Foundation|Technologies|科技|研究所|大学|实验室)",
    re.I,
)

# Related entities in the same association cluster share one color (and edge color).
CLUSTER_PALETTE = [
    "#1a6b7c",
    "#c45c26",
    "#2d6a4f",
    "#6b4c9a",
    "#b56576",
    "#3d5a80",
    "#8a5a12",
    "#0077b6",
    "#9b2226",
    "#52796f",
]


def _cluster_color(key: str) -> str:
    if not key:
        return CLUSTER_PALETTE[0]
    return CLUSTER_PALETTE[abs(hash(key)) % len(CLUSTER_PALETTE)]


def _split_authors(authors: str) -> list[str]:
    if not authors:
        return []
    parts = re.split(r"[,;/]| and | & ", authors)
    return [p.strip() for p in parts if p.strip()]


def _entity_id(kind: str, name: str) -> str:
    safe = re.sub(r"\s+", "-", name.strip().lower())
    safe = re.sub(r"[^\w\-\u4e00-\u9fff]+", "", safe, flags=re.UNICODE)
    return f"{kind}:{safe or 'unknown'}"


def _classify_author(name: str) -> str:
    """team vs company vs person — coarse labels for graph."""
    if _ORG_HINT.search(name) or len(name.split()) <= 3 and "-" in name:
        # DeepSeek-AI, Qwen Team → team/company
        if re.search(r"Team|Lab|Research|大学|实验室", name, re.I):
            return "team"
        return "company"
    if len(name.split()) >= 2 and name[0].isupper():
        return "team"  # treat multi-token orgs still as team hub
    return "team"


def build_graph() -> dict:
    papers = list_all_papers()
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    entity_papers: dict[str, list[str]] = defaultdict(list)

    def ensure_entity(kind: str, name: str, **extra) -> str:
        name = (name or "").strip()
        if not name:
            return ""
        eid = _entity_id(kind, name)
        if eid not in nodes:
            nodes[eid] = {
                "id": eid,
                "label": name,
                "type": kind,
                "name": name,
                "href": f"/entity/{kind}/{name}",
                "paper_count": 0,
                **extra,
            }
        return eid

    for p in papers:
        pid = p["path"]
        kw = str(p.get("keyword") or "general")
        nodes[pid] = {
            "id": pid,
            "path": pid,
            "label": (p.get("title") or pid)[:48],
            "title": p.get("title") or pid,
            "type": "paper",
            "keyword": kw,
            "added_at": p.get("added_at") or "",
            "score": p.get("score") or "",
            "authors": p.get("authors") or "",
            "venue": p.get("venue") or "",
            "href_page": f"/page/{pid}",
            "href_edit": f"/edit/{pid}",
            "href": f"/page/{pid}",
        }

        # keyword hub
        kid = ensure_entity("keyword", kw)
        if kid:
            edges.append({"source": pid, "target": kid, "kind": "keyword", "cluster": kw})
            entity_papers[kid].append(pid)

        # tags
        for tag in p.get("tags") or []:
            tid = ensure_entity("tag", str(tag))
            if tid:
                edges.append({"source": pid, "target": tid, "kind": "tag", "cluster": kw})
                entity_papers[tid].append(pid)

        # authors → team / company
        for author in _split_authors(str(p.get("authors") or "")):
            kind = _classify_author(author)
            aid = ensure_entity(kind, author)
            if aid:
                edges.append({"source": pid, "target": aid, "kind": kind, "cluster": kw})
                entity_papers[aid].append(pid)

        # venue
        venue = str(p.get("venue") or "").strip()
        if venue and venue.lower() not in ("", "—", "-"):
            for v in re.split(r"[|/]|,", venue):
                v = v.strip()
                if not v:
                    continue
                vid = ensure_entity("venue", v)
                if vid:
                    edges.append({"source": pid, "target": vid, "kind": "venue", "cluster": kw})
                    entity_papers[vid].append(pid)

        # packs (A, A-CN)
        packs = str(p.get("packs") or "")
        for pack in re.split(r"[,;]", packs):
            pack = pack.strip()
            if not pack:
                continue
            pk = ensure_entity("pack", pack)
            if pk:
                edges.append({"source": pid, "target": pk, "kind": "pack", "cluster": kw})
                entity_papers[pk].append(pid)

        nodes[pid]["cluster"] = kw
        nodes[pid]["color"] = _cluster_color(kw)

    # Cognitive Thread + experiment nodes (Phase B)
    try:
        from app.services import thread_store as ts
        from app.services import exp_store

        for t in ts.list_threads():
            tid = t["thread_id"]
            nid = f"thread:{tid}"
            detail = ts.get_thread(tid)
            nodes[nid] = {
                "id": nid,
                "label": (t.get("title") or tid)[:48],
                "title": t.get("title") or tid,
                "type": "thread",
                "thread_id": tid,
                "href": f"/threads/{tid}",
                "cluster": "thread",
                "color": _cluster_color("thread"),
                "paper_count": t.get("paper_count") or 0,
            }
            for path in detail.get("paper_paths") or []:
                if path in nodes:
                    edges.append(
                        {
                            "source": nid,
                            "target": path,
                            "kind": "thread_paper",
                            "cluster": "thread",
                        }
                    )
            for eid in detail.get("experiment_ids") or []:
                exp_nid = f"exp:{eid}"
                if exp_nid not in nodes:
                    try:
                        card = exp_store.get_experiment(eid)
                        title = card.get("title") or eid
                    except FileNotFoundError:
                        title = eid
                    nodes[exp_nid] = {
                        "id": exp_nid,
                        "label": str(title)[:48],
                        "title": title,
                        "type": "experiment",
                        "experiment_id": eid,
                        "href": f"/experiments/{eid}",
                        "cluster": "experiment",
                        "color": _cluster_color("experiment"),
                    }
                edges.append(
                    {
                        "source": nid,
                        "target": exp_nid,
                        "kind": "thread_exp",
                        "cluster": "thread",
                    }
                )
        # orphan experiments (not in any thread) still appear
        for card in exp_store.list_experiments():
            eid = card.get("id") or card.get("path")
            exp_nid = f"exp:{eid}"
            if exp_nid in nodes:
                continue
            nodes[exp_nid] = {
                "id": exp_nid,
                "label": str(card.get("title") or eid)[:48],
                "title": card.get("title") or eid,
                "type": "experiment",
                "experiment_id": eid,
                "href": f"/experiments/{eid}",
                "cluster": "experiment",
                "color": _cluster_color("experiment"),
            }
            for path in card.get("paper_refs") or []:
                if path in nodes:
                    edges.append(
                        {
                            "source": exp_nid,
                            "target": path,
                            "kind": "exp_paper",
                            "cluster": "experiment",
                        }
                    )
    except Exception:
        pass

    for eid, plist in entity_papers.items():
        if eid in nodes:
            nodes[eid]["paper_count"] = len(set(plist))
            nodes[eid]["papers"] = list(dict.fromkeys(plist))

    # Entity cluster = majority paper keyword among linked papers
    entity_cluster_votes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for e in edges:
        src, tgt = e["source"], e["target"]
        cluster = e.get("cluster") or "general"
        e["color"] = _cluster_color(cluster)
        if tgt in nodes and nodes[tgt]["type"] != "paper":
            entity_cluster_votes[tgt][cluster] += 1
        if src in nodes and nodes[src]["type"] != "paper":
            entity_cluster_votes[src][cluster] += 1

    for eid, votes in entity_cluster_votes.items():
        best = max(votes.items(), key=lambda kv: kv[1])[0]
        nodes[eid]["cluster"] = best
        nodes[eid]["color"] = _cluster_color(best)

    # layout: papers on outer ring, entities on inner rings by type
    type_ring = {
        "paper": 95,
        "keyword": 55,
        "tag": 42,
        "team": 28,
        "company": 28,
        "venue": 18,
        "pack": 12,
        "thread": 70,
        "experiment": 62,
    }
    by_type: dict[str, list[str]] = defaultdict(list)
    for nid, node in nodes.items():
        by_type[node["type"]].append(nid)
        if "color" not in node:
            node["cluster"] = node.get("cluster") or "general"
            node["color"] = _cluster_color(node["cluster"])

    for typ, ids in by_type.items():
        ring = type_ring.get(typ, 50)
        n = max(len(ids), 1)
        for i, nid in enumerate(sorted(ids)):
            ang = 2 * math.pi * i / n + (hash(typ) % 7) * 0.1
            jitter = (hash(nid) % 11) - 5
            nodes[nid]["x"] = math.cos(ang) * (ring + jitter * 0.4)
            nodes[nid]["y"] = math.sin(ang) * (ring + jitter * 0.4)

    # Cluster legend (same color for related entities + edges)
    cluster_counts: dict[str, int] = defaultdict(int)
    for node in nodes.values():
        cluster_counts[node.get("cluster") or "general"] += 1
    cluster_legends = [
        {
            "cluster": c,
            "count": n,
            "color": _cluster_color(c),
        }
        for c, n in sorted(cluster_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    type_legends = []
    for typ in ("keyword", "tag", "team", "company", "venue", "pack", "paper", "thread", "experiment"):
        ids = by_type.get(typ) or []
        if not ids:
            continue
        type_legends.append({"type": typ, "count": len(ids)})

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "legends": type_legends,
        "clusters": cluster_legends,
        "keywords": [
            {"keyword": nodes[i]["label"], "count": nodes[i].get("paper_count", 0)}
            for i in by_type.get("keyword", [])
        ],
    }


def papers_for_entity(kind: str, name: str) -> dict:
    """Resolve entity → linked papers for /entity/:type/:name."""
    data = build_graph()
    eid = _entity_id(kind, name)
    node = next((n for n in data["nodes"] if n["id"] == eid), None)
    # fuzzy: match by label
    if not node:
        name_l = name.strip().lower()
        node = next(
            (
                n
                for n in data["nodes"]
                if n.get("type") == kind and str(n.get("label") or "").lower() == name_l
            ),
            None,
        )
    if not node:
        return {"entity": {"type": kind, "name": name}, "papers": [], "related": []}

    paper_ids = set(node.get("papers") or [])
    # also collect via edges
    for e in data["edges"]:
        if e["target"] == node["id"] and e["source"] in {
            n["id"] for n in data["nodes"] if n["type"] == "paper"
        }:
            paper_ids.add(e["source"])
        if e["source"] == node["id"]:
            paper_ids.add(e["target"])

    papers = [n for n in data["nodes"] if n["id"] in paper_ids and n["type"] == "paper"]

    # related entities sharing papers
    related_ids: set[str] = set()
    for e in data["edges"]:
        if e["source"] in paper_ids and e["target"] != node["id"]:
            related_ids.add(e["target"])
        if e["target"] in paper_ids and e["source"] != node["id"] and e["source"] not in paper_ids:
            related_ids.add(e["source"])
    related = [
        n
        for n in data["nodes"]
        if n["id"] in related_ids and n["type"] != "paper"
    ]
    related.sort(key=lambda x: (-(x.get("paper_count") or 0), x.get("label") or ""))

    return {
        "entity": {
            "id": node["id"],
            "type": node["type"],
            "name": node.get("label") or name,
            "href": node.get("href"),
            "paper_count": len(papers),
        },
        "papers": papers,
        "related": related[:40],
    }
