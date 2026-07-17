from pathlib import Path
import os


def workspace_root() -> Path:
    env = os.environ.get("PAPER_REC_ROOT")
    if env:
        return Path(env).resolve()
    # apps/wiki-api/app/services -> Paper_Rec_Skill
    return Path(__file__).resolve().parents[3]


def content_dir() -> Path:
    return workspace_root() / "content"


def wiki_pages_dir() -> Path:
    p = content_dir() / "wiki" / "pages"
    p.mkdir(parents=True, exist_ok=True)
    return p


def weekly_dir() -> Path:
    p = content_dir() / "weekly"
    p.mkdir(parents=True, exist_ok=True)
    return p


def uploads_dir() -> Path:
    p = content_dir() / "uploads"
    p.mkdir(parents=True, exist_ok=True)
    return p


def exp_dir() -> Path:
    p = content_dir() / "exp"
    p.mkdir(parents=True, exist_ok=True)
    return p


def wiki_exp_pages_dir() -> Path:
    """Wiki mirror for experiments (underscore → skipped by paper scanners)."""
    p = wiki_pages_dir() / "_exp"
    p.mkdir(parents=True, exist_ok=True)
    return p
