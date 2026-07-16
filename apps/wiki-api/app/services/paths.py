"""Resolve paper paths: keyword/year/slug/README.md (one file per paper)."""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.services import content_root


def wiki_root() -> Path:
    return content_root.wiki_pages_dir()


def is_skipped_md(path: Path, root: Path) -> bool:
    """Skip catalog / keyword logs / meta — not individual paper records."""
    parts = path.relative_to(root).parts
    name = path.name.lower()
    if any(p.startswith("_") for p in parts):
        return True
    if name.startswith("_"):
        return True
    # content/wiki/pages/README.md
    if len(parts) == 1 and name == "readme.md":
        return True
    # content/wiki/pages/<keyword>/README.md  (query log, not a paper)
    if len(parts) == 2 and name == "readme.md":
        return True
    return False


def is_paper_md(path: Path, root: Path) -> bool:
    if is_skipped_md(path, root):
        return False
    parts = path.relative_to(root).parts
    name = path.name.lower()
    # New layout: keyword/year/slug/README.md
    if name == "readme.md" and len(parts) >= 4:
        return True
    # Legacy flat: keyword/year/slug.md
    if name != "readme.md" and name.endswith(".md") and len(parts) >= 3:
        return True
    return False


def file_to_page_path(path: Path, root: Path | None = None) -> str:
    root = root or wiki_root()
    rel = path.relative_to(root)
    if path.name.lower() == "readme.md":
        return rel.parent.as_posix()
    return rel.as_posix()[:-3] if rel.as_posix().endswith(".md") else rel.as_posix()


def resolve_paper_file(rel: str, *, create: bool = False) -> Path:
    """Map API path keyword/year/slug → README.md file (or legacy .md)."""
    root = wiki_root()
    rel = (rel or "").replace("\\", "/").strip("/")
    if not rel or ".." in rel.split("/"):
        raise HTTPException(400, "invalid path")
    readme = (root / rel / "README.md").resolve()
    flat = (root / f"{rel}.md").resolve()
    root_res = root.resolve()
    if not str(readme).startswith(str(root_res)) or not str(flat).startswith(str(root_res)):
        raise HTTPException(400, "path escape")
    if readme.is_file():
        return readme
    if flat.is_file():
        return flat
    if create:
        readme.parent.mkdir(parents=True, exist_ok=True)
        return readme
    raise HTTPException(404, f"page not found: {rel}")


def remove_paper_files(rel: str) -> list[Path]:
    """Delete paper README dir or legacy flat file. Returns removed paths."""
    root = wiki_root()
    rel = rel.replace("\\", "/").strip("/")
    removed: list[Path] = []
    readme = root / rel / "README.md"
    flat = root / f"{rel}.md"
    if readme.is_file():
        readme.unlink()
        removed.append(readme)
        # remove empty parents up to year/slug
        parent = readme.parent
        try:
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass
    if flat.is_file():
        flat.unlink()
        removed.append(flat)
    return removed
