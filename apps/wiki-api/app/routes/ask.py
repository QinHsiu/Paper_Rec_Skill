"""Ask endpoint — lightweight Q&A over local wiki search (no external LLM required)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import search

router = APIRouter()


class AskBody(BaseModel):
    question: str
    limit: int = 8


@router.post("")
def ask(body: AskBody):
    hits = search.search_pages(body.question, limit=body.limit)
    answer = (
        "基于本地 Wiki 检索到以下相关页面，请打开阅读笔记继续追问："
        if hits
        else "本地 Wiki 暂无匹配结果。可先用 Paper_Rec Skill 检索论文并写入 Wiki。"
    )
    return {"answer": answer, "hits": hits}
