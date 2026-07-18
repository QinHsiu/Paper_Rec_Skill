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

    result = run_delta(
        Path(args.wiki_root),
        args.id,
        mode=args.mode or "auto",
        threshold=float(args.threshold),
        persist=not args.dry_run,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "markdown"}, ensure_ascii=False, indent=2))
    if args.print_md:
        print("\n" + result.get("markdown", ""))
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
    s.set_defaults(func=cmd_thread_delta)

    s = sub.add_parser("thread-claim", help="Propose or accept claim status updates")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--id", required=True, help="thread id")
    s.add_argument("--claim-id", default="")
    s.add_argument("--status", default="supported")
    s.add_argument("--accept", action="store_true", help="accept gate (write claim status)")
    s.add_argument("--reason", default="")
    s.set_defaults(func=cmd_thread_claim)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
