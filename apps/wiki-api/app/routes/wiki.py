"""Wiki page CRUD — one README.md per paper; deleted blacklist."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services import content_root, deleted_store, graph, oss_upload, search
from app.services import pages_index
from app.services import paths as pathutil
from app.services.parser import dump_page, extract_wikilinks, parse_frontmatter, slugify

router = APIRouter()


class PagePayload(BaseModel):
    path: str | None = None
    meta: dict = Field(default_factory=dict)
    body: str = ""


class MetaPatch(BaseModel):
    rating: str | None = None
    status: str | None = None
    score: str | None = None
    summary: str | None = None


@router.get("/pages")
def list_pages(keyword: str | None = None, status: str | None = None):
    items = pages_index.list_all_papers()
    if keyword:
        k = keyword.lower()
        items = [
            p
            for p in items
            if k
            in f"{p.get('path')} {p.get('title')} {p.get('keyword')} {p.get('summary')} {p.get('tags')}".lower()
        ]
    if status:
        items = [p for p in items if str(p.get("status") or "") == status]
    return {"pages": items, "count": len(items)}


@router.get("/pages/{path:path}")
def get_page(path: str):
    fp = pathutil.resolve_paper_file(path)
    text = fp.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    card = pages_index.page_card(fp)
    return {
        "path": path,
        "meta": meta,
        "body": body,
        "wikilinks": extract_wikilinks(body),
        "summary": card["summary"],
        "added_at": card["added_at"],
        "score": card["score"],
        "rating": card["rating"],
        "file": str(fp.relative_to(content_root.wiki_pages_dir())).replace("\\", "/"),
    }


@router.put("/pages/{path:path}")
def put_page(path: str, payload: PagePayload):
    # honor delete blacklist — do not recreate
    meta_in = dict(payload.meta or {})
    if deleted_store.is_deleted(
        arxiv=str(meta_in.get("arxiv") or ""),
        title=str(meta_in.get("title") or path.split("/")[-1]),
        path=path,
    ):
        raise HTTPException(
            409,
            "paper is in deleted table; remove from deleted.json to restore",
        )
    fp = pathutil.resolve_paper_file(path, create=True)
    fp.parent.mkdir(parents=True, exist_ok=True)
    meta = meta_in
    if "title" not in meta:
        meta["title"] = path.split("/")[-1]
    if not meta.get("added_at"):
        if fp.is_file():
            old_meta, _ = parse_frontmatter(fp.read_text(encoding="utf-8"))
            meta["added_at"] = old_meta.get("added_at") or date.today().isoformat()
        else:
            meta["added_at"] = date.today().isoformat()
    fp.write_text(dump_page(meta, payload.body or ""), encoding="utf-8")
    return get_page(path)


@router.patch("/pages/{path:path}/meta")
def patch_meta(path: str, payload: MetaPatch):
    fp = pathutil.resolve_paper_file(path)
    text = fp.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    data = payload.model_dump(exclude_none=True)
    meta.update(data)
    fp.write_text(dump_page(meta, body), encoding="utf-8")
    return get_page(path)


@router.post("/pages")
def create_page(payload: PagePayload):
    meta = dict(payload.meta or {})
    title = meta.get("title") or "untitled"
    keyword = meta.get("keyword") or "general"
    year = str(meta.get("year") or "unknown")
    meta.setdefault("added_at", date.today().isoformat())
    rel = payload.path or f"{keyword}/{year}/{slugify(str(title))}"
    return put_page(rel, PagePayload(path=rel, meta=meta, body=payload.body or ""))


@router.delete("/pages/{path:path}")
def delete_page(path: str, reason: str = "user"):
    """Remove paper file(s) and append to deleted blacklist."""
    try:
        fp = pathutil.resolve_paper_file(path)
    except HTTPException:
        # still record blacklist entry if path known
        deleted_store.add_deleted(path=path, reason=reason)
        return {"ok": True, "deleted": True, "blacklist": True, "path": path}

    text = fp.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(text)
    entry = deleted_store.add_deleted(
        arxiv=str(meta.get("arxiv") or ""),
        title=str(meta.get("title") or path.split("/")[-1]),
        path=path,
        reason=reason,
    )
    removed = pathutil.remove_paper_files(path)
    return {
        "ok": True,
        "deleted": True,
        "blacklist": entry,
        "removed": [str(p) for p in removed],
    }


@router.get("/deleted")
def list_deleted():
    return {"items": deleted_store.list_deleted()}


@router.delete("/deleted/{key:path}")
def undelete(key: str):
    """Remove an entry from the blacklist (does not restore files)."""
    ok = deleted_store.remove_from_deleted(key)
    if not ok:
        raise HTTPException(404, "not in deleted table")
    return {"ok": True, "key": key}


@router.get("/search")
def wiki_search(q: str = "", limit: int = 50):
    return {"results": search.search_pages(q, limit=limit)}


@router.get("/graph")
def wiki_graph():
    return graph.build_graph()


@router.get("/bibtex")
def wiki_bibtex(paths: str = ""):
    """Export BibTeX for comma-separated wiki paper paths."""
    from app.services import thread_store as ts

    plist = [p.strip() for p in paths.split(",") if p.strip()]
    if not plist:
        raise HTTPException(400, "paths query required")
    return ts.bibtex_for_paths(plist)


@router.get("/entities/{kind}/{name:path}")
def entity_detail(kind: str, name: str):
    allowed = {"keyword", "tag", "team", "company", "venue", "pack"}
    if kind not in allowed:
        raise HTTPException(400, f"kind must be one of {sorted(allowed)}")
    return graph.papers_for_entity(kind, name)


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    return await oss_upload.save_upload(file, prefix="images")
