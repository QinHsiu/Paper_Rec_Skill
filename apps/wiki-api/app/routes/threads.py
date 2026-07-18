"""Research Thread API — Cognitive Thread v2."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import thread_store

router = APIRouter()


class ThreadCreate(BaseModel):
    title: str
    thread_id: str = ""
    hypothesis: str = ""
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    seed_queries: list[str] = Field(default_factory=list)
    seed_terms: list[str] = Field(default_factory=list)
    notes: str = ""


class ThreadPatch(BaseModel):
    title: str | None = None
    status: str | None = None
    hypothesis: str | None = None
    claims: list[dict[str, Any]] | None = None
    open_questions: list[dict[str, Any]] | None = None
    evidence_gaps: list[dict[str, Any]] | None = None
    keywords: list[str] | None = None
    tags: list[str] | None = None
    seed_queries: list[str] | None = None
    seed_terms: list[str] | None = None
    paper_paths: list[str] | None = None
    experiment_ids: list[str] | None = None
    watch: dict[str, Any] | None = None


class PaperLink(BaseModel):
    path: str
    source: str = "api"


class ExpLink(BaseModel):
    experiment_id: str
    source: str = "api"


class DeltaBody(BaseModel):
    mode: str = "auto"
    threshold: float = 0.45
    persist: bool = True


class ClaimAccept(BaseModel):
    claim_id: str
    status: str = "supported"
    reason: str = ""


class ScorePapersBody(BaseModel):
    papers: list[dict[str, Any]] = Field(default_factory=list)


@router.get("")
def list_threads():
    return {"threads": thread_store.list_threads()}


@router.post("")
def create_thread(body: ThreadCreate):
    try:
        data = thread_store.create_thread(body.model_dump())
    except FileExistsError as e:
        raise HTTPException(409, f"thread exists: {e}") from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return data


@router.get("/by-paper/{path:path}")
def by_paper(path: str):
    return {"path": path, "thread_ids": thread_store.threads_for_paper(path)}


@router.get("/by-exp/{exp_id}")
def by_exp(exp_id: str):
    return {"experiment_id": exp_id, "thread_ids": thread_store.threads_for_exp(exp_id)}


@router.get("/{thread_id}")
def get_thread(thread_id: str):
    try:
        return thread_store.get_thread(thread_id)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.patch("/{thread_id}")
def patch_thread(thread_id: str, body: ThreadPatch):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        return thread_store.patch_thread(thread_id, patch)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.get("/{thread_id}/timeline")
def timeline(thread_id: str, limit: int = 100):
    try:
        thread_store.get_thread(thread_id)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None
    return {"thread_id": thread_id, "events": thread_store.timeline(thread_id, limit=limit)}


@router.post("/{thread_id}/papers")
def link_paper(thread_id: str, body: PaperLink):
    try:
        return thread_store.link_paper(thread_id, body.path, source=body.source)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.delete("/{thread_id}/papers/{path:path}")
def unlink_paper(thread_id: str, path: str):
    try:
        return thread_store.unlink_paper(thread_id, path)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.post("/{thread_id}/experiments")
def link_exp(thread_id: str, body: ExpLink):
    try:
        return thread_store.link_exp(thread_id, body.experiment_id, source=body.source)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.post("/{thread_id}/delta")
def run_delta(thread_id: str, body: DeltaBody | None = None):
    body = body or DeltaBody()
    try:
        return thread_store.run_delta(
            thread_id, mode=body.mode, threshold=body.threshold, persist=body.persist
        )
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.get("/{thread_id}/context")
def search_context(thread_id: str):
    try:
        return thread_store.search_context(thread_id)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.post("/{thread_id}/score")
def score_papers(thread_id: str, body: ScorePapersBody):
    try:
        return {"thread_id": thread_id, "results": thread_store.score_papers(thread_id, body.papers)}
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.get("/{thread_id}/claims/suggestions")
def claim_suggestions(thread_id: str):
    try:
        return thread_store.propose_claims(thread_id)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None


@router.post("/{thread_id}/claims/accept")
def claim_accept(thread_id: str, body: ClaimAccept):
    try:
        return thread_store.accept_claim(thread_id, body.claim_id, body.status, body.reason)
    except FileNotFoundError:
        raise HTTPException(404, f"thread not found: {thread_id}") from None
    except KeyError:
        raise HTTPException(404, f"claim not found: {body.claim_id}") from None
