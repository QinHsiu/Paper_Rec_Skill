"""Survey / related-work: multi-outline merge + subsection RAG + citation check."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from .evidence_ground import abstract_supports_claim

_TOKEN = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]{3,}")
_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "been", "will", "can", "may", "not", "but", "also", "into",
    "using", "based", "paper", "method", "approach", "model", "models",
}


def _title(p: dict[str, Any]) -> str:
    return str(p.get("title") or p.get("paper_path") or "untitled")


def _abstract(p: dict[str, Any]) -> str:
    return str(p.get("abstract") or p.get("summary") or p.get("quote") or "")[:800]


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "") if t.lower() not in _STOP]


def _tfidf_docs(docs: list[list[str]]) -> list[Counter[str]]:
    df: Counter[str] = Counter()
    for toks in docs:
        df.update(set(toks))
    n = max(1, len(docs))
    out = []
    for toks in docs:
        tf = Counter(toks)
        w: Counter[str] = Counter()
        for t, c in tf.items():
            w[t] = (1 + math.log(1 + c)) * math.log(1 + n / (1 + df[t]))
        out.append(w)
    return out


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return dot / (na * nb)


def cluster_papers(papers: list[dict[str, Any]], *, k: int = 4) -> list[list[dict[str, Any]]]:
    """Greedy TF-IDF clustering into up to k topical groups."""
    valid = [p for p in papers or [] if isinstance(p, dict)]
    if not valid:
        return []
    docs = [tokenize(f"{_title(p)} {_abstract(p)}") for p in valid]
    vecs = _tfidf_docs(docs)
    # seed centroids: pick diverse
    seeds = [0]
    while len(seeds) < min(k, len(valid)):
        best_i, best_score = 0, -1.0
        for i in range(len(valid)):
            if i in seeds:
                continue
            score = min(_cosine(vecs[i], vecs[s]) for s in seeds)
            # maximize distance = minimize similarity
            dist = 1.0 - score
            if dist > best_score:
                best_score, best_i = dist, i
        seeds.append(best_i)
    clusters: list[list[dict[str, Any]]] = [[] for _ in seeds]
    for i, p in enumerate(valid):
        sims = [_cosine(vecs[i], vecs[s]) for s in seeds]
        clusters[int(max(range(len(sims)), key=lambda j: sims[j]))].append(p)
    return [c for c in clusters if c]


def _section_label(papers: list[dict[str, Any]]) -> tuple[str, str]:
    toks: Counter[str] = Counter()
    for p in papers:
        toks.update(tokenize(f"{_title(p)} {_abstract(p)}"))
    top = [t for t, _ in toks.most_common(4)]
    if not top:
        return "Methods", "General methods in this batch."
    title = " / ".join(w.title() for w in top[:3])
    desc = f"Theme around {', '.join(top)} ({len(papers)} papers)."
    return title, desc


def draft_outline_from_cluster(cluster: list[dict[str, Any]]) -> dict[str, Any]:
    title, desc = _section_label(cluster)
    # split large clusters into methods vs eval heuristic sub-buckets
    methods, evals, apps = [], [], []
    for p in cluster:
        text = f"{_title(p)} {_abstract(p)}".lower()
        if any(k in text for k in ("benchmark", "dataset", "evaluation", "leaderboard")):
            evals.append(p)
        elif any(k in text for k in ("application", "clinical", "deploy", "industry")):
            apps.append(p)
        else:
            methods.append(p)
    sections = []
    for name, items, dprefix in (
        (title, methods or cluster, desc),
        (f"{title} — Evaluation", evals, f"Evaluation aspects of {title}"),
        (f"{title} — Applications", apps, f"Applications of {title}"),
    ):
        if not items:
            continue
        sections.append(
            {
                "title": name,
                "description": dprefix,
                "paper_keys": [_title(p) for p in items[:12]],
            }
        )
    return {"sections": sections, "paper_n": len(cluster)}


def draft_outline_chunks(papers: list[dict[str, Any]], *, chunk_size: int = 8) -> list[dict[str, Any]]:
    """Multi-candidate outlines: TF-IDF clusters + sliding batches."""
    outlines: list[dict[str, Any]] = []
    for cluster in cluster_papers(papers, k=max(2, min(5, (len(papers) or 1) // 3 or 1))):
        outlines.append(draft_outline_from_cluster(cluster))
    batch: list[dict[str, Any]] = []
    for p in papers or []:
        if not isinstance(p, dict):
            continue
        batch.append(p)
        if len(batch) >= chunk_size:
            outlines.append(draft_outline_from_cluster(batch))
            batch = []
    if batch:
        outlines.append(draft_outline_from_cluster(batch))
    return outlines or [{"sections": [], "paper_n": 0}]


def _jaccard_title(a: str, b: str) -> float:
    ta, tb = set(tokenize(a)), set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def merge_outlines(outlines: list[dict[str, Any]], *, overlap_thresh: float = 0.55) -> dict[str, Any]:
    """Merge section titles; collapse overlapping subsections by Jaccard."""
    merged: list[dict[str, Any]] = []
    for ol in outlines or []:
        for sec in ol.get("sections") or []:
            title = str(sec.get("title") or "").strip()
            if not title:
                continue
            hit = None
            for m in merged:
                if _jaccard_title(title, str(m["title"])) >= overlap_thresh:
                    hit = m
                    break
            if hit is None:
                merged.append(
                    {
                        "title": title,
                        "description": sec.get("description") or "",
                        "paper_keys": list(sec.get("paper_keys") or []),
                    }
                )
            else:
                keys = hit["paper_keys"]
                for pk in sec.get("paper_keys") or []:
                    if pk not in keys:
                        keys.append(pk)
                if len(str(sec.get("description") or "")) > len(str(hit["description"])):
                    hit["description"] = sec.get("description")
    return {"sections": merged, "section_n": len(merged)}


def edit_final_outline(outline: dict[str, Any]) -> dict[str, Any]:
    """Drop empty / near-duplicate sections."""
    seen: set[str] = set()
    kept = []
    for sec in outline.get("sections") or []:
        title = str(sec.get("title") or "")
        norm = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", title.lower())
        if not norm or norm in seen:
            continue
        if not sec.get("paper_keys"):
            continue
        # skip near-dup of kept
        if any(_jaccard_title(title, str(k["title"])) >= 0.7 for k in kept):
            continue
        seen.add(norm)
        kept.append(sec)
    return {"sections": kept, "section_n": len(kept)}


def write_subsection(
    section: dict[str, Any],
    papers: list[dict[str, Any]],
    *,
    rag_k: int = 5,
) -> dict[str, Any]:
    """Draft subsection from top-k papers; each synth claim checked for support."""
    desc = str(section.get("description") or section.get("title") or "")
    ranked = []
    for p in papers or []:
        if not isinstance(p, dict):
            continue
        r = abstract_supports_claim(desc, _abstract(p), min_overlap=2)
        ranked.append((int(r.get("overlap_n") or 0), p))
    ranked.sort(key=lambda x: x[0], reverse=True)
    chosen = [p for _, p in ranked[:rag_k] if _abstract(p) or _title(p)]
    if not chosen:
        keys = set(section.get("paper_keys") or [])
        chosen = [p for p in papers if _title(p) in keys][:rag_k]

    lines = [
        f"### {section.get('title')}",
        "",
        str(section.get("description") or ""),
        "",
    ]
    cites = []
    cite_map: dict[str, dict[str, Any]] = {}
    for i, p in enumerate(chosen, start=1):
        key = f"P{i}"
        cites.append(key)
        cite_map[key] = p
        abs_ = _abstract(p)[:220] or "(no abstract)"
        lines.append(f"- [{key}] **{_title(p)}** ({p.get('year') or 'n.d.'}): {abs_}")
    lines.append("")

    # One grounded claim sentence per paper (must pass support check)
    claim_lines = []
    cite_checks = []
    for key, p in cite_map.items():
        claim = (
            f"[{key}] report work on {_title(p).split(':')[0][:80]}, "
            f"emphasizing themes relevant to {section.get('title')}."
        )
        chk = abstract_supports_claim(claim, _abstract(p), min_overlap=2)
        cite_checks.append({"cite": key, "claim": claim, **chk})
        if chk.get("supported"):
            claim_lines.append(claim)
        else:
            # soften to bibliographic mention only
            claim_lines.append(f"[{key}] ({_title(p)}) is included for topical coverage.")
    lines.extend(claim_lines)
    lines.append("")
    return {
        "title": section.get("title"),
        "markdown": "\n".join(lines),
        "paper_n": len(chosen),
        "cite_keys": cites,
        "cite_checks": cite_checks,
        "supported_n": sum(1 for c in cite_checks if c.get("supported")),
    }


def check_survey_citations(markdown: str, papers: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify bracket cites in prose have abstract support for their sentence."""
    by_key: dict[str, dict[str, Any]] = {}
    for i, p in enumerate(papers or [], start=1):
        if isinstance(p, dict):
            by_key[f"P{i}"] = p
            by_key[_title(p)] = p
    issues = []
    ok_n = 0
    for sent in re.split(r"(?<=[.!?。！？])\s+", markdown or ""):
        keys = re.findall(r"\[(P\d+)\]", sent)
        if not keys:
            continue
        for k in keys:
            p = by_key.get(k)
            if not p:
                issues.append({"sentence": sent[:200], "cite": k, "issue": "unknown_cite"})
                continue
            chk = abstract_supports_claim(sent, _abstract(p), min_overlap=2)
            if chk.get("supported"):
                ok_n += 1
            else:
                issues.append(
                    {
                        "sentence": sent[:200],
                        "cite": k,
                        "issue": "cite_not_supported_by_abstract",
                        "overlap_n": chk.get("overlap_n"),
                    }
                )
    return {
        "ok": len(issues) == 0,
        "supported_sentences": ok_n,
        "issues": issues,
        "issue_n": len(issues),
    }


def build_survey_draft(
    papers: list[dict[str, Any]],
    *,
    chunk_size: int = 8,
    rag_k: int = 5,
    topic: str = "",
) -> dict[str, Any]:
    raw = draft_outline_chunks(papers, chunk_size=chunk_size)
    merged = merge_outlines(raw)
    final = edit_final_outline(merged)
    sections_md = []
    meta = []
    all_checks = []
    for sec in final.get("sections") or []:
        sub = write_subsection(sec, papers, rag_k=rag_k)
        sections_md.append(sub["markdown"])
        meta.append(
            {
                "title": sub["title"],
                "paper_n": sub["paper_n"],
                "cite_keys": sub["cite_keys"],
                "supported_n": sub.get("supported_n"),
            }
        )
        all_checks.extend(sub.get("cite_checks") or [])
    title = topic.strip() or "Related Work"
    md = f"# {title} (survey draft)\n\n" + "\n".join(sections_md)
    cite_audit = check_survey_citations(md, papers)
    return {
        "outline_chunks": len(raw),
        "section_n": final.get("section_n"),
        "sections": meta,
        "markdown": md,
        "cite_checks": all_checks,
        "cite_audit": cite_audit,
        "ok": cite_audit.get("ok", True),
    }
