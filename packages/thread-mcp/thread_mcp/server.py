"""Paper_Rec Thread Memory MCP — Cognitive Thread tools for any MCP client."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Resolve workspace + wiki-bridge
_HERE = Path(__file__).resolve().parent
_PKG = _HERE.parent
_WORKSPACE = Path(os.environ.get("PAPER_REC_ROOT") or _PKG.parents[1]).resolve()
_BRIDGE = _WORKSPACE / "packages" / "wiki-bridge"
if _BRIDGE.is_dir() and str(_BRIDGE) not in sys.path:
    sys.path.insert(0, str(_BRIDGE))

from wiki_bridge import thread_store as ts  # noqa: E402
from wiki_bridge.thread_delta import (  # noqa: E402
    accept_claim_update,
    propose_claim_updates,
    run_delta,
)


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
        """Get full thread.json state plus recent ledger events."""
        data = ts.load_thread(_root(), thread_id)
        events = ts.list_events(_root(), thread_id, limit=50)
        return json.dumps({"thread": data, "events": events}, ensure_ascii=False, indent=2)

    @mcp.tool()
    def thread_search_context(thread_id: str) -> str:
        """Compact hypothesis/claims/gaps/seeds for Thread-conditioned retrieval."""
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
        }
        return json.dumps(ctx, ensure_ascii=False, indent=2)

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

    def main() -> None:
        mcp.run()

except ImportError:
    mcp = None  # type: ignore

    def main() -> None:
        print(
            "mcp package required: pip install mcp\n"
            "Then: PAPER_REC_ROOT=<workspace> python -m thread_mcp.server",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
