"""arXiv category watch → day-partitioned JSON + watermark → optional wiki ingest.

Uses the official Atom API (same family as citation_verify). Multi-cat lanes are
merged with RRF doc-keys; wiki duplicates skipped via normalize_arxiv_id.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .conventions import PaperRecord, paper_wiki_path, today_iso
from .rrf import normalize_arxiv_id, rrf_fuse
from .writer import resolve_content_root, write_paper_page

_UA = "PaperRecSkill/2.37 (arxiv-watch; research; mailto:local)"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
_ARXIV_API = "https://export.arxiv.org/api/query"
_DEFAULT_CATS = ("cs.IR", "cs.CL", "cs.LG")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_only(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    return s[:10]


def default_state_dir(wiki_root: Path) -> Path:
    wiki_root = Path(wiki_root).resolve()
    # workspace root → content/arxiv_watch; content/ or pages → sibling under content/
    if (wiki_root / "content").is_dir() or (wiki_root / "apps").is_dir():
        return wiki_root / "content" / "arxiv_watch"
    if wiki_root.name == "content":
        return wiki_root / "arxiv_watch"
    if wiki_root.name == "pages" and wiki_root.parent.name == "wiki":
        return wiki_root.parent.parent / "arxiv_watch"
    return wiki_root / "arxiv_watch"


def load_config(path: Path | None) -> dict[str, Any]:
    if not path or not Path(path).is_file():
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_state(state_dir: Path) -> dict[str, Any]:
    path = state_dir / "state.json"
    if not path.is_file():
        return {"last_update_date": "", "cats": [], "updated_at": ""}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"last_update_date": "", "cats": [], "updated_at": ""}
    return data if isinstance(data, dict) else {"last_update_date": "", "cats": [], "updated_at": ""}


def save_state(state_dir: Path, state: dict[str, Any]) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _http_get(url: str, *, timeout: int = 30) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/atom+xml"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def _entry_text(entry: ET.Element, tag: str) -> str:
    el = entry.find(f"atom:{tag}", _ATOM_NS)
    if el is None or el.text is None:
        return ""
    return re.sub(r"\s+", " ", el.text).strip()


def _parse_entry(entry: ET.Element, *, source_cat: str) -> dict[str, Any] | None:
    raw_id = _entry_text(entry, "id")
    m = re.search(r"arxiv\.org/abs/([^/\s]+)", raw_id, re.I)
    if m:
        versioned = m.group(1)
    else:
        m2 = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", raw_id)
        if not m2:
            return None
        versioned = m2.group(1)
    arxiv = normalize_arxiv_id(versioned)
    if not arxiv:
        return None
    title = _entry_text(entry, "title")
    summary = _entry_text(entry, "summary")
    published = _date_only(_entry_text(entry, "published") or _entry_text(entry, "updated"))
    authors = [
        re.sub(r"\s+", " ", (a.findtext("atom:name", "", _ATOM_NS) or "")).strip()
        for a in entry.findall("atom:author", _ATOM_NS)
    ]
    authors = [a for a in authors if a]
    primary = ""
    pc = entry.find("arxiv:primary_category", _ATOM_NS)
    if pc is not None:
        primary = (pc.get("term") or "").strip()
    cats = [
        (c.get("term") or "").strip()
        for c in entry.findall("atom:category", _ATOM_NS)
        if (c.get("term") or "").strip()
    ]
    pdf_link = f"https://arxiv.org/pdf/{arxiv}.pdf"
    for link in entry.findall("atom:link", _ATOM_NS):
        href = link.get("href") or ""
        if link.get("title") == "pdf" or href.rstrip("/").endswith(".pdf"):
            pdf_link = href.replace("http://", "https://")
            break
    return {
        "id": versioned if "v" in versioned else f"{arxiv}",
        "arxiv": arxiv,
        "title": title,
        "published": published,
        "authors": authors,
        "summary": summary,
        "paper_link": pdf_link,
        "abs_url": f"https://arxiv.org/abs/{arxiv}",
        "primary_category": primary or source_cat,
        "categories": cats or ([source_cat] if source_cat else []),
        "source_cat": source_cat,
    }


def parse_atom_feed(raw: bytes, *, source_cat: str = "") -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(raw.decode("utf-8"))
    except (ET.ParseError, UnicodeDecodeError):
        return []
    out: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", _ATOM_NS):
        item = _parse_entry(entry, source_cat=source_cat)
        if item and item.get("title"):
            out.append(item)
    return out


def fetch_cat_page(
    cat: str,
    *,
    start: int = 0,
    max_results: int = 50,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
) -> list[dict[str, Any]]:
    cat = cat.strip()
    if not cat.startswith("cat:"):
        query = f"cat:{cat}"
    else:
        query = cat
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": str(start),
            "max_results": str(max_results),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
    )
    raw = _http_get(f"{_ARXIV_API}?{params}")
    if raw is None:
        return []
    return parse_atom_feed(raw, source_cat=cat.removeprefix("cat:"))


def harvest_categories(
    cats: list[str],
    *,
    last_update_date: str = "",
    max_per_cat: int = 100,
    page_size: int = 50,
    wait_time: float = 3.0,
) -> dict[str, Any]:
    """Fetch papers newer than watermark (published date > last_update_date)."""
    watermark = _date_only(last_update_date)
    lanes: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    newest_seen = watermark

    for i, cat in enumerate(cats):
        cat = cat.strip()
        if not cat:
            continue
        collected: list[dict[str, Any]] = []
        start = 0
        while len(collected) < max_per_cat:
            batch = fetch_cat_page(cat, start=start, max_results=min(page_size, max_per_cat - len(collected)))
            if not batch:
                if start == 0:
                    errors.append(f"{cat}: empty or failed API response")
                break
            stop = False
            for item in batch:
                pub = _date_only(str(item.get("published") or ""))
                if pub and (not newest_seen or pub > newest_seen):
                    newest_seen = pub
                if watermark and pub and pub <= watermark:
                    stop = True
                    break
                collected.append(item)
                if len(collected) >= max_per_cat:
                    break
            if stop or len(batch) < page_size:
                break
            start += page_size
            if wait_time > 0:
                time.sleep(wait_time)
        lanes[cat] = collected
        if i + 1 < len(cats) and wait_time > 0:
            time.sleep(wait_time)

    fused = rrf_fuse(lanes, k=60, top_n=max(1, sum(len(v) for v in lanes.values()) or 1))
    documents = fused.get("documents") or []
    # Prefer chronological within same day for ingest order
    documents.sort(key=lambda d: (_date_only(str(d.get("published") or "")), str(d.get("arxiv") or "")), reverse=True)
    return {
        "lanes": {k: len(v) for k, v in lanes.items()},
        "fused_n": len(documents),
        "newest_seen": newest_seen,
        "watermark": watermark,
        "documents": documents,
        "errors": errors,
        "rrf": {"kept_n": fused.get("kept_n"), "input_n": fused.get("input_n"), "rejected_merges": fused.get("rejected_merges")},
    }


def index_wiki_arxiv_ids(wiki_root: Path) -> dict[str, str]:
    """Map normalized arxiv id → existing wiki path."""
    pages = resolve_content_root(wiki_root)
    out: dict[str, str] = {}
    from .conventions import parse_frontmatter

    for path in pages.rglob("README.md"):
        rel_parts = path.relative_to(pages).parts
        if any(p.startswith("_") for p in rel_parts):
            continue
        if len(rel_parts) < 4:
            continue
        try:
            meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        aid = normalize_arxiv_id(str(meta.get("arxiv") or ""))
        if aid:
            out[aid] = "/".join(rel_parts[:-1])
    return out


def write_day_partitions(state_dir: Path, documents: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Write Metadata/{date}.json and Link/{date}.txt (merge with existing same-day files)."""
    by_day: dict[str, list[dict[str, Any]]] = {}
    for doc in documents:
        day = _date_only(str(doc.get("published") or "")) or today_iso()
        by_day.setdefault(day, []).append(doc)

    meta_dir = state_dir / "Metadata"
    link_dir = state_dir / "Link"
    meta_dir.mkdir(parents=True, exist_ok=True)
    link_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, list[str]] = {"metadata": [], "link": []}

    for day, docs in sorted(by_day.items()):
        meta_path = meta_dir / f"{day}.json"
        existing: list[dict[str, Any]] = []
        if meta_path.is_file():
            try:
                raw = json.loads(meta_path.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    existing = raw
            except json.JSONDecodeError:
                existing = []
        seen = {normalize_arxiv_id(str(x.get("arxiv") or x.get("id") or "")) for x in existing}
        merged = list(existing)
        for d in docs:
            key = normalize_arxiv_id(str(d.get("arxiv") or d.get("id") or ""))
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "id": d.get("id") or key,
                    "arxiv": key,
                    "title": d.get("title") or "",
                    "published": d.get("published") or day,
                    "authors": d.get("authors") or [],
                    "summary": d.get("summary") or d.get("abstract") or "",
                    "paper_link": d.get("paper_link") or f"https://arxiv.org/pdf/{key}.pdf",
                    "abs_url": d.get("abs_url") or f"https://arxiv.org/abs/{key}",
                    "primary_category": d.get("primary_category") or "",
                    "categories": d.get("categories") or [],
                    "source_cat": d.get("source_cat") or "",
                }
            )
        meta_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written["metadata"].append(str(meta_path))

        link_path = link_dir / f"{day}.txt"
        lines = [
            f"{(m.get('paper_link') or '').strip()} {(m.get('title') or '').strip()}"
            for m in merged
            if m.get("paper_link")
        ]
        link_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        written["link"].append(str(link_path))

    return written


def _record_from_doc(doc: dict[str, Any], *, keyword: str) -> PaperRecord:
    authors = doc.get("authors") or []
    if isinstance(authors, list):
        authors_s = ", ".join(str(a) for a in authors)
    else:
        authors_s = str(authors)
    pub = _date_only(str(doc.get("published") or ""))
    year = pub[:4] if pub else ""
    cats = doc.get("categories") or []
    tags = ["arxiv-watch"]
    if doc.get("source_cat"):
        tags.append(str(doc["source_cat"]))
    for c in cats[:3]:
        if c and c not in tags:
            tags.append(str(c))
    arxiv = normalize_arxiv_id(str(doc.get("arxiv") or doc.get("id") or ""))
    kw = keyword or str(doc.get("primary_category") or doc.get("source_cat") or "arxiv-watch")
    return PaperRecord(
        title=str(doc.get("title") or arxiv),
        authors=authors_s,
        year=year,
        venue="arXiv",
        arxiv=arxiv,
        url=str(doc.get("abs_url") or f"https://arxiv.org/abs/{arxiv}"),
        summary=str(doc.get("summary") or doc.get("abstract") or "")[:2000],
        keyword=kw,
        tags=tags,
        status="todo",
        added_at=today_iso(),
    )


def ingest_new_papers(
    wiki_root: Path,
    documents: list[dict[str, Any]],
    *,
    keyword: str = "arxiv-watch",
    fetch_pdf: bool = True,
    time_gap: float = 5.0,
    keep_pdf: bool = True,
) -> list[dict[str, Any]]:
    """Write wiki stubs for novel papers; optionally pdf-fetch → ingest."""
    from .pdf_fetch import fetch_and_ingest

    existing = index_wiki_arxiv_ids(wiki_root)
    results: list[dict[str, Any]] = []
    for i, doc in enumerate(documents):
        aid = normalize_arxiv_id(str(doc.get("arxiv") or doc.get("id") or ""))
        if not aid:
            results.append({"arxiv": "", "status": "skip", "reason": "missing_arxiv"})
            continue
        if aid in existing:
            results.append({"arxiv": aid, "status": "duplicate", "path": existing[aid]})
            continue
        rec = _record_from_doc(doc, keyword=keyword)
        written = write_paper_page(wiki_root, rec)
        if written is None:
            results.append({"arxiv": aid, "status": "blacklisted"})
            continue
        path = paper_wiki_path(rec)
        existing[aid] = path
        row: dict[str, Any] = {"arxiv": aid, "status": "created", "path": path, "readme": str(written)}
        if fetch_pdf:
            if i > 0 and time_gap > 0:
                time.sleep(time_gap)
            try:
                bundle = fetch_and_ingest(wiki_root, path, keep_pdf=keep_pdf)
                row["fetch"] = bundle
                ok = bool((bundle.get("fetch") or {}).get("success"))
                row["status"] = "ingested" if ok else "created_fetch_failed"
            except Exception as exc:  # noqa: BLE001 — surface per-paper failure
                row["fetch"] = {"success": False, "message": str(exc)}
                row["status"] = "created_fetch_failed"
        results.append(row)
    return results


def run_arxiv_watch(
    wiki_root: Path,
    *,
    cats: list[str] | None = None,
    config_path: Path | None = None,
    state_dir: Path | None = None,
    last_update_date: str | None = None,
    max_per_cat: int = 100,
    page_size: int = 50,
    wait_time: float = 3.0,
    time_gap: float = 5.0,
    keyword: str = "arxiv-watch",
    ingest: bool = False,
    fetch_pdf: bool = True,
    dry_run: bool = False,
    keep_pdf: bool = True,
) -> dict[str, Any]:
    """
    One watch cycle: harvest → day JSON → persist watermark → optional wiki+pdf ingest.

    Watermark advances to ``newest_seen`` only when not dry_run and harvest succeeded.
    Papers with published <= last_update_date are excluded (same-day re-run is a no-op
    after watermark catch-up; pass ``last_update_date`` override to backfill).
    """
    wiki_root = Path(wiki_root).resolve()
    cfg = load_config(config_path)
    cats = list(cats or cfg.get("cats") or _DEFAULT_CATS)
    cats = [c.strip() for c in cats if str(c).strip()]
    state_dir = Path(state_dir) if state_dir else default_state_dir(wiki_root)
    state = load_state(state_dir)

    max_per_cat = int(cfg.get("max_per_cat", max_per_cat))
    page_size = int(cfg.get("page_size", page_size))
    wait_time = float(cfg.get("wait_time", wait_time))
    time_gap = float(cfg.get("time_gap", time_gap))
    keyword = str(cfg.get("keyword") or keyword)
    watermark = _date_only(last_update_date if last_update_date is not None else str(state.get("last_update_date") or ""))

    harvest = harvest_categories(
        cats,
        last_update_date=watermark,
        max_per_cat=max_per_cat,
        page_size=page_size,
        wait_time=wait_time if not dry_run else 0.0,
    )
    documents = list(harvest.get("documents") or [])

    # Drop wiki duplicates before writing partitions / ingest
    wiki_ids = index_wiki_arxiv_ids(wiki_root)
    novel: list[dict[str, Any]] = []
    dup_wiki = 0
    for doc in documents:
        aid = normalize_arxiv_id(str(doc.get("arxiv") or doc.get("id") or ""))
        if aid and aid in wiki_ids:
            dup_wiki += 1
            continue
        novel.append(doc)

    written_files: dict[str, list[str]] = {"metadata": [], "link": []}
    if not dry_run and novel:
        written_files = write_day_partitions(state_dir, novel)

    ingest_results: list[dict[str, Any]] = []
    if ingest and not dry_run and novel:
        ingest_results = ingest_new_papers(
            wiki_root,
            novel,
            keyword=keyword,
            fetch_pdf=fetch_pdf,
            time_gap=time_gap,
            keep_pdf=keep_pdf,
        )
        try:
            from .dashboard import write_dashboard
            from .indexer import write_reading_index

            write_reading_index(wiki_root)
            write_dashboard(wiki_root)
        except Exception:  # noqa: BLE001
            pass

    new_watermark = _date_only(str(harvest.get("newest_seen") or watermark))
    if not dry_run and new_watermark and (not watermark or new_watermark > watermark):
        state = {
            "last_update_date": new_watermark,
            "cats": cats,
            "updated_at": _utc_now_iso(),
            "last_run": {
                "fused_n": harvest.get("fused_n"),
                "novel_n": len(novel),
                "dup_wiki": dup_wiki,
            },
        }
        save_state(state_dir, state)
    elif not dry_run:
        # still refresh cats / touch without moving watermark backwards
        state = {
            **state,
            "cats": cats,
            "updated_at": _utc_now_iso(),
            "last_update_date": watermark or state.get("last_update_date") or "",
            "last_run": {
                "fused_n": harvest.get("fused_n"),
                "novel_n": len(novel),
                "dup_wiki": dup_wiki,
            },
        }
        save_state(state_dir, state)

    return {
        "ok": True,
        "dry_run": dry_run,
        "state_dir": str(state_dir),
        "cats": cats,
        "watermark_before": watermark,
        "watermark_after": (load_state(state_dir).get("last_update_date") if not dry_run else watermark),
        "lanes": harvest.get("lanes"),
        "fused_n": harvest.get("fused_n"),
        "novel_n": len(novel),
        "dup_wiki": dup_wiki,
        "errors": harvest.get("errors") or [],
        "rrf": harvest.get("rrf"),
        "written": written_files,
        "ingest": ingest_results if ingest else [],
        "sample": [
            {"arxiv": d.get("arxiv"), "title": d.get("title"), "published": d.get("published")}
            for d in novel[:5]
        ],
    }
