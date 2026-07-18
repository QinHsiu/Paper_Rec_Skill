"""Cognitive Thread template pack — export / import / marketplace catalog."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from . import thread_store as ts
from .conventions import slugify


TEMPLATE_MANIFEST = "template.json"


def templates_dir(wiki_root: Path) -> Path:
    d = ts.workspace_from_wiki_root(wiki_root) / "content" / "thread-templates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_id(name: str) -> str:
    return slugify(name, max_len=64) or "template"


def list_templates(wiki_root: Path) -> list[dict[str, Any]]:
    root = templates_dir(wiki_root)
    items: list[dict[str, Any]] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        man = d / TEMPLATE_MANIFEST
        if not man.is_file():
            continue
        try:
            meta = json.loads(man.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {"template_id": d.name, "title": d.name}
        meta.setdefault("template_id", d.name)
        meta["path"] = f"content/thread-templates/{d.name}"
        items.append(meta)
    return items


def export_template(
    wiki_root: Path,
    thread_id: str,
    *,
    template_id: str = "",
    title: str = "",
    description: str = "",
    tags: list[str] | None = None,
    include_drafts: bool = True,
    include_evidences: bool = False,
) -> dict[str, Any]:
    """Snapshot a live thread into content/thread-templates/<id>/ (sanitized)."""
    wiki_root = Path(wiki_root).resolve()
    data = ts.load_thread(wiki_root, thread_id)
    tid = _safe_id(template_id or f"{thread_id}-template")
    out = templates_dir(wiki_root) / tid
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # Sanitize: drop membership paths that are local-only noise; keep structure
    snap = {
        "type": "research_thread_template",
        "thread_id": "",  # filled on import
        "title": title or data.get("title") or thread_id,
        "status": "active",
        "hypothesis": data.get("hypothesis") or "",
        "claims": [
            {
                "id": c.get("id"),
                "text": c.get("text"),
                "status": "open",
                "evidence_ids": [],
            }
            for c in (data.get("claims") or [])
        ],
        "open_questions": list(data.get("open_questions") or []),
        "evidence_gaps": list(data.get("evidence_gaps") or []),
        "keywords": list(data.get("keywords") or []),
        "tags": list(tags if tags is not None else (data.get("tags") or [])),
        "seed_queries": list(data.get("seed_queries") or []),
        "seed_terms": list(data.get("seed_terms") or []),
        "profile_notes": data.get("profile_notes") or "",
        "paper_paths": [],
        "experiment_ids": [],
        "watch": {
            "enabled": False,
            "cadence": (data.get("watch") or {}).get("cadence") or "weekly",
            "sources_hint": (data.get("watch") or {}).get("sources_hint") or ["arxiv"],
            "last_delta_at": None,
        },
    }
    (out / "thread.json").write_text(
        json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if include_evidences:
        src_ev = ts.thread_dir(wiki_root, thread_id) / "evidences.jsonl"
        if src_ev.is_file():
            shutil.copy2(src_ev, out / "evidences.jsonl")

    if include_drafts:
        drafts = ts.thread_dir(wiki_root, thread_id) / "drafts"
        if drafts.is_dir():
            shutil.copytree(drafts, out / "drafts", dirs_exist_ok=True)

    readme = "\n".join(
        [
            f"# Template: {snap['title']}",
            "",
            description or f"Exported from thread `{thread_id}`.",
            "",
            "## Import",
            "",
            "```bash",
            f"python -m wiki_bridge.cli thread-template-import --wiki-root . --template {tid}",
            "```",
            "",
        ]
    )
    (out / "README.md").write_text(readme, encoding="utf-8")

    manifest = {
        "template_id": tid,
        "title": snap["title"],
        "description": description or f"From thread {thread_id}",
        "source_thread": thread_id,
        "tags": snap["tags"],
        "claims_n": len(snap["claims"]),
        "gaps_n": len(snap["evidence_gaps"]),
        "has_drafts": include_drafts and (out / "drafts").is_dir(),
        "has_evidences": include_evidences and (out / "evidences.jsonl").is_file(),
        "version": 1,
    }
    (out / TEMPLATE_MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"template_id": tid, "path": str(out.relative_to(wiki_root)).replace("\\", "/"), "manifest": manifest}


def import_template(
    wiki_root: Path,
    template_id: str,
    *,
    new_thread_id: str = "",
    title: str = "",
) -> dict[str, Any]:
    """Instantiate a template as a new Cognitive Thread."""
    wiki_root = Path(wiki_root).resolve()
    src = templates_dir(wiki_root) / _safe_id(template_id)
    if not (src / "thread.json").is_file():
        raise FileNotFoundError(f"template not found: {template_id}")
    snap = json.loads((src / "thread.json").read_text(encoding="utf-8"))
    title_final = title or str(snap.get("title") or template_id)
    tid = _safe_id(new_thread_id or title_final)
    # create via store
    created = ts.create_thread(
        wiki_root,
        title_final,
        thread_id=tid,
        hypothesis=str(snap.get("hypothesis") or ""),
        keywords=list(snap.get("keywords") or []),
        tags=list(snap.get("tags") or []),
        seed_queries=list(snap.get("seed_queries") or []),
        seed_terms=list(snap.get("seed_terms") or []),
        notes=f"Imported from template `{template_id}`",
    )
    # merge claims / gaps / questions / profile
    data = ts.load_thread(wiki_root, created["thread_id"])
    data["claims"] = list(snap.get("claims") or [])
    data["open_questions"] = list(snap.get("open_questions") or [])
    data["evidence_gaps"] = list(snap.get("evidence_gaps") or [])
    data["profile_notes"] = snap.get("profile_notes") or ""
    if snap.get("watch"):
        data["watch"] = {**(data.get("watch") or {}), **snap["watch"], "enabled": False}
    ts.save_thread(wiki_root, data)

    dest = ts.thread_dir(wiki_root, created["thread_id"])
    if (src / "evidences.jsonl").is_file():
        shutil.copy2(src / "evidences.jsonl", dest / "evidences.jsonl")
    if (src / "drafts").is_dir():
        shutil.copytree(src / "drafts", dest / "drafts", dirs_exist_ok=True)

    ts.append_event(
        wiki_root,
        created["thread_id"],
        {"kind": "template_import", "template_id": template_id, "by": "user"},
    )
    return {
        "thread_id": created["thread_id"],
        "template_id": template_id,
        "title": title_final,
    }


def ensure_builtin_templates(wiki_root: Path) -> list[str]:
    """Seed marketplace with built-ins (skip ids that already exist)."""
    root = templates_dir(wiki_root)
    existing_ids = {e["template_id"] for e in list_templates(wiki_root)}

    builtins = [
        {
            "template_id": "multimodal-alignment",
            "title": "Multimodal LLM Alignment",
            "description": "Preference / RLHF style multimodal alignment research line.",
            "hypothesis": "Unified preference objectives transfer to vision-language models",
            "keywords": ["multimodal", "alignment", "rlhf", "preference"],
            "seed_terms": ["alignment", "multimodal", "rlhf", "dpo", "preference"],
            "seed_queries": ["multimodal LLM preference alignment"],
            "claims": [
                {"id": "C1", "text": "Preference data quality dominates algorithm choice", "status": "open", "evidence_ids": []},
                {"id": "C2", "text": "RLHF-style methods transfer to VLMs", "status": "open", "evidence_ids": []},
            ],
            "evidence_gaps": [
                {"claim_id": "C1", "need": "empirical", "note": "ablation on preference data quality"}
            ],
            "tags": ["builtin", "llm"],
        },
        {
            "template_id": "rag-evaluation",
            "title": "RAG Evaluation & Faithfulness",
            "description": "Grounded generation evaluation research line.",
            "hypothesis": "Citation-level faithfulness correlates with human judgments",
            "keywords": ["rag", "faithfulness", "evaluation", "citation"],
            "seed_terms": ["rag", "faithfulness", "citation", "hallucination"],
            "seed_queries": ["RAG faithfulness evaluation"],
            "claims": [
                {"id": "C1", "text": "Citation-level metrics beat answer-only n-gram scores", "status": "open", "evidence_ids": []},
            ],
            "evidence_gaps": [
                {"claim_id": "C1", "need": "benchmark", "note": "public human-rated faithfulness set"}
            ],
            "tags": ["builtin", "nlp"],
        },
        {
            "template_id": "code-agents",
            "title": "Repository-Level Code Agents",
            "description": "Tool-using agents beyond HumanEval.",
            "hypothesis": "Repo-level context + search tools improve multi-file repair",
            "keywords": ["code", "agent", "swe-bench", "repository"],
            "seed_terms": ["code", "agent", "repository", "swe-bench", "tool"],
            "seed_queries": ["SWE-bench code agent repository"],
            "claims": [
                {"id": "C1", "text": "Repo benchmarks expose failures invisible on HumanEval", "status": "open", "evidence_ids": []},
                {"id": "C2", "text": "Search tools help multi-file bug fixing", "status": "open", "evidence_ids": []},
            ],
            "evidence_gaps": [
                {"claim_id": "C2", "need": "ablation", "note": "search tool vs no-tool on SWE-bench style"}
            ],
            "tags": ["builtin", "se"],
        },
    ]
    created_ids = []
    for b in builtins:
        tid = b["template_id"]
        if tid in existing_ids:
            created_ids.append(tid)
            continue
        d = root / tid
        d.mkdir(parents=True, exist_ok=True)
        thread = {
            "type": "research_thread_template",
            "title": b["title"],
            "hypothesis": b["hypothesis"],
            "claims": b["claims"],
            "open_questions": [],
            "evidence_gaps": b["evidence_gaps"],
            "keywords": b["keywords"],
            "tags": b["tags"],
            "seed_queries": b["seed_queries"],
            "seed_terms": b["seed_terms"],
            "profile_notes": "",
            "paper_paths": [],
            "experiment_ids": [],
            "watch": {"enabled": False, "cadence": "weekly", "sources_hint": ["arxiv"], "last_delta_at": None},
        }
        (d / "thread.json").write_text(json.dumps(thread, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "README.md").write_text(f"# {b['title']}\n\n{b['description']}\n", encoding="utf-8")
        man = {
            "template_id": tid,
            "title": b["title"],
            "description": b["description"],
            "source_thread": None,
            "tags": b["tags"],
            "claims_n": len(b["claims"]),
            "gaps_n": len(b["evidence_gaps"]),
            "has_drafts": False,
            "has_evidences": False,
            "version": 1,
            "builtin": True,
        }
        (d / TEMPLATE_MANIFEST).write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created_ids.append(tid)
    return created_ids
