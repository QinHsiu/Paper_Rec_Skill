"""Thread state kernel: proposals, feedback patterns, verify gate, consolidate.

Thread JSON remains the only research-state source of truth. Retrieval, verify,
and experiment results propose updates; they do not write around the thread.

Risk tiers (friction as a feature):
- low: auto-apply, timeline event is rollbackable (new candidate evidence / gap pending)
- medium: explicit accept (claim state change, reject an evidence)
- high: accept requires a reason (delete a node, merge gaps, distill a skill)
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from . import thread_evidence as te
from . import thread_store as ts

NODE_STATES = ("candidate", "verified", "rejected", "pending")
RISK_OF = {
    "add_claim": "low",
    "add_gap": "low",
    "add_evidence": "low",
    "add_experiment": "low",
    "mark_pending": "low",
    "set_node_state": "medium",
    "reject_evidence": "medium",
    "confirm_draft": "medium",
    "delete_node": "high",
    "merge_gap": "high",
    "distill_skill": "high",
}
VERDICT_LABELS = {
    "thread_pass": "主线验证通过",
    "needs_screen": "待人工筛选",
    "thread_conflict": "主线冲突",
    "abstain": "弃权",
}
_NOT_REPORTED = re.compile(
    r"not reported|未公开|n/?a|no public metric|metrics not reported|未找到公开指标",
    re.I,
)
_NUMBER = re.compile(r"\d")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")


def _proposals_path(wiki_root: Path, thread_id: str) -> Path:
    return ts.thread_dir(wiki_root, thread_id) / "proposals.jsonl"


def _feedback_path(wiki_root: Path, thread_id: str) -> Path:
    return ts.thread_dir(wiki_root, thread_id) / "feedback.jsonl"


def _rollback_path(wiki_root: Path, thread_id: str) -> Path:
    return ts.thread_dir(wiki_root, thread_id) / "rollbacks.jsonl"


def list_proposals(wiki_root: Path, thread_id: str) -> list[dict[str, Any]]:
    ts.load_thread(wiki_root, thread_id)
    return _read_jsonl(_proposals_path(wiki_root, thread_id))


def list_feedback(wiki_root: Path, thread_id: str) -> list[dict[str, Any]]:
    ts.load_thread(wiki_root, thread_id)
    return _read_jsonl(_feedback_path(wiki_root, thread_id))


def _next_seq(rows: list[dict[str, Any]], key: str, prefix: str) -> str:
    n = 0
    for row in rows:
        m = re.match(rf"^{prefix}(\d+)$", str(row.get(key) or ""), re.I)
        if m:
            n = max(n, int(m.group(1)))
    return f"{prefix}{n + 1}"


def _preference(data: dict[str, Any]) -> dict[str, list[str]]:
    raw = data.get("preference") if isinstance(data.get("preference"), dict) else {}
    return {
        "accepted_patterns": [str(x) for x in (raw.get("accepted_patterns") or []) if str(x).strip()],
        "rejected_patterns": [str(x) for x in (raw.get("rejected_patterns") or []) if str(x).strip()],
    }


def _remember_pattern(wiki_root: Path, thread_id: str, action: str, pattern: str) -> None:
    pattern = (pattern or "").strip()
    if not pattern:
        return
    if action in ("accept", "pin", "read"):
        bucket = "accepted_patterns"
    elif action in ("reject", "skip"):
        bucket = "rejected_patterns"
    else:
        return
    data = ts.load_thread(wiki_root, thread_id)
    pref = _preference(data)
    if pattern not in pref[bucket]:
        pref[bucket].append(pattern)
    pref[bucket] = pref[bucket][-40:]
    data["preference"] = pref
    ts.save_thread(wiki_root, data)


def _append_feedback(
    wiki_root: Path,
    thread_id: str,
    *,
    kind: str,
    action: str,
    target: str,
    pattern: str = "",
    entities: list[str] | None = None,
) -> dict[str, Any]:
    row = {
        "ts": ts.utc_now_iso(),
        "kind": kind,
        "action": action,
        "target": target,
        "pattern": pattern,
        "entities": list(entities or []),
    }
    path = _feedback_path(wiki_root, thread_id)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    _remember_pattern(wiki_root, thread_id, action, pattern)
    return row


def note_paper_feedback(
    wiki_root: Path,
    thread_id: str,
    *,
    action: str,
    path: str = "",
    note: str = "",
) -> dict[str, Any]:
    """Record retrieval feedback used as a soft preference and a rank prior."""
    action = (action or "").strip().lower()
    tokens = ts._tokenize(f"{path.replace('/', ' ').replace('-', ' ')} {note}")
    if action in ("accept", "pin", "read"):
        mapped = "accept"
        pattern = (note or "").strip()
        entities = tokens[:12]
    elif action == "skip":
        mapped = "reject"
        pattern = (note or "").strip() or f"skipped:{path}"
        entities = []
    else:
        mapped = action
        pattern = (note or "").strip()
        entities = []
    return _append_feedback(
        wiki_root,
        thread_id,
        kind="paper",
        action=mapped,
        target=path,
        pattern=pattern,
        entities=entities,
    )


def feedback_profile(wiki_root: Path, thread_id: str) -> dict[str, Any]:
    rows = list_feedback(wiki_root, thread_id)
    accepted: list[str] = []
    rejected: list[str] = []
    for row in rows:
        if row.get("action") in ("accept", "pin", "read") and row.get("kind") == "paper":
            accepted.extend(str(t) for t in (row.get("entities") or []))
        if row.get("action") in ("reject", "skip") and row.get("pattern"):
            rejected.extend(ts._tokenize(str(row.get("pattern"))))
    data = ts.load_thread(wiki_root, thread_id)
    pref = _preference(data)
    for pat in pref["rejected_patterns"]:
        rejected.extend(ts._tokenize(pat))
    return {
        "accepted_entities": sorted(set(accepted)),
        "rejected_terms": sorted(set(rejected)),
        "accepted_patterns": pref["accepted_patterns"],
        "rejected_patterns": pref["rejected_patterns"],
    }


def _payload_text(payload: dict[str, Any]) -> str:
    parts = [
        str(payload.get("text") or ""),
        str(payload.get("note") or ""),
        str(payload.get("quote") or ""),
        str(payload.get("pattern") or ""),
        str(payload.get("reason") or ""),
    ]
    return " ".join(p for p in parts if p).strip()


def _hits_rejected_pattern(wiki_root: Path, thread_id: str, text: str) -> str:
    data = ts.load_thread(wiki_root, thread_id)
    bag = set(ts._tokenize(text))
    if not bag:
        return ""
    for pattern in _preference(data)["rejected_patterns"]:
        pb = set(ts._tokenize(pattern))
        if pb and ts._jaccard(bag, pb) >= 0.5:
            return pattern
    return ""


def _node_id(rows: list[dict[str, Any]], prefix: str) -> str:
    n = 0
    for row in rows:
        m = re.match(rf"^{prefix}(\d+)$", str(row.get("id") or ""), re.I)
        if m:
            n = max(n, int(m.group(1)))
    return f"{prefix}{n + 1}"


def _pending_payloads(wiki_root: Path, thread_id: str, op: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in list_proposals(wiki_root, thread_id):
        if row.get("op") == op and row.get("status") == "pending":
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            out.append(payload)
    return out


def proposal_summary(proposal: dict[str, Any]) -> str:
    payload = proposal.get("payload") if isinstance(proposal.get("payload"), dict) else {}
    text = _payload_text(payload) or str(proposal.get("op") or "")
    return f"{proposal.get('op')}: {text[:180]}"


def propose(
    wiki_root: Path,
    thread_id: str,
    op: str,
    payload: dict[str, Any] | None = None,
    *,
    source: str = "agent",
    by: str = "agent",
    reason: str = "",
    force_pending: bool = False,
) -> dict[str, Any]:
    if op not in RISK_OF:
        raise ValueError(f"unknown op: {op}")
    ts.load_thread(wiki_root, thread_id)
    payload = dict(payload or {})
    risk = RISK_OF[op]
    held = _hits_rejected_pattern(wiki_root, thread_id, _payload_text(payload))
    rows = list_proposals(wiki_root, thread_id)
    proposal = {
        "proposal_id": _next_seq(rows, "proposal_id", "P"),
        "ts": ts.utc_now_iso(),
        "source": source,
        "by": by,
        "op": op,
        "risk": risk,
        "status": "pending",
        "reason": reason,
        "payload": payload,
        "held_by": held,
        "rollback_id": "",
    }
    auto = risk == "low" and not force_pending and not held
    if auto:
        rollback_id = _apply_op(wiki_root, thread_id, op, payload)
        proposal["status"] = "applied"
        proposal["rollback_id"] = rollback_id
    rows.append(proposal)
    _write_jsonl(_proposals_path(wiki_root, thread_id), rows)
    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "thread_proposal",
            "proposal_id": proposal["proposal_id"],
            "op": op,
            "risk": risk,
            "status": proposal["status"],
            "source": source,
            "by": by,
            "held_by": held,
        },
    )
    rebuild_hot_memory(wiki_root, thread_id)
    proposal["thread_status"] = ts.load_thread(wiki_root, thread_id).get("status")
    return proposal


def decide(
    wiki_root: Path,
    thread_id: str,
    proposal_id: str,
    action: str,
    *,
    reason: str = "",
    by: str = "user",
) -> dict[str, Any]:
    action = (action or "").strip().lower()
    if action not in ("accept", "reject", "defer"):
        raise ValueError("action must be accept|reject|defer")
    if proposal_id == "all":
        results = []
        blocked = []
        for row in list_proposals(wiki_root, thread_id):
            if row.get("status") != "pending":
                continue
            if row.get("risk") == "high" and action == "accept" and not (reason or "").strip():
                blocked.append(row.get("proposal_id"))
                continue
            results.append(
                decide(wiki_root, thread_id, str(row.get("proposal_id")), action, reason=reason, by=by)
            )
        return {"action": action, "results": results, "blocked_high": blocked}

    rows = list_proposals(wiki_root, thread_id)
    target = next((r for r in rows if r.get("proposal_id") == proposal_id), None)
    if target is None:
        raise KeyError(proposal_id)
    if target.get("status") != "pending":
        raise ValueError(f"proposal {proposal_id} is {target.get('status')}")
    if action == "accept" and target.get("risk") == "high" and not (reason or "").strip():
        raise ValueError("high-risk accept requires a reason")
    if action == "accept":
        payload = target.get("payload") if isinstance(target.get("payload"), dict) else {}
        rollback_id = _apply_op(wiki_root, thread_id, str(target.get("op")), payload)
        target["status"] = "accepted"
        target["rollback_id"] = rollback_id
        target["decision_reason"] = reason
    elif action == "reject":
        target["status"] = "rejected"
        target["decision_reason"] = reason
    else:
        target["status"] = "deferred"
        target["decision_reason"] = reason
    target["decided_at"] = ts.utc_now_iso()
    target["decided_by"] = by
    _write_jsonl(_proposals_path(wiki_root, thread_id), rows)
    pattern = (reason or "").strip() or proposal_summary(target)
    if action in ("accept", "reject"):
        _append_feedback(
            wiki_root,
            thread_id,
            kind="proposal",
            action=action,
            target=proposal_id,
            pattern=pattern,
            entities=ts._tokenize(pattern)[:12],
        )
    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "thread_decision",
            "proposal_id": proposal_id,
            "action": action,
            "reason": reason,
            "source": target.get("source") or "",
            "by": by,
        },
    )
    rebuild_hot_memory(wiki_root, thread_id)
    return target


def rollback(wiki_root: Path, thread_id: str, proposal_id: str, *, by: str = "user") -> dict[str, Any]:
    rows = list_proposals(wiki_root, thread_id)
    target = next((r for r in rows if r.get("proposal_id") == proposal_id), None)
    if target is None:
        raise KeyError(proposal_id)
    rollback_id = str(target.get("rollback_id") or "")
    snaps = _read_jsonl(_rollback_path(wiki_root, thread_id))
    snap = next((s for s in snaps if s.get("rollback_id") == rollback_id), None)
    if snap is None:
        raise ValueError(f"no rollback snapshot for {proposal_id}")
    data = ts.load_thread(wiki_root, thread_id)
    before = snap.get("before") if isinstance(snap.get("before"), dict) else {}
    for key, value in before.items():
        data[key] = value
    ts.save_thread(wiki_root, data)
    if "evidences" in snap:
        te._rewrite_evidences(wiki_root, thread_id, list(snap.get("evidences") or []))
    target["status"] = "rolled_back"
    _write_jsonl(_proposals_path(wiki_root, thread_id), rows)
    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "thread_rollback",
            "proposal_id": proposal_id,
            "rollback_id": rollback_id,
            "source": "timeline",
            "by": by,
        },
    )
    rebuild_hot_memory(wiki_root, thread_id)
    return target


def _snapshot(
    wiki_root: Path,
    thread_id: str,
    proposal_op: str,
    keys: list[str],
    *,
    include_evidences: bool = False,
) -> str:
    data = ts.load_thread(wiki_root, thread_id)
    snaps = _read_jsonl(_rollback_path(wiki_root, thread_id))
    rollback_id = _next_seq(snaps, "rollback_id", "RB")
    snap: dict[str, Any] = {
        "rollback_id": rollback_id,
        "ts": ts.utc_now_iso(),
        "op": proposal_op,
        "before": {k: data.get(k) for k in keys},
    }
    if include_evidences:
        snap["evidences"] = te.list_evidences(wiki_root, thread_id)
        snap["before"]["claims"] = data.get("claims")
        snap["before"]["paper_paths"] = data.get("paper_paths")
    snaps.append(snap)
    _write_jsonl(_rollback_path(wiki_root, thread_id), snaps)
    return rollback_id


def _apply_op(wiki_root: Path, thread_id: str, op: str, payload: dict[str, Any]) -> str:
    if op == "add_claim":
        return _apply_add_claim(wiki_root, thread_id, payload)
    if op == "add_gap":
        return _apply_add_gap(wiki_root, thread_id, payload)
    if op == "add_evidence":
        return _apply_add_evidence(wiki_root, thread_id, payload)
    if op == "add_experiment":
        return _apply_add_experiment(wiki_root, thread_id, payload)
    if op == "mark_pending":
        return _apply_set_state(wiki_root, thread_id, {**payload, "node_state": "pending"})
    if op == "set_node_state":
        return _apply_set_state(wiki_root, thread_id, payload)
    if op == "reject_evidence":
        return _apply_reject_evidence(wiki_root, thread_id, payload)
    if op == "delete_node":
        return _apply_delete(wiki_root, thread_id, payload)
    if op == "merge_gap":
        return _apply_merge_gap(wiki_root, thread_id, payload)
    if op == "confirm_draft":
        return _apply_confirm_draft(wiki_root, thread_id)
    if op == "distill_skill":
        return _apply_distill(wiki_root, thread_id, payload)
    raise ValueError(f"unknown op: {op}")


def _apply_add_claim(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    rollback_id = _snapshot(wiki_root, thread_id, "add_claim", ["claims"])
    data = ts.load_thread(wiki_root, thread_id)
    claims = [dict(c) for c in (data.get("claims") or [])]
    reserved = [str(p.get("id")) for p in _pending_payloads(wiki_root, thread_id, "add_claim")]
    cid = str(payload.get("id") or "").strip() or _node_id(claims + [{"id": i} for i in reserved], "C")
    if any(str(c.get("id")) == cid for c in claims):
        return rollback_id
    state = str(payload.get("node_state") or "candidate")
    if state not in NODE_STATES:
        state = "candidate"
    claims.append(
        {
            "id": cid,
            "text": str(payload.get("text") or "").strip(),
            "status": "open",
            "node_state": state,
            "support_n": int(payload.get("support_n") or 1),
        }
    )
    data["claims"] = claims
    ts.save_thread(wiki_root, data)
    return rollback_id


def _apply_add_gap(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    rollback_id = _snapshot(wiki_root, thread_id, "add_gap", ["evidence_gaps"])
    data = ts.load_thread(wiki_root, thread_id)
    gaps = [dict(g) for g in (data.get("evidence_gaps") or [])]
    gid = str(payload.get("id") or "").strip() or _node_id(gaps, "G")
    state = str(payload.get("node_state") or "candidate")
    if state not in NODE_STATES:
        state = "candidate"
    gaps.append(
        {
            "id": gid,
            "claim_id": str(payload.get("claim_id") or ""),
            "need": str(payload.get("need") or "evidence"),
            "note": str(payload.get("note") or "").strip(),
            "node_state": state,
        }
    )
    data["evidence_gaps"] = gaps
    ts.save_thread(wiki_root, data)
    return rollback_id


def _apply_add_evidence(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    rollback_id = _snapshot(
        wiki_root, thread_id, "add_evidence", ["claims", "paper_paths"], include_evidences=True
    )
    rec = te.add_evidence(
        wiki_root,
        thread_id,
        claim_id=str(payload.get("claim_id") or ""),
        kind=str(payload.get("kind") or "quote"),
        paper_path=str(payload.get("paper_path") or payload.get("path") or ""),
        quote=str(payload.get("quote") or ""),
        stance=str(payload.get("stance") or "supports"),
        gate="suggested",
        by="proposal",
    )
    rows = te.list_evidences(wiki_root, thread_id)
    for row in rows:
        if row.get("evidence_id") == rec.get("evidence_id"):
            row["node_state"] = "candidate"
    te._rewrite_evidences(wiki_root, thread_id, rows)
    return rollback_id


def _apply_add_experiment(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    rollback_id = _snapshot(wiki_root, thread_id, "add_experiment", ["experiment_ids", "experiment_nodes"])
    from .conventions import slugify

    data = ts.load_thread(wiki_root, thread_id)
    eid = str(payload.get("id") or slugify(str(payload.get("title") or "experiment"), max_len=60))
    state = str(payload.get("node_state") or "candidate")
    if state not in NODE_STATES:
        state = "candidate"
    ids = list(data.get("experiment_ids") or [])
    nodes = [dict(n) for n in (data.get("experiment_nodes") or [])]
    if eid and eid not in ids:
        ids.append(eid)
    if eid and not any(str(n.get("id")) == eid for n in nodes):
        nodes.append(
            {
                "id": eid,
                "title": str(payload.get("title") or eid),
                "note": str(payload.get("note") or ""),
                "node_state": state,
            }
        )
    data["experiment_ids"] = ids
    data["experiment_nodes"] = nodes
    ts.save_thread(wiki_root, data)
    return rollback_id


def _apply_set_state(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    kind = str(payload.get("kind") or "claim")
    node_state = str(payload.get("node_state") or "")
    if node_state not in NODE_STATES:
        raise ValueError("node_state must be candidate|verified|rejected|pending")
    node_id = str(payload.get("id") or "")
    if kind == "evidence":
        rollback_id = _snapshot(
            wiki_root, thread_id, "set_node_state", ["claims"], include_evidences=True
        )
        rows = te.list_evidences(wiki_root, thread_id)
        hit = False
        for row in rows:
            if str(row.get("evidence_id")) == node_id:
                row["node_state"] = node_state
                hit = True
        if not hit:
            raise KeyError(node_id)
        te._rewrite_evidences(wiki_root, thread_id, rows)
        return rollback_id
    field = {"claim": "claims", "experiment": "experiment_nodes"}.get(kind, "evidence_gaps")
    id_key = "id"
    rollback_id = _snapshot(wiki_root, thread_id, "set_node_state", [field])
    data = ts.load_thread(wiki_root, thread_id)
    nodes = [dict(n) for n in (data.get(field) or [])]
    hit = False
    for node in nodes:
        if str(node.get(id_key)) == node_id:
            node["node_state"] = node_state
            hit = True
    if not hit:
        raise KeyError(node_id)
    data[field] = nodes
    ts.save_thread(wiki_root, data)
    return rollback_id


def _apply_reject_evidence(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    return _apply_set_state(
        wiki_root,
        thread_id,
        {"kind": "evidence", "id": payload.get("evidence_id") or payload.get("id"), "node_state": "rejected"},
    )


def _apply_delete(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    kind = str(payload.get("kind") or "claim")
    node_id = str(payload.get("id") or "")
    if kind == "evidence":
        rollback_id = _snapshot(
            wiki_root, thread_id, "delete_node", ["claims"], include_evidences=True
        )
        rows = [r for r in te.list_evidences(wiki_root, thread_id) if str(r.get("evidence_id")) != node_id]
        te._rewrite_evidences(wiki_root, thread_id, rows)
        return rollback_id
    field = {"claim": "claims", "experiment": "experiment_nodes"}.get(kind, "evidence_gaps")
    extra = ["experiment_ids"] if kind == "experiment" else []
    rollback_id = _snapshot(wiki_root, thread_id, "delete_node", [field, *extra])
    data = ts.load_thread(wiki_root, thread_id)
    data[field] = [n for n in (data.get(field) or []) if str(n.get("id")) != node_id]
    if kind == "experiment":
        data["experiment_ids"] = [e for e in (data.get("experiment_ids") or []) if e != node_id]
    ts.save_thread(wiki_root, data)
    return rollback_id


def _apply_merge_gap(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    rollback_id = _snapshot(wiki_root, thread_id, "merge_gap", ["evidence_gaps"])
    data = ts.load_thread(wiki_root, thread_id)
    gaps = [dict(g) for g in (data.get("evidence_gaps") or [])]
    keep = str(payload.get("keep_id") or "")
    drop = str(payload.get("drop_id") or "")
    kept = next((g for g in gaps if str(g.get("id")) == keep), None)
    if kept is None:
        raise KeyError(keep)
    dropped = [g for g in gaps if str(g.get("id")) == drop]
    if not dropped:
        raise KeyError(drop)
    extra = str(dropped[0].get("note") or "").strip()
    if extra and extra not in str(kept.get("note") or ""):
        kept["note"] = (str(kept.get("note") or "").strip() + " | " + extra).strip(" |")
    kept["node_state"] = kept.get("node_state") or "pending"
    data["evidence_gaps"] = [g for g in gaps if str(g.get("id")) != drop]
    ts.save_thread(wiki_root, data)
    return rollback_id


def _apply_confirm_draft(wiki_root: Path, thread_id: str) -> str:
    rollback_id = _snapshot(wiki_root, thread_id, "confirm_draft", ["status"])
    data = ts.load_thread(wiki_root, thread_id)
    data["status"] = "active"
    ts.save_thread(wiki_root, data)
    return rollback_id


def _apply_distill(wiki_root: Path, thread_id: str, payload: dict[str, Any]) -> str:
    rollback_id = _snapshot(wiki_root, thread_id, "distill_skill", ["preference"])
    sequence = [str(x) for x in (payload.get("sequence") or [])]
    from .conventions import slugify

    slug = slugify("-".join(sequence) or "sequence", max_len=60)
    data = ts.load_thread(wiki_root, thread_id)
    domain_src = (data.get("tags") or data.get("keywords") or ["general"])[0]
    domain = slugify(str(domain_src) or "general", max_len=40) or "general"
    steps = "\n".join(f"{i}. `{name}`" for i, name in enumerate(sequence, start=1))
    text = (
        f"---\nname: {thread_id}-{slug}\n"
        f"description: Distilled from repeated thread operations on {thread_id}.\n---\n\n"
        f"# Distilled thread skill\n\n"
        f"Domain: {domain}\n\n"
        f"This skill records a repeated operation sequence. It does not add a new agent.\n\n"
        f"## Sequence\n\n{steps or '- (empty)'}\n\n"
        f"## Use\n\nWhen the same retrieval, verify, and mount sequence appears again, "
        f"follow this order and keep writing proposals to the thread instead of local notes.\n"
        f"Run `run.py` to print the sequence. It does not execute the steps.\n"
    )
    script = (
        "\"\"\"Print the distilled operation sequence. Does not execute it.\"\"\"\n"
        f"SEQUENCE = {sequence!r}\n\n"
        "def main() -> None:\n"
        "    for step in SEQUENCE:\n"
        "        print(step)\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )
    for folder in (
        ts.thread_dir(wiki_root, thread_id) / "skills" / slug,
        ts.workspace_from_wiki_root(wiki_root) / "content" / "skills" / "distilled" / domain / slug,
    ):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(text, encoding="utf-8")
        (folder / "run.py").write_text(script, encoding="utf-8")
    index_path = ts.workspace_from_wiki_root(wiki_root) / "content" / "skills" / "distilled" / "index.json"
    catalog: dict[str, Any] = {}
    if index_path.is_file():
        try:
            loaded = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                catalog = loaded
        except json.JSONDecodeError:
            catalog = {}
    domain_node = catalog.setdefault(domain, {})
    rel = f"content/skills/distilled/{domain}/{slug}"
    domain_node[slug] = {"thread_id": thread_id, "sequence": sequence, "path": rel}
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rollback_id


def proposal_stats(wiki_root: Path, thread_id: str) -> dict[str, Any]:
    """Acceptance rate of explicit proposal decisions. Auto-applied lows are counted apart."""
    rows = list_proposals(wiki_root, thread_id)
    accepted = sum(1 for row in rows if row.get("status") == "accepted")
    rejected = sum(1 for row in rows if row.get("status") == "rejected")
    decided = accepted + rejected
    feedback = list_feedback(wiki_root, thread_id)
    return {
        "accepted": accepted,
        "rejected": rejected,
        "deferred": sum(1 for row in rows if row.get("status") == "deferred"),
        "applied": sum(1 for row in rows if row.get("status") == "applied"),
        "pending": sum(1 for row in rows if row.get("status") == "pending"),
        "acceptance_rate": (accepted / decided) if decided else None,
        "paper_accept": sum(1 for row in feedback if row.get("kind") == "paper" and row.get("action") == "accept"),
        "paper_reject": sum(1 for row in feedback if row.get("kind") == "paper" and row.get("action") == "reject"),
    }


def skill_catalog(wiki_root: Path, domain: str = "") -> dict[str, Any]:
    """Route distilled skills by domain, then by task slug."""
    from .conventions import slugify

    index = ts.workspace_from_wiki_root(wiki_root) / "content" / "skills" / "distilled" / "index.json"
    catalog: dict[str, Any] = {}
    if index.is_file():
        try:
            loaded = json.loads(index.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                catalog = loaded
        except json.JSONDecodeError:
            catalog = {}
    if domain:
        key = slugify(domain, max_len=40)
        return {"domain": key, "skills": catalog.get(key) or catalog.get(domain) or {}}
    return {"domains": sorted(catalog), "catalog": catalog}


def rebuild_hot_memory(wiki_root: Path, thread_id: str) -> dict[str, Any]:
    data = ts.load_thread(wiki_root, thread_id)
    claims = [
        c
        for c in (data.get("claims") or [])
        if str(c.get("node_state") or "candidate") != "rejected"
    ][:8]
    gaps = [
        g
        for g in (data.get("evidence_gaps") or [])
        if str(g.get("node_state") or "candidate") != "rejected"
    ][:8]
    hot = {
        "layer": "hot",
        "thread_id": data.get("thread_id") or thread_id,
        "title": data.get("title") or "",
        "status": data.get("status") or "",
        "hypothesis": data.get("hypothesis") or "",
        "claims": claims,
        "evidence_gaps": gaps,
        "preference": _preference(data),
        "experiment_nodes": [
            n
            for n in (data.get("experiment_nodes") or [])
            if str(n.get("node_state") or "candidate") != "rejected"
        ][:8],
        "proposal_stats": proposal_stats(wiki_root, thread_id),
        "recent_events": ts.list_events(wiki_root, thread_id, limit=12),
        "archive": {
            "thread": "thread.json",
            "events": "events.jsonl",
            "feedback": "feedback.jsonl",
            "proposals": "proposals.jsonl",
        },
        "updated_at": ts.utc_now_iso(),
    }
    path = ts.thread_dir(wiki_root, thread_id) / "memory_hot.json"
    path.write_text(json.dumps(hot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    archive = {
        "layer": "archive",
        "thread_id": thread_id,
        "events": len(ts.list_events(wiki_root, thread_id, limit=10000)),
        "feedback": len(list_feedback(wiki_root, thread_id)),
        "proposals": len(list_proposals(wiki_root, thread_id)),
        "files": hot["archive"],
        "updated_at": hot["updated_at"],
    }
    (ts.thread_dir(wiki_root, thread_id) / "memory_archive.json").write_text(
        json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return hot


def load_papers(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        rows = raw.get("papers") or raw.get("items") or raw.get("candidates") or []
    else:
        rows = raw
    return [r for r in rows if isinstance(r, dict)]


def _paper_blob(paper: dict[str, Any]) -> str:
    return " ".join(
        str(paper.get(k) or "")
        for k in ("title", "summary", "abstract", "core_idea", "contribution", "method", "weaknesses", "metrics")
    )


def _first_sentence(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    parts = re.split(r"[。\n]+|(?<=[.!?])\s+", text)
    for part in parts:
        if len(part.strip()) >= 8:
            return part.strip()
    return text[:240]


def _cluster(sentences: list[str], threshold: float = 0.34) -> list[list[str]]:
    clusters: list[list[str]] = []
    for sentence in sentences:
        bag = set(ts._tokenize(sentence))
        if not bag:
            continue
        placed = False
        for cluster in clusters:
            if ts._jaccard(bag, set(ts._tokenize(cluster[0]))) >= threshold:
                cluster.append(sentence)
                placed = True
                break
        if not placed:
            clusters.append([sentence])
    clusters.sort(key=len, reverse=True)
    return clusters


def bootstrap_thread(
    wiki_root: Path,
    papers: list[dict[str, Any]],
    *,
    thread_id: str = "",
    title: str = "",
    hypothesis: str = "",
) -> dict[str, Any]:
    """Draft candidate claims, gaps, and evidence as pending proposals."""
    claim_src: list[str] = []
    gap_src: list[str] = []
    for paper in papers:
        sentence = _first_sentence(
            str(paper.get("contribution") or paper.get("core_idea") or paper.get("summary") or paper.get("abstract") or "")
        )
        if sentence:
            claim_src.append(sentence)
        gap = _first_sentence(str(paper.get("weaknesses") or paper.get("limitation") or ""))
        if gap:
            gap_src.append(gap)
    claim_clusters = [c for c in _cluster(claim_src) if len(c) >= 2] or _cluster(claim_src)[:3]
    gap_clusters = [c for c in _cluster(gap_src) if len(c) >= 2] or _cluster(gap_src)[:3]
    created = False
    if thread_id and (ts.thread_dir(wiki_root, thread_id) / "thread.json").is_file():
        data = ts.load_thread(wiki_root, thread_id)
    else:
        created = True
        data = ts.create_thread(
            wiki_root,
            title or "Draft thread",
            thread_id=thread_id,
            hypothesis=hypothesis or "Synthesize candidate claims and gaps from the retrieved set.",
        )
        data = ts.load_thread(wiki_root, data["thread_id"])
        data["status"] = "draft"
        ts.save_thread(wiki_root, data)
    tid = str(data.get("thread_id"))
    proposals: list[dict[str, Any]] = []
    claim_payloads: list[dict[str, Any]] = []
    existing_claims = list(data.get("claims") or [])
    for cluster in claim_clusters[:5]:
        cid = _node_id(existing_claims + claim_payloads, "C")
        payload = {"id": cid, "text": max(cluster, key=len), "node_state": "candidate", "support_n": len(cluster)}
        claim_payloads.append(payload)
        proposals.append(
            propose(wiki_root, tid, "add_claim", payload, source="bootstrap", force_pending=True)
        )
    for cluster in gap_clusters[:5]:
        payload = {
            "id": "",
            "note": max(cluster, key=len),
            "need": "evidence",
            "node_state": "candidate",
            "claim_id": claim_payloads[0]["id"] if claim_payloads else "",
        }
        proposals.append(propose(wiki_root, tid, "add_gap", payload, source="bootstrap", force_pending=True))
    for paper in papers[:8]:
        quote = _first_sentence(str(paper.get("core_idea") or paper.get("contribution") or paper.get("summary") or ""))
        if not quote or not claim_payloads:
            continue
        best = claim_payloads[0]
        best_j = -1.0
        qbag = set(ts._tokenize(quote))
        for payload in claim_payloads:
            score = ts._jaccard(qbag, set(ts._tokenize(str(payload.get("text")))))
            if score > best_j:
                best_j = score
                best = payload
        proposals.append(
            propose(
                wiki_root,
                tid,
                "add_evidence",
                {
                    "claim_id": best["id"],
                    "quote": quote,
                    "paper_path": str(paper.get("path") or ""),
                    "kind": "quote",
                },
                source="bootstrap",
                force_pending=True,
            )
        )
    if created:
        proposals.append(
            propose(wiki_root, tid, "confirm_draft", {"title": data.get("title")}, source="bootstrap", force_pending=True)
        )
    return {
        "thread_id": tid,
        "created": created,
        "status": ts.load_thread(wiki_root, tid).get("status"),
        "proposals": [{"proposal_id": p["proposal_id"], "op": p["op"], "status": p["status"]} for p in proposals],
    }


def _dim(result: str, reason: str) -> dict[str, str]:
    return {"result": result, "reason": reason}


def _best_jaccard(text: str, blobs: list[str]) -> float:
    bag = set(ts._tokenize(text))
    if not bag or not blobs:
        return 0.0
    return max(ts._jaccard(bag, set(ts._tokenize(b))) for b in blobs)


def _open_nodes(nodes: list[dict[str, Any]], text_keys: tuple[str, ...]) -> list[str]:
    blobs: list[str] = []
    for node in nodes:
        if str(node.get("node_state") or "") == "rejected":
            continue
        blobs.append(" ".join(str(node.get(k) or "") for k in text_keys))
    return [b for b in blobs if b.strip()]


def verify_paper(data: dict[str, Any], paper: dict[str, Any], evidences: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Non-compensatory gate: any failed dimension blocks thread_pass.

    A strong metric cannot rescue a paper that misses the thread's problem or claim.
    """
    claims = _open_nodes(list(data.get("claims") or []), ("text",))
    gaps = _open_nodes(list(data.get("evidence_gaps") or []), ("need", "note"))
    if not claims and not gaps:
        return {
            "title": paper.get("title") or "",
            "verdict": "abstain",
            "label": VERDICT_LABELS["abstain"],
            "dimensions": {
                "problem_gap": _dim("uncertain", "thread has no open gap or claim to audit against"),
                "method_claim": _dim("uncertain", "thread has no open claim"),
                "conclusion_support": _dim("uncertain", "abstained before paper-internal check"),
            },
            "coverage": {"status": "abstain", "reason": "no thread nodes"},
        }
    blob = _paper_blob(paper)
    problem = _best_jaccard(blob, gaps) if gaps else 0.0
    method = _best_jaccard(str(paper.get("method") or "") + " " + blob, claims) if claims else 0.0
    if not gaps:
        problem_dim = _dim("uncertain", "no open gap; problem alignment not audited")
    elif problem >= 0.18:
        problem_dim = _dim("pass", f"overlaps an open gap (j={problem:.2f})")
    elif problem == 0:
        problem_dim = _dim("fail", "paper does not address any open gap")
    else:
        problem_dim = _dim("uncertain", f"partial gap overlap (j={problem:.2f})")
    if not claims:
        method_dim = _dim("uncertain", "no open claim; method compatibility not audited")
    elif method >= 0.18:
        method_dim = _dim("pass", f"compatible with an open claim (j={method:.2f})")
    elif method == 0:
        method_dim = _dim("fail", "method assumptions do not meet any open claim")
    else:
        method_dim = _dim("uncertain", f"partial claim overlap (j={method:.2f})")
    metrics = str(paper.get("metrics") or "")
    support_text = metrics or str(paper.get("summary") or "")
    if _NOT_REPORTED.search(metrics):
        support_dim = _dim("fail", "paper does not report an experiment that supports the conclusion")
    elif _NUMBER.search(support_text):
        support_dim = _dim("pass", "numeric result is present in the paper record")
    else:
        support_dim = _dim("uncertain", "no numeric experiment result in the supplied record")
    dims = {
        "problem_gap": problem_dim,
        "method_claim": method_dim,
        "conclusion_support": support_dim,
    }
    results = [d["result"] for d in dims.values()]
    if "fail" in results:
        verdict = "thread_conflict"
    elif all(r == "pass" for r in results):
        verdict = "thread_pass"
    else:
        verdict = "needs_screen"
    coverage = coverage_check(data, paper, evidences or [])
    return {
        "title": paper.get("title") or "",
        "path": paper.get("path") or "",
        "verdict": verdict,
        "label": VERDICT_LABELS[verdict],
        "dimensions": dims,
        "coverage": coverage,
    }


def coverage_check(data: dict[str, Any], paper: dict[str, Any], evidences: list[dict[str, Any]]) -> dict[str, str]:
    blob = _paper_blob(paper)
    gaps = _open_nodes(list(data.get("evidence_gaps") or []), ("need", "note"))
    gap_j = _best_jaccard(blob, gaps) if gaps else 0.0
    quotes = [str(e.get("quote") or "") for e in evidences if str(e.get("node_state") or "") != "rejected"]
    repeat_j = _best_jaccard(blob, quotes) if quotes else 0.0
    if repeat_j >= 0.45:
        return {"status": "repeats", "reason": "conclusion already covered by an existing evidence quote"}
    if gap_j >= 0.18:
        return {"status": "fills_slot", "reason": "addresses at least one open gap without repeating an evidence quote"}
    return {"status": "no_new_slot", "reason": "does not fill an open evidence slot"}


def verify_papers(
    wiki_root: Path,
    thread_id: str,
    papers: list[dict[str, Any]],
    *,
    propose_updates: bool = False,
    readme_path: str = "",
) -> dict[str, Any]:
    data = ts.load_thread(wiki_root, thread_id)
    evidences = te.list_evidences(wiki_root, thread_id)
    rows = [verify_paper(data, paper, evidences) for paper in papers]
    proposals: list[dict[str, Any]] = []
    if propose_updates:
        claim_id = ""
        for claim in data.get("claims") or []:
            if str(claim.get("node_state") or "") != "rejected":
                claim_id = str(claim.get("id") or "")
                break
        for paper, row in zip(papers, rows):
            if row["verdict"] != "thread_pass" or not claim_id:
                continue
            quote = _first_sentence(str(paper.get("core_idea") or paper.get("contribution") or paper.get("summary") or ""))
            proposals.append(
                propose(
                    wiki_root,
                    thread_id,
                    "add_evidence",
                    {
                        "claim_id": claim_id,
                        "quote": quote,
                        "paper_path": str(paper.get("path") or ""),
                    },
                    source="verify",
                    reason=row["label"],
                )
            )
    report = {
        "thread_id": thread_id,
        "rule": "non_compensatory",
        "counts": {key: sum(1 for row in rows if row["verdict"] == key) for key in VERDICT_LABELS},
        "papers": rows,
        "proposals": [{"proposal_id": p["proposal_id"], "status": p["status"]} for p in proposals],
    }
    if readme_path:
        upsert_readme_section(Path(readme_path), "覆盖检查", render_coverage_markdown(rows))
        report["readme"] = readme_path
    pages = ts.workspace_from_wiki_root(wiki_root) / "content" / "wiki" / "pages"
    written: list[str] = [readme_path] if readme_path else []
    for paper, row in zip(papers, rows):
        rel = str(paper.get("path") or "").strip().strip("/")
        if not rel:
            continue
        page = pages / rel / "README.md"
        if page.is_file():
            upsert_readme_section(page, "覆盖检查", render_coverage_markdown([row]))
            written.append(str(page))
    if written:
        report["readmes"] = written
    ts.append_event(
        wiki_root,
        thread_id,
        {
            "kind": "thread_verify",
            "source": "verify",
            "counts": report["counts"],
            "by": "agent",
        },
    )
    return report


def render_coverage_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "三维同时不失败才记为主线验证通过。任一维度失败即主线冲突，高分指标不能补偿。",
        "",
        "| 论文 | 判定 | 覆盖 | 理由 |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        dims = row.get("dimensions") or {}
        why = "; ".join(
            f"{name}:{dim.get('result')}" for name, dim in dims.items() if isinstance(dim, dict)
        )
        cov = row.get("coverage") if isinstance(row.get("coverage"), dict) else {}
        title = str(row.get("title") or "").replace("|", "/")
        lines.append(
            f"| {title} | {row.get('label')} | {cov.get('status', '')} | {why} |"
        )
    return "\n".join(lines) + "\n"


def upsert_readme_section(path: Path, heading: str, body: str) -> None:
    marker = f"## {heading}"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    block = f"{marker}\n\n{body.rstrip()}\n"
    if marker in existing:
        start = existing.index(marker)
        rest = existing[start + len(marker):]
        nxt = re.search(r"\n## ", rest)
        end = start + len(marker) + (nxt.start() if nxt else len(rest))
        existing = existing[:start] + block + existing[end:]
    else:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing = existing + "\n" + block
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(existing, encoding="utf-8")


def consolidate(wiki_root: Path, thread_id: str) -> dict[str, Any]:
    """Light background pass: unused evidence, stale claims, duplicate gaps.

    Merges stay pending (high risk). Nothing is deleted automatically.
    """
    data = ts.load_thread(wiki_root, thread_id)
    evidences = te.list_evidences(wiki_root, thread_id)
    proposals: list[dict[str, Any]] = []
    gaps_now = _open_nodes(list(data.get("evidence_gaps") or []), ("need", "note"))
    pending = list_proposals(wiki_root, thread_id)
    pending_evidence = {
        str((p.get("payload") or {}).get("id"))
        for p in pending
        if p.get("op") == "mark_pending" and p.get("status") == "pending"
    }
    for ev in evidences:
        state = str(ev.get("node_state") or "candidate")
        if state in ("rejected", "pending") or str(ev.get("evidence_id")) in pending_evidence:
            continue
        quote = str(ev.get("quote") or "")
        if gaps_now and quote and _best_jaccard(quote, gaps_now) == 0:
            proposals.append(
                propose(
                    wiki_root,
                    thread_id,
                    "mark_pending",
                    {"kind": "evidence", "id": ev.get("evidence_id"), "node_state": "pending"},
                    source="consolidate",
                    reason="evidence quote does not address an open gap",
                )
            )
    gaps = [dict(g) for g in (data.get("evidence_gaps") or [])]
    for gap in gaps:
        if not gap.get("id"):
            gap["id"] = _node_id(gaps, "G")
    if any(not g.get("id") for g in (data.get("evidence_gaps") or [])):
        data["evidence_gaps"] = gaps
        ts.save_thread(wiki_root, data)
    for i, left in enumerate(gaps):
        for right in gaps[i + 1:]:
            if str(left.get("node_state") or "") == "rejected" or str(right.get("node_state") or "") == "rejected":
                continue
            jac = ts._jaccard(
                set(ts._tokenize(str(left.get("note") or ""))),
                set(ts._tokenize(str(right.get("note") or ""))),
            )
            if jac >= 0.5:
                pair = (str(left.get("id")), str(right.get("id")))
                already = any(
                    p.get("op") == "merge_gap"
                    and p.get("status") in ("pending", "accepted", "applied")
                    and str((p.get("payload") or {}).get("keep_id")) == pair[0]
                    and str((p.get("payload") or {}).get("drop_id")) == pair[1]
                    for p in list_proposals(wiki_root, thread_id)
                )
                if already:
                    continue
                proposals.append(
                    propose(
                        wiki_root,
                        thread_id,
                        "merge_gap",
                        {"keep_id": left.get("id"), "drop_id": right.get("id")},
                        source="consolidate",
                        reason=f"duplicate gap notes (j={jac:.2f})",
                    )
                )
    data = ts.load_thread(wiki_root, thread_id)
    evidences = te.list_evidences(wiki_root, thread_id)
    for claim in data.get("claims") or []:
        if str(claim.get("node_state") or "") != "verified":
            continue
        linked = [ev for ev in evidences if str(ev.get("claim_id")) == str(claim.get("id"))]
        live = [ev for ev in linked if str(ev.get("node_state") or "") != "rejected"]
        refutes = [
            ev
            for ev in live
            if ev.get("stance") == "refutes" or ev.get("support_status") == "refutes"
        ]
        supports = [ev for ev in live if ev.get("stance") == "supports" or ev.get("support_status") == "supports"]
        if live and not (refutes and not supports):
            continue
        already = any(
            p.get("op") == "set_node_state"
            and p.get("status") == "pending"
            and str((p.get("payload") or {}).get("id")) == str(claim.get("id"))
            for p in list_proposals(wiki_root, thread_id)
        )
        if already:
            continue
        reason = "verified claim has no live supporting evidence"
        if refutes and not supports:
            reason = "verified claim is only contradicted by remaining evidence"
        proposals.append(
            propose(
                wiki_root,
                thread_id,
                "set_node_state",
                {"kind": "claim", "id": claim.get("id"), "node_state": "pending"},
                source="consolidate",
                reason=reason,
            )
        )
    return {
        "thread_id": thread_id,
        "proposals": [{"proposal_id": p["proposal_id"], "op": p["op"], "status": p["status"], "risk": p["risk"]} for p in proposals],
    }


def repeated_sequences(events: list[dict[str, Any]], *, n: int = 3, threshold: int = 3) -> list[list[str]]:
    ops = [str(e.get("op")) for e in events if e.get("kind") == "thread_proposal" and e.get("op")]
    counts: dict[tuple[str, ...], int] = {}
    for i in range(0, max(0, len(ops) - n + 1)):
        window = tuple(ops[i:i + n])
        counts[window] = counts.get(window, 0) + 1
    return [list(seq) for seq, count in counts.items() if count >= threshold]


def distill_skills(wiki_root: Path, thread_id: str, *, threshold: int = 3) -> dict[str, Any]:
    events = ts.list_events(wiki_root, thread_id, limit=500)
    sequences = repeated_sequences(events, threshold=threshold)
    existing = set()
    for proposal in list_proposals(wiki_root, thread_id):
        if proposal.get("op") != "distill_skill" or proposal.get("status") not in ("pending", "accepted", "applied"):
            continue
        payload = proposal.get("payload") if isinstance(proposal.get("payload"), dict) else {}
        existing.add(tuple(str(x) for x in (payload.get("sequence") or [])))
    proposals = []
    for seq in sequences:
        if tuple(seq) in existing:
            continue
        proposals.append(
            propose(
                wiki_root,
                thread_id,
                "distill_skill",
                {"sequence": seq},
                source="distill",
                reason=f"sequence repeated >= {threshold}",
            )
        )
    return {
        "thread_id": thread_id,
        "threshold": threshold,
        "sequences": sequences,
        "proposals": [{"proposal_id": p["proposal_id"], "status": p["status"]} for p in proposals],
    }


_GITHUB_REPO = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s#?.]+)", re.I)


def _github_get_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "paper-rec", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def lookup_github_repo(url: str, *, get_json: Any = None) -> dict[str, Any]:
    """Public repo activity. Failure stays unknown; nothing is invented."""
    match = _GITHUB_REPO.search(url or "")
    if not match:
        return {}
    owner, repo = match.group(1), match.group(2)
    fetch = get_json or _github_get_json
    base = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        meta = fetch(base)
        commits = fetch(base + "/commits?per_page=1")
        issues = fetch(base + "/issues?state=open&per_page=5")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
        return {"url": url, "activity": "unknown", "issues_summary": "", "fetch": "failed"}
    if not isinstance(meta, dict):
        return {"url": url, "activity": "unknown", "fetch": "failed"}
    commit_msg = ""
    if isinstance(commits, list) and commits:
        commit_msg = str(((commits[0].get("commit") or {}).get("message") or "")).split("\n", 1)[0]
    titles = []
    if isinstance(issues, list):
        titles = [str(item.get("title") or "") for item in issues if isinstance(item, dict) and not item.get("pull_request")]
    activity = str(meta.get("pushed_at") or "unknown")
    if commit_msg:
        activity = f"{activity} · {commit_msg}"
    return {
        "url": meta.get("html_url") or url,
        "stars": meta.get("stargazers_count"),
        "activity": activity,
        "issues_summary": "; ".join(t for t in titles if t) or "",
        "fetch": "ok",
    }


def build_exp_contract(paper: dict[str, Any]) -> dict[str, Any]:
    """Implementation-contract draft. Missing fields stay missing; nothing is invented."""
    def pick(*keys: str) -> str:
        for key in keys:
            value = paper.get(key)
            if isinstance(value, (str, int, float)) and str(value).strip():
                return str(value).strip()
        return ""

    algorithm = pick("algorithm", "method", "core_idea")
    metrics = pick("metrics")
    data_split = pick("data_split", "dataset", "split")
    hyper = pick("hyperparameters", "hyperparams")
    obligations = {
        "algorithm": algorithm,
        "metrics": metrics,
        "data_split": data_split,
        "hyperparameters": hyper,
    }
    missing = [name for name, value in obligations.items() if not value or _NOT_REPORTED.search(value)]
    github = paper.get("github") or paper.get("repo") or {}
    if isinstance(github, str):
        github = {"url": github}
    if not isinstance(github, dict):
        github = {}
    activity = "unknown"
    if github.get("pushed_at") or github.get("last_commit"):
        activity = str(github.get("pushed_at") or github.get("last_commit"))
    return {
        "title": paper.get("title") or "",
        "obligations": obligations,
        "missing": missing,
        "coverage": {
            "explicit": len(obligations) - len(missing),
            "total": len(obligations),
        },
        "github": {
            "url": github.get("url") or github.get("html_url") or "",
            "stars": github.get("stars"),
            "activity": activity,
            "issues_summary": github.get("issues_summary") or "",
        },
        "note": "Scaffold only. A runnable tree is not a faithful reproduction.",
    }


def render_exp_contract(contract: dict[str, Any]) -> str:
    obs = contract.get("obligations") or {}
    gh = contract.get("github") or {}
    lines = [
        f"# Implementation contract — {contract.get('title') or 'untitled'}",
        "",
        contract.get("note") or "",
        "",
        "## Explicit obligations",
        "",
    ]
    for key in ("algorithm", "metrics", "data_split", "hyperparameters"):
        value = obs.get(key) or ""
        if not value:
            lines.append(f"- **{key}**: missing in the paper record")
        else:
            lines.append(f"- **{key}**: {value}")
    lines.extend(
        [
            "",
            "## Missing details",
            "",
        ]
    )
    missing = contract.get("missing") or []
    if missing:
        lines.extend(f"- {name}" for name in missing)
    else:
        lines.append("- none of the tracked obligation fields were empty")
    lines.extend(
        [
            "",
            "## Repository evidence",
            "",
            f"- url: {gh.get('url') or 'not provided'}",
            f"- stars: {gh.get('stars') if gh.get('stars') is not None else 'unknown'}",
            f"- activity: {gh.get('activity') or 'unknown'}",
            f"- issues: {gh.get('issues_summary') or 'not provided'}",
            "",
        ]
    )
    return "\n".join(lines)


def write_exp_contract(
    paper: dict[str, Any],
    out_dir: Path,
    *,
    generate: bool = False,
    wiki_root: Path | None = None,
    thread_id: str = "",
    fetch_github: bool = True,
    github_get: Any = None,
) -> dict[str, Any]:
    paper = dict(paper)
    github = paper.get("github") or paper.get("repo") or {}
    url = github if isinstance(github, str) else (github.get("url") or github.get("html_url") or "")
    if fetch_github and url:
        live = lookup_github_repo(str(url), get_json=github_get)
        if isinstance(github, dict):
            merged = {**live, **{k: v for k, v in github.items() if v not in (None, "")}}
        else:
            merged = live or {"url": url}
        paper["github"] = merged
    contract = build_exp_contract(paper)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "CONTRACT.md").write_text(render_exp_contract(contract), encoding="utf-8")
    (out_dir / "obligations.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    proposals: list[dict[str, Any]] = []
    if wiki_root is not None and thread_id:
        proposals.append(
            propose(
                wiki_root,
                thread_id,
                "add_experiment",
                {
                    "title": contract.get("title") or "experiment",
                    "note": "Implementation contract draft. Not a reproduction.",
                    "node_state": "candidate",
                },
                source="exp",
                force_pending=True,
            )
        )
        if contract.get("missing"):
            proposals.append(
                propose(
                    wiki_root,
                    thread_id,
                    "add_gap",
                    {
                        "note": "Contract missing: " + ", ".join(contract["missing"]),
                        "need": "implementation detail",
                        "node_state": "candidate",
                    },
                    source="exp",
                    force_pending=True,
                )
            )
    if generate:
        (out_dir / "README.md").write_text(
            "# Experiment scaffold\n\n"
            "This directory lists obligations extracted from the paper. "
            "It is not a reproduction and contains no training code.\n\n"
            "See CONTRACT.md. Fill missing details from the paper, a cited repository, "
            "or an explicit domain convention before any implementation.\n",
            encoding="utf-8",
        )
    return {
        "out_dir": str(out_dir),
        "contract": contract,
        "generate": generate,
        "proposals": [{"proposal_id": p["proposal_id"], "op": p["op"], "status": p["status"]} for p in proposals],
    }


def rerank_with_feedback(
    wiki_root: Path,
    thread_id: str,
    papers: list[dict[str, Any]],
) -> dict[str, Any]:
    data = ts.load_thread(wiki_root, thread_id)
    profile = feedback_profile(wiki_root, thread_id)
    ranked = []
    for paper in papers:
        scored = ts.score_paper_against_thread(
            data,
            title=str(paper.get("title") or ""),
            summary=str(paper.get("summary") or paper.get("abstract") or paper.get("core_idea") or ""),
            tags=list(paper.get("tags") or []),
            keyword=str(paper.get("keyword") or ""),
            feedback_entities=profile["accepted_entities"],
            rejected_terms=profile["rejected_terms"],
        )
        ranked.append({"title": paper.get("title") or "", "path": paper.get("path") or "", **scored})
    ranked.sort(key=lambda row: row["R"], reverse=True)
    return {"thread_id": thread_id, "feedback": profile, "papers": ranked}
