"""Experiment API — list/read content/exp and wiki _exp mirrors."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import exp_store

router = APIRouter()


@router.get("")
def list_experiments():
    return {"experiments": exp_store.list_experiments()}


@router.get("/{exp_id}")
def get_experiment(exp_id: str):
    try:
        return exp_store.get_experiment(exp_id)
    except FileNotFoundError:
        raise HTTPException(404, f"experiment not found: {exp_id}") from None


@router.get("/{exp_id}/asset/{rel:path}")
def get_experiment_asset(exp_id: str, rel: str):
    """Serve binary artifacts (figures/*.png) for the experiment UI / wiki markdown."""
    try:
        path = exp_store.resolve_experiment_asset(exp_id, rel)
    except FileNotFoundError:
        raise HTTPException(404, f"asset not found: {rel}") from None
    except PermissionError:
        raise HTTPException(400, "invalid path") from None
    return FileResponse(path)


@router.get("/{exp_id}/file/{rel:path}")
def get_experiment_file(exp_id: str, rel: str):
    try:
        return exp_store.get_experiment_file(exp_id, rel)
    except FileNotFoundError:
        raise HTTPException(404, f"file not found: {rel}") from None
    except PermissionError:
        raise HTTPException(400, "invalid path") from None
    except UnicodeDecodeError:
        raise HTTPException(400, "not a text file; use /asset/ for binaries") from None
