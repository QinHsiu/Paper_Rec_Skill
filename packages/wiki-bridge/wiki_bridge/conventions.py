"""Page naming and frontmatter for Paper_Rec Wiki (content/wiki/pages)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path
from typing import Any


STATUS_VALUES = ("todo", "reading", "done", "abandoned")


@dataclass
class PaperRecord:
    title: str
    authors: str = ""
    year: int | str = ""
    venue: str = ""
    arxiv: str = ""
    doi: str = ""
    url: str = ""
    packs: str = ""
    score: str = ""
    status: str = "todo"
    rating: str = ""
    started_at: str = ""
    finished_at: str = ""
    tags: list[str] = field(default_factory=list)
    keyword: str = ""
    query_ref: str = ""
    title_zh: str = ""
    summary: str = ""
    added_at: str = ""
    core_idea: str = ""
    contribution: str = ""
    metrics: str = ""
    strengths: str = ""
    weaknesses: str = ""
    notes: str = ""

    def normalized_status(self) -> str:
        s = (self.status or "todo").strip().lower()
        return s if s in STATUS_VALUES else "todo"

    def year_str(self) -> str:
        if self.year is None or self.year == "":
            return "unknown"
        return str(self.year)[:4]

    def keyword_str(self) -> str:
        if self.keyword:
            return slugify(str(self.keyword), max_len=40)
        if self.tags:
            return slugify(str(self.tags[0]), max_len=40)
        return "general"


def slugify(title: str, max_len: int = 60) -> str:
    text = title.strip().lower()
    text = re.sub(r"[^\w\s\-\u4e00-\u9fff]", "", text, flags=re.UNICODE)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    if not text:
        text = "paper"
    return text[:max_len].rstrip("-")


def paper_relpath(record: PaperRecord) -> str:
    """Relative path: keyword/year/slug/README.md (one editable file per paper)."""
    return f"{record.keyword_str()}/{record.year_str()}/{slugify(record.title)}/README.md"


def paper_wiki_path(record: PaperRecord) -> str:
    """SPA / API page path without README.md."""
    return f"{record.keyword_str()}/{record.year_str()}/{slugify(record.title)}"


def dump_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif value is None:
            lines.append(f'{key}: ""')
        else:
            text = str(value).replace('"', '\\"')
            if "\n" in text or ":" in text:
                lines.append(f'{key}: "{text}"')
            else:
                lines.append(f"{key}: {text}" if text != "" else f'{key}: ""')
    lines.append("---")
    return "\n".join(lines)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, Any] = {}
    list_key = None
    for raw in parts[1].strip().splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if list_key and line.strip().startswith("- "):
            meta.setdefault(list_key, []).append(line.strip()[2:].strip().strip('"'))
            continue
        list_key = None
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val == "[]":
            meta[key] = []
        elif val == "":
            list_key = key
            meta[key] = []
        else:
            meta[key] = val.strip('"')
    body = parts[2].lstrip("\n")
    return meta, body


def record_to_frontmatter(record: PaperRecord) -> dict[str, Any]:
    data = asdict(record)
    # body fields stored in markdown sections, not frontmatter
    for k in (
        "core_idea",
        "contribution",
        "metrics",
        "strengths",
        "weaknesses",
        "notes",
    ):
        data.pop(k, None)
    data["status"] = record.normalized_status()
    data["tags"] = list(record.tags or [])
    data["keyword"] = record.keyword_str()
    data["summary"] = (record.summary or record.core_idea or "").strip()
    data["added_at"] = (record.added_at or today_iso()).strip()
    return data


def render_paper_markdown(record: PaperRecord) -> str:
    fm = dump_frontmatter(record_to_frontmatter(record))
    title = record.title_zh or record.title
    notes_body = record.notes or "\n".join(
        [
            "### Takeaways",
            "",
            "- …",
            "",
            "### Figures / 插图",
            "",
            "<!-- Paste/drag image in Edit, or use Attachments → insert as image -->",
            "<!-- ![](figure1.png) -->",
            "<!-- ![](figure1.png?thumbnail=400) -->",
            "",
            "### Quotes",
            "",
            "> …",
            "",
            "### Open questions",
            "",
            "- …",
        ]
    )
    sections = [
        fm,
        "",
        f"# {record.title}",
        "",
        f"> **Edit**: `/edit/{paper_wiki_path(record)}` · paste/upload images",
        "",
        "## Meta",
        "",
        f"- **Authors**: {record.authors}",
        f"- **Year**: {record.year}",
        f"- **Keyword**: {record.keyword_str()}",
        f"- **Venue / Source**: {record.venue}",
        f"- **Links**: {record.arxiv or record.url or '—'}",
        f"- **Packs / Score**: {record.packs} / {record.score}",
        "",
        "## Reading",
        "",
        f"- **Status**: {record.normalized_status()}",
        f"- **Rating**: {record.rating or '—'}",
        f"- **Started**: {record.started_at or '—'}",
        f"- **Finished**: {record.finished_at or '—'}",
        "",
        "## Core Idea / 核心观点",
        "",
        record.core_idea or "…",
        "",
        "## Contribution / 核心贡献",
        "",
        record.contribution or "…",
        "",
        "## Metrics / 指标",
        "",
        record.metrics or "…",
        "",
        "## Strengths / 强项",
        "",
        record.strengths or "…",
        "",
        "## Weaknesses / 不足之处",
        "",
        record.weaknesses or "…",
        "",
        "## Personal notes / 个人笔记",
        "",
        notes_body,
        "",
    ]
    if record.title_zh:
        sections.insert(3, f"\n> {title}\n")
    return "\n".join(sections)


def today_iso() -> str:
    return date.today().isoformat()
