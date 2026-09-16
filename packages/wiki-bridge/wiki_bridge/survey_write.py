"""Survey / related-work: multi-outline merge + subsection RAG + citation check."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from .evidence_ground import abstract_supports_claim
from .llm_client import llm_meta, resolve_llm

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


def retrieve_for_section(desc: str, papers: list[dict[str, Any]], *, k: int = 5) -> list[tuple[float, dict[str, Any]]]:
    """TF-IDF cosine top-k abstracts for a section description."""
    docs = [p for p in papers or [] if isinstance(p, dict) and (_abstract(p) or _title(p))]
    if not docs:
        return []
    vecs = _tfidf_docs([tokenize(_title(p) + " " + _abstract(p)) for p in docs] + [tokenize(desc)])
    q = vecs[-1]
    ranked = sorted(((_cosine(v, q), p) for v, p in zip(vecs[:-1], docs)), key=lambda x: x[0], reverse=True)
    return [(round(s, 4), p) for s, p in ranked[:k] if s > 0]


def _support_score(claim: str, abstract: str) -> float:
    """Overlap ratio 0..1 of claim tokens found in abstract (stopword-light)."""
    c = [t for t in tokenize(claim) if len(t) > 2]
    if not c:
        return 0.0
    a = set(tokenize(abstract))
    return round(sum(1 for t in c if t in a) / len(c), 4)


def _prose_paragraph(claims: list[dict[str, Any]]) -> list[str]:
    return [(c["claim"] if c["supported"] else c["claim"].rstrip(".") + ". [citation needed]") for c in claims]


def write_subsection(
    section: dict[str, Any],
    papers: list[dict[str, Any]],
    *,
    rag_k: int = 5,
    tau: float = 0.12,
    chat=None,
) -> dict[str, Any]:
    """Draft subsection from TF-IDF top-k papers; every claim carries a support score vs its cited abstract."""
    desc = str(section.get("description") or section.get("title") or "")
    ranked = retrieve_for_section(desc, papers, k=rag_k)
    chosen = [p for _, p in ranked]
    if not chosen:
        keys = set(section.get("paper_keys") or [])
        chosen = [p for p in papers if _title(p) in keys][:rag_k]

    lines = [f"### {section.get('title')}", "", str(section.get("description") or ""), ""]
    cites, cite_map = [], {}
    for i, p in enumerate(chosen, start=1):
        key = f"P{i}"
        cites.append(key)
        cite_map[key] = p
        lines.append(f"- [{key}] **{_title(p)}** ({p.get('year') or 'n.d.'}): {_abstract(p)[:220] or '(no abstract)'}")
    lines.append("")

    claims: list[dict[str, Any]] = []
    llm_prose = None
    if chat is not None and cite_map:
        llm_prose = llm_write_subsection(chat, section, cite_map)
    if llm_prose:
        for sent in re.split(r"(?<=[.!?])\s+", llm_prose):
            keys = re.findall(r"\[(P\d+)\]", sent)
            if not keys:
                continue
            for k in keys:
                p = cite_map.get(k)
                score = _support_score(sent, _abstract(p)) if p else 0.0
                claims.append({"cite": k, "claim": sent.strip(), "support_score": score, "supported": bool(p) and score >= tau, "source": "llm"})
        lines.append(llm_prose)
    else:
        for key, p in cite_map.items():
            claim = f"[{key}] report work on {_title(p).split(':')[0][:80]}, emphasizing themes relevant to {section.get('title')}."
            score = _support_score(claim, _abstract(p))
            claims.append({"cite": key, "claim": claim, "support_score": score, "supported": score >= tau, "source": "heuristic"})
        lines.extend(_prose_paragraph(claims))
    lines.append("")
    cite_checks = [{"cite": c["cite"], "claim": c["claim"], "supported": c["supported"], "overlap_ratio": c["support_score"]} for c in claims]
    return {
        "title": section.get("title"),
        "markdown": "\n".join(lines),
        "paper_n": len(chosen),
        "cite_keys": cites,
        "cite_checks": cite_checks,
        "claims": claims,
        "supported_n": sum(1 for c in claims if c["supported"]),
        "retrieval_scores": [s for s, _ in ranked],
    }


def check_claim_support(sections_meta: list[dict[str, Any]], *, tau: float = 0.12) -> dict[str, Any]:
    unsupported = [
        {"section": m.get("title"), "cite": c.get("cite"), "claim": str(c.get("claim") or "")[:200], "support_score": c.get("support_score")}
        for m in sections_meta or []
        for c in (m.get("claims") or [])
        if not c.get("supported")
    ]
    return {"tau": tau, "unsupported_n": len(unsupported), "unsupported": unsupported}


_OUTLINE_SYSTEM = 'Merge these related-work outlines into one deduplicated outline. Answer ONLY JSON {"sections": [{"title": str, "subsections": [str]}]}.'
_PROSE_SYSTEM = 'Write a 2-4 sentence related-work paragraph. Every sentence MUST cite one of the given keys as [Pk]. Answer ONLY JSON {"prose": str}.'


def llm_merge_outline(chat, chunk_outlines: list[dict[str, Any]], heuristic: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return (outline, rejected). Accept only if every LLM section maps to a chunk section by title Jaccard >= 0.3."""
    chunk_titles = [str(s.get("title") or "") for o in chunk_outlines for s in (o.get("sections") or [])]
    user = "OUTLINES:\n" + "\n".join(f"- {t}" for t in chunk_titles)
    out = chat(_OUTLINE_SYSTEM, user)
    secs = (out or {}).get("sections") if isinstance(out, dict) else None
    if not isinstance(secs, list) or not secs:
        return heuristic, True
    merged = []
    for s in secs:
        title = str((s or {}).get("title") or "").strip()
        if not title or not any(_jaccard_title(title, ct) >= 0.3 for ct in chunk_titles):
            return heuristic, True
        match = next((h for h in heuristic.get("sections") or [] if _jaccard_title(title, str(h.get("title"))) >= 0.3), {})
        merged.append({**match, "title": title, "subsections": [str(x) for x in (s.get("subsections") or [])]})
    return {"sections": merged, "section_n": len(merged)}, False


def llm_write_subsection(chat, section: dict[str, Any], cite_map: dict[str, dict[str, Any]]) -> str | None:
    refs = "\n".join(f"[{k}] {_title(p)}: {_abstract(p)[:300]}" for k, p in cite_map.items())
    out = chat(_PROSE_SYSTEM, f"SECTION: {section.get('title')}\nDESCRIPTION: {section.get('description') or ''}\nREFERENCES:\n{refs}")
    prose = (out or {}).get("prose") if isinstance(out, dict) else None
    return str(prose).strip() if prose else None


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
    use_llm: str = "off",
    tau: float = 0.12,
    transport=None,
) -> dict[str, Any]:
    chat, model, skip = resolve_llm(use_llm, transport=transport)
    raw = draft_outline_chunks(papers, chunk_size=chunk_size)
    merged = merge_outlines(raw)
    outline_rejected = False
    if chat is not None:
        merged, outline_rejected = llm_merge_outline(chat, raw, merged)
    final = edit_final_outline(merged)
    sections_md, meta, all_checks = [], [], []
    for sec in final.get("sections") or []:
        sub = write_subsection(sec, papers, rag_k=rag_k, tau=tau, chat=chat)
        sections_md.append(sub["markdown"])
        meta.append({"title": sub["title"], "paper_n": sub["paper_n"], "cite_keys": sub["cite_keys"], "supported_n": sub["supported_n"], "claims": sub["claims"]})
        all_checks.extend(sub["cite_checks"])
    title = topic.strip() or "Related Work"
    md = f"# {title} (survey draft)\n\n" + "\n".join(sections_md)
    cite_audit = check_survey_citations(md, papers)
    known = {c for m in meta for c in m["cite_keys"]}
    cite_audit["unknown_keys"] = sorted({i["cite"] for i in cite_audit["issues"] if i.get("issue") == "unknown_cite"} | {k for k in re.findall(r"\[(P\d+)\]", md) if k not in known})
    support = check_claim_support(meta, tau=tau)
    cite_audit["unsupported_n"] = support["unsupported_n"]
    cite_audit["unsupported"] = support["unsupported"]
    ok = bool(cite_audit.get("ok", True)) and support["unsupported_n"] == 0 and not cite_audit["unknown_keys"]
    applied = chat is not None
    return {
        "outline_chunks": len(raw),
        "section_n": final.get("section_n"),
        "sections": meta,
        "markdown": md,
        "cite_checks": all_checks,
        "cite_audit": cite_audit,
        "ok": ok,
        "llm": llm_meta(applied, model, skip, outline_rejected=outline_rejected if applied else None),
    }
