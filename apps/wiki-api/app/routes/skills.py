"""Expose Paper_Rec agent skill metadata to the SPA."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.services import content_root

router = APIRouter()


@router.get("")
def list_skills():
    root = content_root.workspace_root()
    skill_dir = root / "skill"
    files = []
    if skill_dir.is_dir():
        for p in sorted(skill_dir.glob("*.md")):
            files.append({"name": p.name, "path": f"skill/{p.name}"})
    return {
        "skills": [
            {
                "id": "paper-rec",
                "name": "paper-rec",
                "commands": ["/query_english", "/query_chinese", "/query_other", "/wiki"],
                "docs": files,
            }
        ]
    }


@router.get("/paper-rec/readme")
def skill_readme():
    path = content_root.workspace_root() / "skill" / "README.zh-CN.md"
    if not path.is_file():
        path = content_root.workspace_root() / "skill" / "README.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {"markdown": text}
