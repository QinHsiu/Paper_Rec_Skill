"""Expose Paper_Rec / Exp agent skill metadata to the SPA."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.services import content_root

router = APIRouter()


def _md_docs(rel_dir: str) -> list[dict]:
    root = content_root.workspace_root()
    skill_dir = root / rel_dir
    files: list[dict] = []
    if skill_dir.is_dir():
        for p in sorted(skill_dir.glob("*.md")):
            files.append({"name": p.name, "path": f"{rel_dir}/{p.name}"})
    return files


@router.get("")
def list_skills():
    return {
        "skills": [
            {
                "id": "paper-rec",
                "name": "paper-rec",
                "commands": ["/query_english", "/query_chinese", "/query_other", "/wiki"],
                "docs": _md_docs("skill"),
            },
            {
                "id": "exp-sandbox",
                "name": "exp-sandbox",
                "commands": [
                    "/exp_analysis",
                    "/exp_analysis train",
                    "/exp_analysis eval",
                    "/exp_training",
                    "/exp_eval",
                    "/exp_loop",
                ],
                "docs": _md_docs("skill-exp"),
            },
            {
                "id": "plot-draw",
                "name": "plot-draw",
                "commands": ["/draw"],
                "docs": _md_docs("skill-draw"),
            },
        ]
    }


@router.get("/paper-rec/readme")
def skill_readme():
    path = content_root.workspace_root() / "skill" / "README.zh-CN.md"
    if not path.is_file():
        path = content_root.workspace_root() / "skill" / "README.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {"markdown": text}


@router.get("/exp-sandbox/readme")
def exp_skill_readme():
    path = content_root.workspace_root() / "skill-exp" / "README.zh-CN.md"
    if not path.is_file():
        path = content_root.workspace_root() / "skill-exp" / "README.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {"markdown": text}


@router.get("/plot-draw/readme")
def draw_skill_readme():
    path = content_root.workspace_root() / "skill-draw" / "README.zh-CN.md"
    if not path.is_file():
        path = content_root.workspace_root() / "skill-draw" / "README.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {"markdown": text}
