"""Local upload service (OSS-compatible interface; stores under content/uploads)."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.services import content_root


async def save_upload(file: UploadFile, prefix: str = "images") -> dict:
    raw = await file.read()
    ext = Path(file.filename or "bin").suffix.lower() or ".bin"
    name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = content_root.uploads_dir() / prefix
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / name
    dest.write_bytes(raw)
    url = f"/uploads/{prefix}/{name}"
    return {"url": url, "filename": name, "size": len(raw)}
