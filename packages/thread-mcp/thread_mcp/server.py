"""Paper_Rec Thread Memory MCP — Cognitive Thread tools for any MCP client."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _bootstrap_paths() -> Path:
    """Zero-PYTHONPATH: locate workspace + wiki-bridge relative to this package."""
    here = Path(__file__).resolve().parent
    pkg = here.parent  # packages/thread-mcp
    # Prefer env; else packages/thread-mcp -> Paper_Rec_Skill
    workspace = Path(os.environ.get("PAPER_REC_ROOT") or pkg.parents[1]).resolve()
    bridge = workspace / "packages" / "wiki-bridge"
    # also allow sibling install layouts
    if not bridge.is_dir():
        alt = pkg.parent / "wiki-bridge"
        if alt.is_dir():
            bridge = alt
    for p in (str(bridge), str(pkg)):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ.setdefault("PAPER_REC_ROOT", str(workspace))
    return workspace


_WORKSPACE = _bootstrap_paths()

from wiki_bridge import thread_store as ts  # noqa: E402
from wiki_bridge.thread_delta import (  # noqa: E402
    accept_claim_update,
    propose_claim_updates,
    run_delta,
)
from wiki_bridge import thread_evidence as te  # noqa: E402


def _root() -> Path:
    return Path(os.environ.get("PAPER_REC_ROOT") or _WORKSPACE).resolve()


try:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("paper-rec-threads")

    @mcp.tool()
    def thread_list() -> str:
        """List Cognitive Threads (id, title, status, paper/exp counts)."""
        return json.dumps(ts.list_threads(_root()), ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_get(thread_id: str) -> str:
        """Get full thread.json state plus events and evidences."""
        data = ts.load_thread(_root(), thread_id)
        events = ts.list_events(_root(), thread_id, limit=50)
        evidences = te.list_evidences(_root(), thread_id)
        return json.dumps(
            {"thread": data, "events": events, "evidences": evidences},
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    def thread_search_context(thread_id: str) -> str:
        """Compact hypothesis/claims/gaps/seeds/evidences for Thread-conditioned retrieval."""
        data = ts.load_thread(_root(), thread_id)
        ctx = {
            "thread_id": data.get("thread_id"),
            "title": data.get("title"),
            "hypothesis": data.get("hypothesis"),
            "claims": data.get("claims"),
            "open_questions": data.get("open_questions"),
            "evidence_gaps": data.get("evidence_gaps"),
            "seed_queries": data.get("seed_queries"),
            "seed_terms": data.get("seed_terms"),
            "keywords": data.get("keywords"),
            "paper_paths": (data.get("paper_paths") or [])[:20],
            "experiment_ids": data.get("experiment_ids"),
            "evidences": te.list_evidences(_root(), thread_id)[:20],
        }
        return json.dumps(ctx, ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_query_hint(thread_id: str) -> str:
        """Return rewritten query hints from thread seeds/claims/gaps (for external search MCP)."""
        data = ts.load_thread(_root(), thread_id)
        hints = list(data.get("seed_queries") or [])
        for c in data.get("claims") or []:
            if c.get("status") in ("open", "", None):
                hints.append(str(c.get("text") or ""))
        for g in data.get("evidence_gaps") or []:
            hints.append(f"{g.get('need', '')} {g.get('note', '')}".strip())
        return json.dumps(
            {
                "thread_id": thread_id,
                "queries": [h for h in hints if h][:12],
                "seed_terms": data.get("seed_terms") or [],
                "compose_with": "article-mcp or /query_* Skill",
            },
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    def thread_score_papers(thread_id: str, papers_json: str) -> str:
        """Score papers JSON list [{title,summary,tags,keyword,path}] against a thread."""
        papers = json.loads(papers_json)
        if not isinstance(papers, list):
            raise ValueError("papers_json must be a JSON list")
        data = ts.load_thread(_root(), thread_id)
        results = []
        for p in papers:
            scored = ts.score_paper_against_thread(
                data,
                title=str(p.get("title") or ""),
                summary=str(p.get("summary") or ""),
                tags=list(p.get("tags") or []),
                keyword=str(p.get("keyword") or ""),
            )
            results.append({"path": p.get("path"), "title": p.get("title"), **scored})
        return json.dumps(results, ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_link_paper(thread_id: str, path: str) -> str:
        """Accept a wiki paper path into thread membership (gate=accepted)."""
        data = ts.link_paper(_root(), thread_id, path, source="mcp", gate="accepted", by="mcp")
        return json.dumps(data, ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_link_exp(thread_id: str, experiment_id: str) -> str:
        """Accept an experiment id into thread membership."""
        data = ts.link_exp(
            _root(), thread_id, experiment_id, source="mcp", gate="accepted", by="mcp"
        )
        return json.dumps(data, ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_add_evidence(
        thread_id: str,
        claim_id: str,
        quote: str,
        paper_path: str = "",
        stance: str = "supports",
        support_status: str = "",
        confidence: float = 0.6,
        gate: str = "accepted",
    ) -> str:
        """Add quote evidence bound to a claim (Claim–Evidence Map)."""
        rec = te.add_evidence(
            _root(),
            thread_id,
            claim_id=claim_id,
            kind="quote",
            paper_path=paper_path,
            quote=quote,
            stance=stance,
            support_status=support_status,
            confidence=confidence,
            gate=gate,
            by="mcp",
        )
        return json.dumps(rec, ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_graph(thread_id: str) -> str:
        """Claim–Evidence cognitive graph JSON for a thread."""
        from wiki_bridge.thread_graph import build_thread_graph

        return json.dumps(build_thread_graph(_root(), thread_id), ensure_ascii=False, indent=2)

    @mcp.tool()
    def bibtex_export(paths: str = "", thread_id: str = "") -> str:
        """Export BibTeX. paths=comma-separated wiki paths; or pass thread_id for members."""
        from wiki_bridge.bibtex_export import export_bibtex

        plist = [p.strip() for p in paths.split(",") if p.strip()]
        if thread_id:
            data = ts.load_thread(_root(), thread_id)
            plist = list(dict.fromkeys(plist + list(data.get("paper_paths") or [])))
        return json.dumps(export_bibtex(_root(), plist), ensure_ascii=False, indent=2)

    @mcp.tool()
    def related_work(thread_id: str) -> str:
        """Generate Related Work outline markdown under thread drafts/."""
        from wiki_bridge.related_work import build_related_work_outline

        return json.dumps(build_related_work_outline(_root(), thread_id), ensure_ascii=False, indent=2)

    @mcp.tool()
    def section_outline(thread_id: str, section: str = "method") -> str:
        """Generate method/experiments outline (not LaTeX)."""
        from wiki_bridge.writing_assist import build_section_outline

        return json.dumps(
            build_section_outline(_root(), thread_id, section=section),
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    def paper_draft(thread_id: str, venue: str = "generic") -> str:
        """Multi-chapter Markdown draft pack with [Claim:]/[Exp:] provenance (not LaTeX)."""
        from wiki_bridge.paper_draft import build_paper_draft

        out = build_paper_draft(_root(), thread_id, venue=venue)
        slim = {k: v for k, v in out.items() if k != "chapters"}
        slim["chapter_preview"] = {
            name: (out["chapters"].get(name) or "")[:500] for name in ("abstract", "introduction")
        }
        return json.dumps(slim, ensure_ascii=False, indent=2)

    @mcp.tool()
    def evidence_coverage(thread_id: str) -> str:
        """Hypothesis/claim evidence confidence coverage advice."""
        return json.dumps(
            te.hypothesis_evidence_coverage(_root(), thread_id),
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    def citation_expand(paper_path: str, top_k: int = 5) -> str:
        """1-hop citation expand for a wiki paper (S2/Crossref; no auto ingest)."""
        from wiki_bridge.citation_expand import expand_citations

        return json.dumps(
            expand_citations(_root(), paper_path, top_k=top_k),
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    def prerank_papers(query: str, papers_json: str, top_k: int = 30) -> str:
        """BM25+recency pre-rank before LLM fine-rank. papers_json = JSON list."""
        from wiki_bridge.prerank import prerank

        papers = json.loads(papers_json)
        if not isinstance(papers, list):
            raise ValueError("papers_json must be a JSON list")
        return json.dumps(prerank(query, papers, top_k=top_k), ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_delta(thread_id: str, mode: str = "auto") -> str:
        """Run Watch/Delta brief (diff_brief|gap_focus|new_digest|exp_bridge|auto)."""
        result = run_delta(_root(), thread_id, mode=mode, persist=True)
        slim = {k: v for k, v in result.items() if k != "markdown"}
        slim["markdown_preview"] = (result.get("markdown") or "")[:2000]
        return json.dumps(slim, ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_claim_suggest(thread_id: str) -> str:
        """Propose claim status updates (gate=suggested only)."""
        return json.dumps(propose_claim_updates(_root(), thread_id), ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_claim_accept(thread_id: str, claim_id: str, status: str = "supported") -> str:
        """Accept a claim status change (human/agent gate)."""
        data = accept_claim_update(_root(), thread_id, claim_id, status, by="mcp")
        return json.dumps(data, ensure_ascii=False, indent=2)

    @mcp.tool()
    def wiki_list_papers(limit: int = 50) -> str:
        """List local Wiki paper cards (path, title, keyword, status)."""
        pages = _root() / "content" / "wiki" / "pages"
        out = []
        if pages.is_dir():
            for readme in sorted(pages.rglob("README.md")):
                parts = readme.relative_to(pages).parts
                if any(p.startswith("_") for p in parts) or len(parts) < 4:
                    continue
                text = readme.read_text(encoding="utf-8")
                title = parts[-2]
                for line in text.splitlines()[:20]:
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"')
                        break
                out.append({"path": "/".join(parts[:-1]), "title": title})
                if len(out) >= limit:
                    break
        return json.dumps(out, ensure_ascii=False, indent=2)

    @mcp.tool()
    def exp_list() -> str:
        """List local experiments under content/exp."""
        root = _root() / "content" / "exp"
        items = []
        if root.is_dir():
            for d in sorted(root.iterdir()):
                if d.is_dir() and not d.name.startswith("."):
                    items.append({"id": d.name})
        return json.dumps(items, ensure_ascii=False, indent=2)

    @mcp.tool()
    def exp_get_metrics(experiment_id: str) -> str:
        """Read metrics/summary.json or metrics.json for an experiment."""
        d = _root() / "content" / "exp" / experiment_id
        for rel in ("metrics/summary.json", "metrics/metrics.json", "metrics.json"):
            p = d / rel
            if p.is_file():
                return p.read_text(encoding="utf-8")
        return json.dumps({"error": "metrics not found", "id": experiment_id})

    def main() -> None:
        mcp.run()

except ImportError:
    mcp = None  # type: ignore

    def main() -> None:
        print(
            "mcp package required: pip install 'mcp>=1.0'\n"
            "Then: set PAPER_REC_ROOT=<workspace> && python -m thread_mcp.server\n"
            "PYTHONPATH is optional — server auto-adds wiki-bridge.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
