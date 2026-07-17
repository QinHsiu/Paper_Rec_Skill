"""Paper_Rec Wiki API — FastAPI entrypoint."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import ask, auth, exp, skills, weekly, wiki
from app.services import content_root

APP_DIR = Path(__file__).resolve().parent
WORKSPACE = APP_DIR.parents[2]  # Paper_Rec_Skill
os.environ.setdefault("PAPER_REC_ROOT", str(WORKSPACE))

app = FastAPI(title="Paper_Rec Wiki", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(wiki.router, prefix="/api/wiki", tags=["wiki"])
app.include_router(weekly.router, prefix="/api/weekly", tags=["weekly"])
app.include_router(exp.router, prefix="/api/exp", tags=["exp"])
app.include_router(ask.router, prefix="/api/ask", tags=["ask"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "content": str(content_root.wiki_pages_dir()),
        "exp": str(content_root.exp_dir()),
    }


uploads = content_root.uploads_dir()
uploads.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads)), name="uploads")

web_dist = WORKSPACE / "apps" / "wiki-web" / "dist"
if web_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="spa")
