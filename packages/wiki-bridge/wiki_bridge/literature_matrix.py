"""Compact literature matrix rows from paper dicts (PaperPilot-inspired).

Heuristic method/task/metric tags for related-work tables — no LLM required.
"""
from __future__ import annotations

import re
from typing import Any

METHOD_PATTERNS: list[tuple[str, list[str]]] = [
    ("Diffusion / Generative", ["diffusion", "flow matching", "gan", "vae", "generative"]),
    ("Graph / Geometric DL", ["graph neural", "gnn", "geometric", "3d", "point cloud"]),
    ("Reinforcement Learning", ["reinforcement", "rlhf", "policy gradient", "reward model"]),
    ("Language / Foundation Models", ["language model", "llm", "transformer", "foundation model", "bert"]),
    ("Retrieval / RAG", ["retrieval", "rag", "dense retriev", "bm25", "rerank"]),
    ("Vision", ["vision", "image", "cvpr", "object detect", "segmentation"]),
    ("Optimization / Search", ["evolutionary", "bayesian optim", "nas", "hyperparameter"]),
    ("Benchmark / Eval", ["benchmark", "evaluation", "leaderboard", "dataset"]),
]

TASK_HINTS: list[tuple[str, list[str]]] = [
    ("classification", ["classif"]),
    ("generation", ["generat", "synthesis", "sampling"]),
    ("retrieval", ["retriev", "search"]),
    ("detection", ["detect"]),
    ("segmentation", ["segment"]),
    ("prediction", ["predict", "forecast"]),
    ("reasoning", ["reason", "chain-of-thought", "cot"]),
    ("benchmarking", ["benchmark", "leaderboard"]),
]


def infer_method_category(title: str, abstract: str = "") -> str:
    text = f"{title} {abstract}".lower()
    best_score, best = 0, "Other"
    for category, terms in METHOD_PATTERNS:
        score = sum(1 for term in terms if term in text)
        if score > best_score:
            best_score, best = score, category
    return best if best_score else "Other"


def infer_task(title: str, abstract: str = "") -> str:
    text = f"{title} {abstract}".lower()
    for label, terms in TASK_HINTS:
        if any(t in text for t in terms):
            return label
    return "general"


def extract_metric_hints(text: str) -> list[str]:
    hints = re.findall(
        r"(?:\d+(?:\.\d+)?\s*%|[<>]=?\s*\d+(?:\.\d+)?|"
        r"AUC|F1|BLEU|ROUGE|accuracy|precision|recall|perplexity|FID|PSNR)",
        text or "",
        flags=re.I,
    )
    return list(dict.fromkeys(hints))[:8]


def _cite_key(item: dict[str, Any], idx: int) -> str:
    for k in ("citation_key", "cite_key", "bibkey", "key"):
        v = str(item.get(k) or "").strip()
        if v:
            return v
    year = str(item.get("year") or "nodate")[:4]
    title = re.sub(r"[^A-Za-z0-9]+", "", str(item.get("title") or "paper"))[:16] or "paper"
    return f"P{idx}{year}{title[:8]}"


def matrix_row(item: dict[str, Any], *, idx: int = 0) -> dict[str, Any]:
    title = str(item.get("title") or "")
    abstract = str(item.get("abstract") or item.get("summary") or "")
    code = str(item.get("code_url") or item.get("github_url") or "").strip()
    has_ft = bool(item.get("fulltext_path") or item.get("fulltext"))
    label = str(item.get("inclusion_label") or item.get("tier") or "candidate")
    return {
        "citation_key": _cite_key(item, idx),
        "title": title,
        "authors": item.get("authors") or [],
        "year": item.get("year"),
        "venue": item.get("venue") or "",
        "method_category": infer_method_category(title, abstract),
        "task": infer_task(title, abstract),
        "evidence_basis": "fulltext+metadata" if has_ft else "metadata_or_abstract_only",
        "metrics_or_results": extract_metric_hints(abstract),
        "code_url": code or None,
        "pdf_url": item.get("pdf_url") or item.get("url"),
        "inclusion_label": label,
        "doi": item.get("doi"),
        "rrf_score": item.get("rrf_score"),
    }


def build_literature_matrix(items: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [matrix_row(it, idx=i + 1) for i, it in enumerate(items or []) if isinstance(it, dict)]
    return {
        "version": "1.0",
        "count": len(rows),
        "rows": rows,
        "markdown": matrix_to_markdown(rows),
    }


def matrix_to_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Key | Year | Method | Task | Code | Evidence |",
        "|-----|------|--------|------|------|----------|",
    ]
    for r in rows:
        code = "Y" if r.get("code_url") else "—"
        title = (r.get("title") or "")[:48].replace("|", "/")
        lines.append(
            f"| `{r.get('citation_key')}` | {r.get('year') or '—'} | "
            f"{r.get('method_category')} | {r.get('task')} | {code} | "
            f"{r.get('evidence_basis')} |"
        )
        lines.append(f"| ↳ {title} | | | | | |")
    return "\n".join(lines) + ("\n" if rows else "")
