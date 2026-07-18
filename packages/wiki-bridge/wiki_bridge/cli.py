"""CLI: sync-report / rebuild-index / sync-exp / thread-*."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .conventions import paper_wiki_path
from .dashboard import write_dashboard
from .exp_writer import load_exp_payload, sync_experiment
from .indexer import write_reading_index
from . import thread_store
from .writer import load_report_json, update_keyword_readmes, write_paper_page, write_query_archive


def workspace_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def _split_csv(raw: str) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def cmd_sync_report(args: argparse.Namespace) -> int:
    records = load_report_json(Path(args.report))
    root = Path(args.wiki_root)
    paths = []
    kept = []
    skipped = 0
    for rec in records:
        if not rec.started_at and args.mark_reading:
            from .conventions import today_iso

            rec.status = rec.status or "todo"
            if args.mark_reading:
                rec.status = "reading"
                rec.started_at = today_iso()
        out = write_paper_page(root, rec)
        if out is None:
            skipped += 1
            continue
        paths.append(out)
        kept.append(rec)
    if args.query_id:
        write_query_archive(
            root,
            args.query_id,
            mode=args.mode or "query_other",
            domain=args.domain or "",
            packs=args.packs or "",
            original_query=args.original_query or args.query_id,
            body_md=args.query_body or "See linked paper pages.",
        )
    readmes = update_keyword_readmes(
        root,
        kept,
        mode=args.mode or "query_other",
        query_id=args.query_id or "",
        original_query=args.original_query or args.query_id or "",
    )
    write_reading_index(root)
    write_dashboard(root)
    print(
        f"Wrote {len(paths)} paper README(s); skipped deleted={skipped}; "
        "index + dashboard refreshed."
    )
    for p in paths:
        print(f"  + {p}")
    for p in readmes:
        print(f"  ~ README {p}")

    if args.thread:
        paper_payloads = []
        for rec in kept:
            paper_payloads.append(
                {
                    "path": paper_wiki_path(rec),
                    "title": rec.title,
                    "summary": rec.summary or rec.core_idea,
                    "tags": list(rec.tags or []),
                    "keyword": rec.keyword_str(),
                }
            )
        scored = thread_store.sync_papers_to_thread(
            root,
            args.thread,
            paper_payloads,
            auto_link=bool(args.auto_link),
            threshold=float(args.auto_link_threshold),
            source="sync-report",
        )
        if args.query_id:
            thread_store.append_event(
                root,
                args.thread,
                {
                    "kind": "query",
                    "query_id": args.query_id,
                    "mode": args.mode or "",
                    "text": args.original_query or "",
                    "top_hits": [
                        {"path": s.get("path"), "R": s.get("R"), "gate": s.get("gate")}
                        for s in scored[:10]
                    ],
                },
            )
        # Optional retrieval trajectory from report JSON wrapper
        try:
            raw_report = json.loads(Path(args.report).read_text(encoding="utf-8"))
            if isinstance(raw_report, dict):
                trace = list(raw_report.get("retrieval_trace") or [])
                if trace:
                    thread_store.append_query_trace(root, args.thread, trace, by="sync-report")
                    print(f"  + query_iter x{len(trace)}")
        except (json.JSONDecodeError, OSError):
            pass
        print(f"Thread `{args.thread}` scored {len(scored)} paper(s); auto_link={bool(args.auto_link)}")
        for s in scored[:10]:
            print(f"  R={s['R']:.2f} gate={s['gate']} {s.get('path') or s.get('title')}")
    return 0


def cmd_rebuild_index(args: argparse.Namespace) -> int:
    root = Path(args.wiki_root)
    idx = write_reading_index(root)
    dash = write_dashboard(root)
    print(f"Updated {idx}")
    print(f"Updated {dash}")
    return 0


def cmd_sync_exp(args: argparse.Namespace) -> int:
    payload = load_exp_payload(Path(args.report))
    outs = sync_experiment(Path(args.wiki_root), payload)
    print(f"Synced experiment → {outs['exp_dir']}")
    print(f"Wiki module page → {outs['wiki_page']}")
    if args.thread:
        exp_id = str(payload.get("experiment_id") or payload.get("id") or "")
        thread_store.link_exp(
            Path(args.wiki_root),
            args.thread,
            exp_id,
            source="sync-exp",
            gate="accepted",
            by="sync",
        )
        print(f"Linked experiment `{exp_id}` → thread `{args.thread}`")
    return 0


def cmd_thread_create(args: argparse.Namespace) -> int:
    data = thread_store.create_thread(
        Path(args.wiki_root),
        args.title,
        thread_id=args.id or "",
        hypothesis=args.hypothesis or "",
        keywords=_split_csv(args.keywords or ""),
        tags=_split_csv(args.tags or ""),
        seed_queries=_split_csv(args.seed_queries or ""),
        seed_terms=_split_csv(args.seed_terms or ""),
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_list(args: argparse.Namespace) -> int:
    cards = thread_store.list_threads(Path(args.wiki_root))
    print(json.dumps(cards, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_show(args: argparse.Namespace) -> int:
    root = Path(args.wiki_root)
    data = thread_store.load_thread(root, args.id)
    events = thread_store.list_events(root, args.id, limit=args.events)
    print(json.dumps({"thread": data, "events": events}, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_link_paper(args: argparse.Namespace) -> int:
    data = thread_store.link_paper(
        Path(args.wiki_root),
        args.thread,
        args.path,
        source=args.source or "manual",
        gate="accepted",
        by="user",
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_link_exp(args: argparse.Namespace) -> int:
    data = thread_store.link_exp(
        Path(args.wiki_root),
        args.thread,
        args.exp_id,
        source=args.source or "manual",
        gate="accepted",
        by="user",
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_delta(args: argparse.Namespace) -> int:
    from .thread_delta import run_delta
    from .webhook_notify import notify_delta

    result = run_delta(
        Path(args.wiki_root),
        args.id,
        mode=args.mode or "auto",
        threshold=float(args.threshold),
        persist=not args.dry_run,
    )
    # ensure thread_id for notify
    result.setdefault("thread_id", args.id)
    print(json.dumps({k: v for k, v in result.items() if k != "markdown"}, ensure_ascii=False, indent=2))
    if args.print_md:
        print("\n" + result.get("markdown", ""))
    if getattr(args, "webhook", "") or getattr(args, "notify", False):
        note = notify_delta(result, webhook_url=getattr(args, "webhook", "") or "")
        print(json.dumps({"notify": note}, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_claim(args: argparse.Namespace) -> int:
    from .thread_delta import accept_claim_update, propose_claim_updates

    root = Path(args.wiki_root)
    if args.accept:
        data = accept_claim_update(
            root,
            args.id,
            args.claim_id,
            args.status,
            by="user",
            reason=args.reason or "",
        )
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        out = propose_claim_updates(root, args.id, apply=False)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_evidence_add(args: argparse.Namespace) -> int:
    from .thread_evidence import add_evidence

    rec = add_evidence(
        Path(args.wiki_root),
        args.thread,
        claim_id=args.claim_id,
        kind=args.kind or "quote",
        paper_path=args.path or "",
        quote=args.quote or "",
        exp_id=args.exp_id or None,
        metric_key=args.metric_key or None,
        metric_value=args.metric_value or None,
        stance=args.stance or "supports",
        support_status=getattr(args, "support_status", "") or "",
        confidence=getattr(args, "confidence", None),
        citation_key=getattr(args, "citation_key", "") or "",
        page=getattr(args, "page", None),
        evidence_level=getattr(args, "evidence_level", "") or "",
        gate="suggested" if args.suggested else "accepted",
        by="user",
    )
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_evidence_list(args: argparse.Namespace) -> int:
    from .thread_evidence import list_evidences

    rows = list_evidences(
        Path(args.wiki_root),
        args.thread,
        claim_id=args.claim_id or "",
        gate=args.gate or "",
    )
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_evidence_gate(args: argparse.Namespace) -> int:
    from .thread_evidence import set_evidence_gate

    rec = set_evidence_gate(
        Path(args.wiki_root),
        args.thread,
        args.evidence_id,
        args.gate,
        by="user",
    )
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


def cmd_query_trace(args: argparse.Namespace) -> int:
    """Persist retrieval_trace rounds as query_iter ledger events."""
    root = Path(args.wiki_root)
    if args.json:
        raw = json.loads(Path(args.json).read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            rounds = list(raw.get("retrieval_trace") or raw.get("rounds") or [])
        else:
            rounds = list(raw)
    else:
        rounds = [
            {
                "round": args.round,
                "path_id": args.path_id,
                "queries": [q for q in (args.query or "").split("||") if q.strip()],
                "raw_hits": args.raw_hits,
                "kept": args.kept,
                "notes": args.notes or "",
            }
        ]
    written = thread_store.append_query_trace(root, args.thread, rounds, by="cli")
    print(json.dumps({"thread": args.thread, "events": len(written)}, ensure_ascii=False))
    return 0


def cmd_thread_graph(args: argparse.Namespace) -> int:
    from .thread_graph import build_thread_graph

    print(json.dumps(build_thread_graph(Path(args.wiki_root), args.id), ensure_ascii=False, indent=2))
    return 0


def cmd_pdf_ingest(args: argparse.Namespace) -> int:
    from .pdf_ingest import ingest_pdf

    out = ingest_pdf(
        Path(args.wiki_root),
        Path(args.pdf),
        args.path,
        title=args.title or "",
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_claim_suggest(args: argparse.Namespace) -> int:
    from .pdf_ingest import apply_claim_suggestions, suggest_claims_from_fulltext

    root = Path(args.wiki_root)
    if args.apply and args.thread:
        out = apply_claim_suggestions(
            root,
            args.thread,
            args.path,
            max_claims=args.max,
            also_evidence=not args.no_evidence,
        )
    else:
        out = {"candidates": suggest_claims_from_fulltext(root, args.path, max_claims=args.max)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_bibtex_export(args: argparse.Namespace) -> int:
    from .bibtex_export import export_bibtex

    paths = _split_csv(args.paths) if args.paths else []
    if args.thread:
        data = thread_store.load_thread(Path(args.wiki_root), args.thread)
        paths = list(dict.fromkeys(paths + list(data.get("paper_paths") or [])))
    out = export_bibtex(Path(args.wiki_root), paths)
    if args.out:
        Path(args.out).write_text(out["bibtex"], encoding="utf-8")
        print(f"Wrote {args.out} ({out['count']} entries)")
        for w in out["warnings"]:
            print(f"  ! {w}")
    else:
        print(out["bibtex"])
        if out["warnings"]:
            print("% warnings:", file=sys.stderr)
            for w in out["warnings"]:
                print(f"% {w}", file=sys.stderr)
    return 0


def cmd_related_work(args: argparse.Namespace) -> int:
    from .related_work import build_related_work_outline

    out = build_related_work_outline(Path(args.wiki_root), args.thread)
    print(json.dumps({"path": out["path"], "chars": len(out["markdown"])}, ensure_ascii=False))
    if args.print_md:
        print(out["markdown"])
    return 0


def cmd_section_outline(args: argparse.Namespace) -> int:
    from .writing_assist import build_section_outline

    out = build_section_outline(Path(args.wiki_root), args.thread, section=args.section)
    print(json.dumps({"path": out["path"], "section": out.get("section")}, ensure_ascii=False))
    if args.print_md:
        print(out["markdown"])
    return 0


def cmd_paper_draft(args: argparse.Namespace) -> int:
    from .paper_draft import build_paper_draft

    out = build_paper_draft(Path(args.wiki_root), args.thread, venue=args.venue)
    print(
        json.dumps(
            {
                "dir": out["dir"],
                "venue": out["venue"],
                "paths": out["paths"],
                "bibtex_count": out["bibtex_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_prerank(args: argparse.Namespace) -> int:
    from .prerank import prerank_from_json

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    out = prerank_from_json(
        payload,
        query=args.query,
        top_k=args.top_k,
        use_citations=not args.no_citations,
    )
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "prerank": out["prerank"],
                "input_n": out["input_n"],
                "kept_n": out["kept_n"],
                "top_k": out["top_k"],
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_citation_expand(args: argparse.Namespace) -> int:
    from .citation_expand import expand_citations

    out = expand_citations(
        Path(args.wiki_root),
        args.path,
        top_k=args.top_k,
        persist=not args.no_persist,
    )
    print(
        json.dumps(
            {
                "provider": out.get("provider"),
                "fetched_n": out.get("fetched_n"),
                "top_k": out.get("top_k"),
                "path": out.get("path"),
                "references": out.get("references"),
                "warnings": out.get("warnings"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_evidence_coverage(args: argparse.Namespace) -> int:
    from .thread_evidence import hypothesis_evidence_coverage

    out = hypothesis_evidence_coverage(Path(args.wiki_root), args.thread)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_pdf_fetch(args: argparse.Namespace) -> int:
    from .pdf_fetch import fetch_and_ingest

    out = fetch_and_ingest(Path(args.wiki_root), args.path, keep_pdf=not args.no_keep)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("fetch", {}).get("success") else 1


def cmd_rrf_fuse(args: argparse.Namespace) -> int:
    from .rrf import rrf_fuse_from_payload

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    out = rrf_fuse_from_payload(payload, k=args.k, top_n=args.top_n)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"rrf": out["rrf"], "lane_hits": out["lane_hits"], "kept_n": out["kept_n"], "input_n": out["input_n"]},
            ensure_ascii=False,
        )
    )
    return 0


def cmd_csl_json(args: argparse.Namespace) -> int:
    from .csl_json_export import export_csl_json
    from . import thread_store as ts

    paths = [p.strip() for p in (args.paths or "").split(",") if p.strip()]
    if args.thread:
        data = ts.load_thread(Path(args.wiki_root), args.thread)
        paths = list(dict.fromkeys(paths + list(data.get("paper_paths") or [])))
    out = export_csl_json(Path(args.wiki_root), paths)
    if args.out:
        Path(args.out).write_text(out["csl_json"], encoding="utf-8")
        print(json.dumps({"path": args.out, "count": out["count"], "warnings": out["warnings"]}, ensure_ascii=False))
    else:
        print(out["csl_json"])
    return 0


def cmd_thread_feedback(args: argparse.Namespace) -> int:
    from . import thread_store as ts

    out = ts.record_feedback(
        Path(args.wiki_root),
        args.thread,
        action=args.action,
        path=args.path,
        note=args.note,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_thread_bench(args: argparse.Namespace) -> int:
    from .thread_bench import evaluate_bench, evaluate_case

    if args.bench_root:
        root = Path(args.bench_root)
    else:
        wiki = Path(args.wiki_root).resolve()
        cand = wiki / "benchmarks" / "thread-bench"
        root = cand if cand.is_dir() else Path("benchmarks/thread-bench")
    if args.case:
        out = evaluate_case(root / "cases" / args.case, k=args.k)
    else:
        out = evaluate_bench(root, k=args.k)
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def cmd_notify_webhook(args: argparse.Namespace) -> int:
    from .webhook_notify import build_payload, notify_delta, post_webhook, resolve_webhook_url

    url = resolve_webhook_url(args.webhook)
    if args.dry_run or not url:
        payload = build_payload(
            thread_id=args.thread or "demo",
            mode=args.mode or "test",
            title=args.title or "webhook dry-run",
            candidates=[{"path": "demo/paper", "title": "Demo", "R": 0.8}],
            delta_path="",
            markdown_preview=args.message or "Paper_Rec webhook test",
        )
        print(json.dumps({"dry_run": True, "url": url or None, "payload": payload}, ensure_ascii=False, indent=2))
        return 0 if args.dry_run or not url else 1
    if args.json:
        result = json.loads(Path(args.json).read_text(encoding="utf-8"))
        print(json.dumps(notify_delta(result, webhook_url=url), ensure_ascii=False, indent=2))
        return 0
    payload = build_payload(
        thread_id=args.thread or "manual",
        mode=args.mode or "notify",
        title=args.title or "",
        candidates=[],
        markdown_preview=args.message or "Paper_Rec notify",
    )
    print(json.dumps(post_webhook(url, payload), ensure_ascii=False, indent=2))
    return 0


def cmd_template_list(args: argparse.Namespace) -> int:
    from .thread_templates import ensure_builtin_templates, list_templates

    root = Path(args.wiki_root)
    if args.seed:
        ensure_builtin_templates(root)
    print(json.dumps(list_templates(root), ensure_ascii=False, indent=2))
    return 0


def cmd_template_export(args: argparse.Namespace) -> int:
    from .thread_templates import export_template

    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    out = export_template(
        Path(args.wiki_root),
        args.thread,
        template_id=args.template_id or "",
        title=args.title or "",
        description=args.description or "",
        tags=tags or None,
        include_drafts=not args.no_drafts,
        include_evidences=args.evidences,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_template_import(args: argparse.Namespace) -> int:
    from .thread_templates import ensure_builtin_templates, import_template

    root = Path(args.wiki_root)
    ensure_builtin_templates(root)
    out = import_template(
        root,
        args.template,
        new_thread_id=args.id or "",
        title=args.title or "",
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wiki_bridge", description="Paper_Rec ↔ Wiki Markdown bridge")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sync-report", help="Write papers from JSON report into wiki")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--report", required=True, help="JSON file: list or {papers:[...]}")
    s.add_argument("--query-id", default="")
    s.add_argument("--mode", default="")
    s.add_argument("--domain", default="")
    s.add_argument("--packs", default="")
    s.add_argument("--original-query", default="")
    s.add_argument("--query-body", default="")
    s.add_argument("--mark-reading", action="store_true")
    s.add_argument("--thread", default="", help="Research thread id to score/link papers")
    s.add_argument(
        "--auto-link",
        action="store_true",
        help="Accept papers into thread when R >= threshold (default: score only)",
    )
    s.add_argument("--auto-link-threshold", type=float, default=0.75)
    s.set_defaults(func=cmd_sync_report)

    s = sub.add_parser("rebuild-index", help="Regenerate Reading_Index and Dashboard")
    s.add_argument("--wiki-root", required=True)
    s.set_defaults(func=cmd_rebuild_index)

    s = sub.add_parser(
        "sync-exp",
        help="Write experiment final results (metrics/curves) into content/exp + wiki _exp",
    )
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--report", required=True, help="JSON experiment payload")
    s.add_argument("--thread", default="", help="Link experiment to research thread")
    s.set_defaults(func=cmd_sync_exp)

    s = sub.add_parser("thread-create", help="Create a Cognitive Thread")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--title", required=True)
    s.add_argument("--id", default="", help="thread_id (default: slugify title)")
    s.add_argument("--hypothesis", default="")
    s.add_argument("--keywords", default="", help="comma-separated")
    s.add_argument("--tags", default="", help="comma-separated")
    s.add_argument("--seed-queries", default="", help="comma-separated")
    s.add_argument("--seed-terms", default="", help="comma-separated")
    s.set_defaults(func=cmd_thread_create)

    s = sub.add_parser("thread-list", help="List research threads")
    s.add_argument("--wiki-root", required=True)
    s.set_defaults(func=cmd_thread_list)

    s = sub.add_parser("thread-show", help="Show thread + recent events")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--id", required=True)
    s.add_argument("--events", type=int, default=50)
    s.set_defaults(func=cmd_thread_show)

    s = sub.add_parser("thread-link-paper", help="Accept a paper path into a thread")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--path", required=True, help="wiki path keyword/year/slug")
    s.add_argument("--source", default="manual")
    s.set_defaults(func=cmd_thread_link_paper)

    s = sub.add_parser("thread-link-exp", help="Accept an experiment into a thread")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--exp-id", required=True)
    s.add_argument("--source", default="manual")
    s.set_defaults(func=cmd_thread_link_exp)

    s = sub.add_parser("thread-delta", help="Run Watch/Delta brief for a thread")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--id", required=True)
    s.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "new_digest", "diff_brief", "gap_focus", "exp_bridge"],
    )
    s.add_argument("--threshold", type=float, default=0.45)
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--print-md", action="store_true")
    s.add_argument("--webhook", default="", help="POST Delta summary (or PAPER_REC_WEBHOOK_URL)")
    s.add_argument("--notify", action="store_true", help="notify using PAPER_REC_WEBHOOK_URL")
    s.set_defaults(func=cmd_thread_delta)

    s = sub.add_parser("thread-claim", help="Propose or accept claim status updates")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--id", required=True, help="thread id")
    s.add_argument("--claim-id", default="")
    s.add_argument("--status", default="supported")
    s.add_argument("--accept", action="store_true", help="accept gate (write claim status)")
    s.add_argument("--reason", default="")
    s.set_defaults(func=cmd_thread_claim)

    s = sub.add_parser("thread-evidence-add", help="Add claim evidence (quote/metric)")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--claim-id", required=True)
    s.add_argument("--kind", default="quote", choices=["quote", "metric", "figure", "note"])
    s.add_argument("--path", default="", help="wiki paper path")
    s.add_argument("--quote", default="")
    s.add_argument("--exp-id", default="")
    s.add_argument("--metric-key", default="")
    s.add_argument("--metric-value", default="")
    s.add_argument("--stance", default="supports", choices=["supports", "refutes", "related"])
    s.add_argument(
        "--support-status",
        default="",
        choices=["", "supports", "refutes", "related", "insufficient"],
    )
    s.add_argument("--confidence", type=float, default=None)
    s.add_argument("--citation-key", default="")
    s.add_argument("--page", type=int, default=None)
    s.add_argument("--evidence-level", default="", help="optional anecdote|study|meta or CEBM-lite")
    s.add_argument("--suggested", action="store_true", help="gate=suggested (default accepted)")
    s.set_defaults(func=cmd_thread_evidence_add)

    s = sub.add_parser("thread-evidence-list", help="List evidences for a thread")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--claim-id", default="")
    s.add_argument("--gate", default="")
    s.set_defaults(func=cmd_thread_evidence_list)

    s = sub.add_parser("thread-evidence-gate", help="Accept/suggest evidence gate")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--evidence-id", required=True)
    s.add_argument("--gate", required=True, choices=["suggested", "accepted"])
    s.set_defaults(func=cmd_thread_evidence_gate)

    s = sub.add_parser("query-trace", help="Append query_iter events (retrieval trajectory)")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--json", default="", help="JSON file: list or {retrieval_trace:[...]}")
    s.add_argument("--round", type=int, default=0)
    s.add_argument("--path-id", default="")
    s.add_argument("--query", default="", help="queries separated by ||")
    s.add_argument("--raw-hits", type=int, default=None)
    s.add_argument("--kept", type=int, default=None)
    s.add_argument("--notes", default="")
    s.set_defaults(func=cmd_query_trace)

    s = sub.add_parser("thread-graph", help="Claim–Evidence cognitive graph JSON")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--id", required=True)
    s.set_defaults(func=cmd_thread_graph)

    s = sub.add_parser("pdf-ingest", help="PDF/txt → wiki paper fulltext.md")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--pdf", required=True, help="PDF or .txt/.md extraction")
    s.add_argument("--path", required=True, help="wiki paper path")
    s.add_argument("--title", default="")
    s.set_defaults(func=cmd_pdf_ingest)

    s = sub.add_parser("claim-suggest", help="Suggest claims from fulltext.md")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--path", required=True)
    s.add_argument("--thread", default="")
    s.add_argument("--max", type=int, default=5)
    s.add_argument("--apply", action="store_true", help="write suggested claims to thread")
    s.add_argument("--no-evidence", action="store_true")
    s.set_defaults(func=cmd_claim_suggest)

    s = sub.add_parser("bibtex-export", help="Export BibTeX from wiki paper paths")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--paths", default="", help="comma-separated wiki paths")
    s.add_argument("--thread", default="", help="also include thread member papers")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_bibtex_export)

    s = sub.add_parser("related-work", help="Write Related Work outline from thread")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--print-md", action="store_true")
    s.set_defaults(func=cmd_related_work)

    s = sub.add_parser("section-outline", help="Method/experiments outline (writing assist)")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--section", default="method", help="method|experiments|related_work")
    s.add_argument("--print-md", action="store_true")
    s.set_defaults(func=cmd_section_outline)

    s = sub.add_parser("paper-draft", help="Multi-chapter Markdown draft pack (traceable, not LaTeX)")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--venue", default="generic", help="cvpr|icml|neurips|acl|generic")
    s.set_defaults(func=cmd_paper_draft)

    s = sub.add_parser("prerank", help="BM25+recency pre-rank candidates before LLM fine-rank")
    s.add_argument("--json", required=True, help="JSON list or {papers/candidates, query}")
    s.add_argument("--query", default="")
    s.add_argument("--top-k", type=int, default=30)
    s.add_argument("--no-citations", action="store_true")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_prerank)

    s = sub.add_parser("citation-expand", help="1-hop citation expand (S2/Crossref)")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--path", required=True, help="wiki paper path")
    s.add_argument("--top-k", type=int, default=5)
    s.add_argument("--no-persist", action="store_true")
    s.set_defaults(func=cmd_citation_expand)

    s = sub.add_parser("evidence-coverage", help="Hypothesis/claim evidence confidence summary")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.set_defaults(func=cmd_evidence_coverage)

    s = sub.add_parser("pdf-fetch", help="Legal OA PDF download → pdf-ingest (no Sci-Hub)")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--path", required=True, help="wiki paper path")
    s.add_argument("--no-keep", action="store_true", help="do not keep PDF under _pdf/")
    s.set_defaults(func=cmd_pdf_fetch)

    s = sub.add_parser("rrf-fuse", help="Reciprocal Rank Fusion across lanes/sources")
    s.add_argument("--json", required=True, help="{lanes:{...}} or list with source field")
    s.add_argument("--k", type=int, default=60)
    s.add_argument("--top-n", type=int, default=200)
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_rrf_fuse)

    s = sub.add_parser("csl-json-export", help="Export CSL-JSON for Zotero")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--paths", default="")
    s.add_argument("--thread", default="")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_csl_json)

    s = sub.add_parser("thread-feedback", help="Record accept|skip|read|pin feedback on a paper")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--action", required=True, choices=["accept", "skip", "read", "pin"])
    s.add_argument("--path", default="", help="wiki paper path")
    s.add_argument("--note", default="")
    s.set_defaults(func=cmd_thread_feedback)

    s = sub.add_parser("thread-bench", help="Run Thread-Bench evaluation (claim coverage / R@K)")
    s.add_argument(
        "--bench-root",
        default="",
        help="default: <wiki-root>/benchmarks/thread-bench or ./benchmarks/thread-bench",
    )
    s.add_argument("--wiki-root", default=".", help="used to locate benchmarks/ if --bench-root omitted")
    s.add_argument("--case", default="", help="single case id under cases/")
    s.add_argument("--k", type=int, default=5)
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_thread_bench)

    s = sub.add_parser("notify-webhook", help="POST a test/Delta payload to webhook URL")
    s.add_argument("--webhook", default="", help="or env PAPER_REC_WEBHOOK_URL")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--json", default="", help="Delta result JSON file")
    s.add_argument("--thread", default="")
    s.add_argument("--mode", default="notify")
    s.add_argument("--title", default="")
    s.add_argument("--message", default="")
    s.set_defaults(func=cmd_notify_webhook)

    s = sub.add_parser("thread-template-list", help="List thread templates (marketplace)")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--seed", action="store_true", help="ensure builtin templates")
    s.set_defaults(func=cmd_template_list)

    s = sub.add_parser("thread-template-export", help="Export a thread as marketplace template")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--thread", required=True)
    s.add_argument("--template-id", default="")
    s.add_argument("--title", default="")
    s.add_argument("--description", default="")
    s.add_argument("--tags", default="")
    s.add_argument("--no-drafts", action="store_true")
    s.add_argument("--evidences", action="store_true")
    s.set_defaults(func=cmd_template_export)

    s = sub.add_parser("thread-template-import", help="Import template → new thread")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--template", required=True)
    s.add_argument("--id", default="", help="new thread id")
    s.add_argument("--title", default="")
    s.set_defaults(func=cmd_template_import)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
