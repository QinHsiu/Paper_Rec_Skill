"""Auth middleware stubs — optional token gate for write APIs."""
from __future__ import annotations

import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter()

DEV_TOKEN = os.environ.get("PAPER_REC_TOKEN", "dev-token")


class LoginBody(BaseModel):
    username: str
    password: str = ""


@router.post("/login")
def login(body: LoginBody):
    # Dev auth: any username with shared token
    return {
        "token": DEV_TOKEN,
        "user": {"name": body.username or "reader", "role": "editor"},
    }


@router.get("/me")
def me(authorization: str | None = Header(default=None)):
    if not authorization:
        return {"user": None, "anonymous": True}
    token = authorization.replace("Bearer", "").strip()
    if token != DEV_TOKEN:
        raise HTTPException(401, "invalid token")
    return {"user": {"name": "editor", "role": "editor"}, "anonymous": False}
