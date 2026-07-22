"""Deferred research session store: gather now, write_report later."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

_DEFAULT_TTL_SEC = 7 * 24 * 3600


def _store_path(wiki_root: Path) -> Path:
    return Path(wiki_root) / "content" / "_meta" / "research_sessions.json"


def _load(wiki_root: Path) -> dict[str, Any]:
    path = _store_path(wiki_root)
    if not path.is_file():
        return {"sessions": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"sessions": {}}


def _save(wiki_root: Path, data: dict[str, Any]) -> None:
    path = _store_path(wiki_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _purge(data: dict[str, Any], *, now: float | None = None) -> dict[str, Any]:
    now = now or time.time()
    sessions = data.get("sessions") or {}
    keep = {}
    for rid, sess in sessions.items():
        exp = float(sess.get("expires_at") or 0)
        if exp <= 0 or exp > now:
            keep[rid] = sess
    data["sessions"] = keep
    return data


def create_session(
    wiki_root: Path,
    *,
    topic: str,
    context: dict[str, Any] | None = None,
    sources: list[Any] | None = None,
    thread_id: str = "",
    ttl_sec: int = _DEFAULT_TTL_SEC,
) -> dict[str, Any]:
    data = _purge(_load(wiki_root))
    rid = uuid.uuid4().hex[:12]
    sess = {
        "research_id": rid,
        "topic": topic,
        "thread_id": thread_id,
        "created_at": time.time(),
        "expires_at": time.time() + ttl_sec,
        "context": context or {},
        "sources": sources or [],
        "status": "gathered",
    }
    data["sessions"][rid] = sess
    _save(wiki_root, data)
    return {"research_id": rid, "topic": topic, "thread_id": thread_id, "status": "gathered"}


def get_session(wiki_root: Path, research_id: str) -> dict[str, Any] | None:
    data = _purge(_load(wiki_root))
    return data.get("sessions", {}).get(research_id)


def get_sources(wiki_root: Path, research_id: str) -> dict[str, Any]:
    sess = get_session(wiki_root, research_id)
    if not sess:
        return {"ok": False, "error": "unknown_research_id"}
    return {
        "ok": True,
        "research_id": research_id,
        "topic": sess.get("topic"),
        "sources": sess.get("sources") or [],
        "context_keys": list((sess.get("context") or {}).keys()),
    }


def write_report_payload(wiki_root: Path, research_id: str) -> dict[str, Any]:
    """Return payload for paper_draft / related-work — does not invent prose."""
    sess = get_session(wiki_root, research_id)
    if not sess:
        return {"ok": False, "error": "unknown_research_id"}
    data = _purge(_load(wiki_root))
    sess["status"] = "report_ready"
    data["sessions"][research_id] = sess
    _save(wiki_root, data)
    return {
        "ok": True,
        "research_id": research_id,
        "topic": sess.get("topic"),
        "thread_id": sess.get("thread_id"),
        "sources": sess.get("sources") or [],
        "context": sess.get("context") or {},
        "next": [
            "related-work --thread <id>" if sess.get("thread_id") else "create thread then related-work",
            "paper-draft --thread <id>" if sess.get("thread_id") else "paper-draft after thread bind",
            "claim-ledger / number-verify / stats-rigor before latex-export",
        ],
    }
