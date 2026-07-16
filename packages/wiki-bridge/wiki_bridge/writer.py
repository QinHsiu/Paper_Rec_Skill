"""Write paper / query pages into content/wiki/pages (Git Markdown)."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from .conventions import (
    PaperRecord,
    paper_relpath,
    paper_wiki_path,
    render_paper_markdown,
    today_iso,
)


def resolve_content_root(wiki_root: Path) -> Path:
    """Accept workspace root, content/, or content/wiki/pages."""
    wiki_root = wiki_root.resolve()
    if wiki_root.name == "pages" and wiki_root.parent.name == "wiki":
        return wiki_root
    if wiki_root.name == "content":
        p = wiki_root / "wiki" / "pages"
        p.mkdir(parents=True, exist_ok=True)
        return p
    if (wiki_root / "apps" / "wiki-api").is_dir() or (wiki_root / "content").exists():
        p = wiki_root / "content" / "wiki" / "pages"
        p.mkdir(parents=True, exist_ok=True)
        return p
    return wiki_root


def mode_to_slash(mode: str) -> str:
    m = (mode or "").strip().lower().replace("/", "")
    if m in ("query_english", "english", "en"):
        return "/query_english"
    if m in ("query_chinese", "chinese", "zh", "cn"):
        return "/query_chinese"
    if m in ("query_other", "other", "adaptive"):
        return "/query_other"
    if m.startswith("query_"):
        return f"/{m}"
    return "/query_other"


def write_paper_page(content_root: Path, record: PaperRecord) -> Path | None:
    content_root = resolve_content_root(content_root)
    if is_blacklisted(content_root, record):
        print(f"  skip deleted: {record.title[:60]}")
        return None
    rel = paper_relpath(record)
    path = content_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_paper_markdown(record), encoding="utf-8")
    return path


def _deleted_json(content_root: Path) -> Path:
    # content/wiki/pages -> content/wiki/deleted.json
    return content_root.parent / "deleted.json"


def is_blacklisted(content_root: Path, record: PaperRecord) -> bool:
    path = _deleted_json(resolve_content_root(content_root))
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    arxiv = (record.arxiv or "").strip().lower()
    title = (record.title or "").strip().lower()
    wiki_path = paper_wiki_path(record).lower()
    for item in data.get("items") or []:
        if arxiv and (item.get("arxiv") or "").strip().lower() == arxiv:
            return True
        if title and (item.get("title") or "").strip().lower() == title:
            return True
        if wiki_path and (item.get("path") or "").strip().lower() == wiki_path:
            return True
        key = (item.get("key") or "").lower()
        if arxiv and key == f"arxiv:{arxiv}":
            return True
        if title and key == f"title:{title}":
            return True
    return False


def write_query_archive(
    content_root: Path,
    query_id: str,
    *,
    mode: str,
    domain: str,
    packs: str,
    original_query: str,
    body_md: str,
) -> Path:
    content_root = resolve_content_root(content_root)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in query_id)[:80]
    path = content_root / "_queries" / f"{safe_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "---",
            f"query_id: {safe_id}",
            f"mode: {mode}",
            f"domain: {domain}",
            f'packs: "{packs}"',
            f"created_at: {today_iso()}",
            f'original_query: "{original_query.replace(chr(34), chr(39))}"',
            "---",
            "",
            f"# Query: {original_query}",
            "",
            f"**Command**: `{mode_to_slash(mode)}`",
            "",
            body_md.strip(),
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return path


def update_keyword_readmes(
    content_root: Path,
    records: list[PaperRecord],
    *,
    mode: str = "",
    query_id: str = "",
    original_query: str = "",
) -> list[Path]:
    """Append /query_* sync info into each keyword directory README.md."""
    content_root = resolve_content_root(content_root)
    by_kw: dict[str, list[PaperRecord]] = defaultdict(list)
    for rec in records:
        by_kw[rec.keyword_str()].append(rec)

    cmd = mode_to_slash(mode)
    day = today_iso()
    qid = query_id or "adhoc"
    oq = (original_query or qid).replace("|", "/")
    written: list[Path] = []

    for kw, recs in by_kw.items():
        path = content_root / kw / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        paper_links = []
        for r in recs:
            rel = paper_wiki_path(r)
            local = "/".join(rel.split("/")[1:]) + "/README.md"
            paper_links.append(
                f"- [{r.title}]({local}) · score {r.score or '—'} · `{cmd}`"
            )

        log_row = f"| {day} | `{cmd}` | `{qid}` | {oq} | {len(recs)} |"

        if path.is_file():
            text = path.read_text(encoding="utf-8")
        else:
            text = (
                f"# {kw}\n\n"
                f"Papers in this directory are synced from Paper_Rec `/query_*` "
                f"via `wiki_bridge`.\n\n"
                f"本目录论文由 Paper_Rec `/query_*` 检索后经 wiki_bridge 同步写入。\n\n"
                f"## Slash 命令日志\n\n"
                f"| Date | Command | Query id | Query | N |\n"
                f"|------|---------|----------|-------|---|\n"
                f"\n## Papers\n\n"
            )

        if "| Date | Command |" in text and log_row not in text:
            text = text.replace(
                "|------|---------|----------|-------|---|\n",
                f"|------|---------|----------|-------|---|\n{log_row}\n",
                1,
            )
        elif "| Date | Command |" not in text:
            text += (
                "\n## Slash 命令日志\n\n"
                "| Date | Command | Query id | Query | N |\n"
                "|------|---------|----------|-------|---|\n"
                f"{log_row}\n"
            )

        if "## Papers" not in text:
            text += "\n## Papers\n\n"
        for link in paper_links:
            title_key = link.split("](")[0]
            if title_key not in text:
                text = re.sub(
                    r"(## Papers\n\n)",
                    rf"\1{link}\n",
                    text,
                    count=1,
                )

        path.write_text(text.rstrip() + "\n", encoding="utf-8")
        written.append(path)

    return written


def load_report_json(path: Path) -> list[PaperRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "papers" in data:
        items = data["papers"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("Report JSON must be a list or {papers: [...]}")
    records = []
    for item in items:
        records.append(
            PaperRecord(**{k: item[k] for k in PaperRecord.__dataclass_fields__ if k in item})
        )
    return records
