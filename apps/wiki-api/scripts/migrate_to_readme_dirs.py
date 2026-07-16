"""Migrate legacy keyword/year/slug.md → keyword/year/slug/README.md."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES = ROOT / "content" / "wiki" / "pages"


def main() -> int:
    if not PAGES.is_dir():
        print("no pages dir")
        return 1
    moved = 0
    for path in sorted(PAGES.rglob("*.md")):
        parts = path.relative_to(PAGES).parts
        name = path.name.lower()
        if name == "readme.md":
            continue
        if any(p.startswith("_") for p in parts):
            continue
        # legacy flat paper: keyword/year/slug.md (len>=3)
        if len(parts) < 3:
            continue
        dest_dir = path.parent / path.stem
        dest = dest_dir / "README.md"
        if dest.is_file():
            print(f"skip exists {dest}")
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
        print(f"moved {path.relative_to(PAGES)} -> {dest.relative_to(PAGES)}")
        moved += 1
    print(f"done moved={moved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
