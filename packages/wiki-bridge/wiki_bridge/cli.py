"""CLI: sync-report / rebuild-index."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .dashboard import write_dashboard
from .exp_writer import load_exp_payload, sync_experiment
from .indexer import write_reading_index
from .writer import load_report_json, update_keyword_readmes, write_paper_page, write_query_archive


def workspace_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


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
    s.set_defaults(func=cmd_sync_exp)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
