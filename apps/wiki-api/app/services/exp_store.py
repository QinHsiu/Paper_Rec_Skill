"""Experiment store helpers — content/exp + wiki pages/_exp mirror."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services import content_root

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    m = _FRONT.match(text)
    if not m:
        return {}, text
    meta: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip().strip("\"'")
    return meta, text[m.end() :]


def list_experiments() -> list[dict[str, Any]]:
    root = content_root.exp_dir()
    items: list[dict[str, Any]] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        card = _card_from_dir(d)
        if card:
            items.append(card)
    return items


def _card_from_dir(d: Path) -> dict[str, Any] | None:
    readme = d / "README.md"
    final = d / "final_report.md"
    meta: dict[str, Any] = {"id": d.name}
    body = ""
    if readme.is_file():
        meta_fm, body = _parse_frontmatter(readme.read_text(encoding="utf-8"))
        meta.update(meta_fm)
    metrics = _load_metrics(d)
    meta.setdefault("title", meta.get("id", d.name))
    meta["path"] = d.name
    meta["has_final"] = final.is_file()
    meta["metrics_summary"] = metrics.get("primary") or metrics.get("summary") or {}
    meta["target_met"] = str(meta.get("target_met", metrics.get("target_met", ""))).lower() in (
        "true",
        "1",
        "yes",
    )
    meta["updated_at"] = _mtime_iso(d)
    meta["preview"] = _first_para(body)[:200]
    meta["paper_refs"] = _split_list(meta.get("paper_refs") or meta.get("papers") or "")
    return meta


def get_experiment(exp_id: str) -> dict[str, Any]:
    d = content_root.exp_dir() / exp_id
    if not d.is_dir():
        raise FileNotFoundError(exp_id)
    card = _card_from_dir(d) or {"id": exp_id, "path": exp_id}
    files = []
    for p in sorted(d.rglob("*")):
        if p.is_file() and not p.name.startswith("."):
            rel = p.relative_to(d).as_posix()
            files.append({"path": rel, "size": p.stat().st_size})
    card["files"] = files
    card["metrics"] = _load_metrics(d)
    card["curves"] = _load_curves(d)
    readme = d / "README.md"
    final = d / "final_report.md"
    card["readme_md"] = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    card["final_md"] = final.read_text(encoding="utf-8") if final.is_file() else ""
    wiki_mirror = content_root.wiki_exp_pages_dir() / exp_id / "README.md"
    card["wiki_path"] = f"_exp/{exp_id}" if wiki_mirror.is_file() else None
    return card


def get_experiment_file(exp_id: str, rel: str) -> dict[str, Any]:
    d = content_root.exp_dir() / exp_id
    path = (d / rel).resolve()
    if not str(path).startswith(str(d.resolve())):
        raise PermissionError("path escape")
    if not path.is_file():
        raise FileNotFoundError(rel)
    text = path.read_text(encoding="utf-8")
    return {"id": exp_id, "path": rel, "markdown": text}


def _load_metrics(d: Path) -> dict[str, Any]:
    for name in ("metrics/summary.json", "metrics.json"):
        p = d / name
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
    return {}


def _load_curves(d: Path) -> dict[str, Any]:
    p = d / "metrics" / "curves.json"
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _mtime_iso(d: Path) -> str:
    ts = d.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _first_para(body: str) -> str:
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("```"):
            return s
    return ""


def _split_list(v: Any) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v]
    s = str(v or "").strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            return [str(x) for x in json.loads(s)]
        except json.JSONDecodeError:
            pass
    return [x.strip() for x in s.split(",") if x.strip()]
