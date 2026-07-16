from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import weekly as weekly_svc

router = APIRouter()


class WeeklyPayload(BaseModel):
    meta: dict = Field(default_factory=dict)
    body: str = ""


@router.get("")
def list_weekly():
    """This week's Skill-synced papers (deduped) + optional weekly digests."""
    return weekly_svc.this_week_bundle()


@router.get("/digests")
def list_digests():
    return {"items": weekly_svc.list_weeklies()}


@router.get("/{path:path}")
def get_weekly(path: str):
    try:
        return weekly_svc.get_weekly(path)
    except FileNotFoundError:
        raise HTTPException(404, "weekly not found")


@router.put("/{path:path}")
def put_weekly(path: str, payload: WeeklyPayload):
    try:
        return weekly_svc.save_weekly(path, payload.meta, payload.body)
    except ValueError as e:
        raise HTTPException(400, str(e))
