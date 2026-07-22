"""CLI: sync-report / rebuild-index / sync-exp / thread-*."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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


def cmd_citation_verify(args: argparse.Namespace) -> int:
    from .citation_verify import verify_bib_file

    bib = Path(args.bib)
    out_json = Path(args.out) if args.out else bib.with_suffix(".verify.json")
    filtered = Path(args.filtered_bib) if args.filtered_bib else None
    if args.write_filtered and filtered is None:
        filtered = bib.with_name(bib.stem + ".clean.bib")
    report = verify_bib_file(
        bib,
        out_json=out_json,
        filtered_bib=filtered,
        mailto=args.mailto or "paper-rec@local",
    )
    summary = report.get("summary") or {}
    print(
        json.dumps(
            {
                "integrity_score": summary.get("integrity_score"),
                "verified": summary.get("verified"),
                "suspicious": summary.get("suspicious"),
                "hallucinated": summary.get("hallucinated"),
                "skipped": summary.get("skipped"),
                "report": str(out_json),
                "filtered_bib": str(filtered) if filtered else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    # non-zero if any hallucinated (blocks "ready to submit")
    return 1 if int(summary.get("hallucinated") or 0) > 0 else 0


def cmd_latex_export(args: argparse.Namespace) -> int:
    from .latex_export import export_latex_pack

    draft = Path(args.draft_dir) if args.draft_dir else Path()
    if args.thread:
        from . import thread_store as ts

        draft = ts.thread_dir(Path(args.wiki_root), args.thread) / "drafts" / "paper_draft"
    if getattr(args, "hard_gate", False) and args.exp_dir:
        from .number_verify import discover_exp_metrics, load_registry
        from .verified_registry import hard_gate

        chunks = []
        if draft.is_dir():
            for p in sorted(draft.glob("*.md")):
                chunks.append(p.read_text(encoding="utf-8"))
        metrics = discover_exp_metrics(Path(args.exp_dir))
        reg = load_registry(metrics)["values"]
        gate = hard_gate("\n".join(chunks), reg)
        if gate.get("blocked"):
            print(json.dumps({"blocked": True, "hard_gate": gate}, ensure_ascii=False, indent=2))
            return 1
    out = export_latex_pack(
        draft,
        venue=args.venue,
        title=args.title or "",
        bib_path=Path(args.bib) if args.bib else None,
    )
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


def cmd_ris_export(args: argparse.Namespace) -> int:
    from .ris_export import export_ris

    paths = _split_csv(args.paths) if args.paths else []
    if args.thread:
        data = thread_store.load_thread(Path(args.wiki_root), args.thread)
        paths = list(dict.fromkeys(paths + list(data.get("paper_paths") or [])))
    out = export_ris(Path(args.wiki_root), paths)
    if args.out:
        Path(args.out).write_text(out["ris"], encoding="utf-8")
        print(f"Wrote {args.out} ({out['count']} entries)")
        for w in out["warnings"]:
            print(f"  ! {w}")
    else:
        print(out["ris"])
    return 0


def cmd_rank_intent(args: argparse.Namespace) -> int:
    from .rank_intent import parse_rank_intent

    intent = parse_rank_intent(args.query)
    print(json.dumps(intent.to_dict(), ensure_ascii=False, indent=2))
    return 1 if intent.ambiguous and args.strict else 0


def cmd_filter_code(args: argparse.Namespace) -> int:
    from .code_filter import filter_by_code

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        items = payload
    else:
        items = list(payload.get("documents") or payload.get("papers") or payload.get("candidates") or [])
    out = filter_by_code(items, mode=args.mode)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"kept_n": out["kept_n"], "dropped_n": out["dropped_n"], "out": args.out}, ensure_ascii=False))
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_matrix_build(args: argparse.Namespace) -> int:
    from .literature_matrix import build_literature_matrix

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        items = payload
    else:
        items = list(payload.get("documents") or payload.get("papers") or payload.get("rows") or [])
    out = build_literature_matrix(items)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(out["markdown"], encoding="utf-8")
    summary = {"count": out["count"], "out": args.out or None, "md_out": args.md_out or None}
    print(json.dumps(summary if (args.out or args.md_out) else out, ensure_ascii=False, indent=2))
    return 0


def cmd_claim_ledger(args: argparse.Namespace) -> int:
    from .claim_ledger import build_claim_ledger, build_claim_ledger_from_paths

    known = _split_csv(args.known_keys) if args.known_keys else []
    paths: list[Path] = []
    if args.draft_dir:
        d = Path(args.draft_dir)
        paths.extend(sorted(d.glob("*.md")))
    if args.markdown:
        paths.append(Path(args.markdown))
    if args.claims_json:
        paths.append(Path(args.claims_json))
    if args.thread:
        td = thread_store.thread_dir(Path(args.wiki_root), args.thread) / "drafts" / "paper_draft"
        if td.is_dir():
            paths.extend(sorted(td.glob("*.md")))
    if paths:
        out = build_claim_ledger_from_paths(paths, known_keys=known)
    else:
        md = Path(args.markdown).read_text(encoding="utf-8") if args.markdown else ""
        out = build_claim_ledger(markdown=md, known_keys=known)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "claim_count": out["claim_count"],
                "grounded": out["grounded"],
                "material_gap": out["material_gap"],
                "unknown_cite": out["unknown_cite"],
                "out": args.out or None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if int(out.get("material_gap") or 0) > 0 and args.strict else 0


def cmd_answer_ground(args: argparse.Namespace) -> int:
    from .evidence_ground import check_claims_against_abstracts, ground_answer, ground_from_files

    if args.check_nli:
        claims = json.loads(Path(args.claims_json).read_text(encoding="utf-8")) if args.claims_json else []
        if isinstance(claims, dict):
            claims = list(claims.get("claims") or [])
        papers = json.loads(Path(args.evidences_json).read_text(encoding="utf-8"))
        if isinstance(papers, dict):
            papers = list(papers.get("evidences") or papers.get("papers") or papers.get("contexts") or [])
        out = check_claims_against_abstracts(claims, papers)
        if args.out:
            Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"yes": out["yes"], "no": out["no"], "out": args.out or None}, ensure_ascii=False, indent=2))
        return 1 if int(out.get("no") or 0) > 0 and args.strict else 0

    cutoff = float(getattr(args, "relevance_cutoff", 0) or 0)
    if args.answer_file and args.evidences_json:
        out = ground_from_files(
            Path(args.answer_file),
            Path(args.evidences_json),
            lang=args.lang,
            relevance_cutoff=cutoff,
        )
    else:
        evs = json.loads(Path(args.evidences_json).read_text(encoding="utf-8"))
        if isinstance(evs, dict):
            evs = list(evs.get("evidences") or evs.get("contexts") or [])
        out = ground_answer(args.answer or "", evs, lang=args.lang, relevance_cutoff=cutoff)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "has_successful_answer": out.get("has_successful_answer"),
                "cannot_answer": out.get("cannot_answer"),
                "used_evidences": out.get("used_evidences"),
                "unknown_citations": out.get("unknown_citations"),
                "answer": out.get("grounded_answer") or out.get("answer"),
                "out": args.out or None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if out.get("has_successful_answer") else 1


def cmd_number_verify(args: argparse.Namespace) -> int:
    from .number_verify import discover_exp_metrics, load_registry, verify_paths
    from .verified_registry import hard_gate, persist_registry

    drafts: list[Path] = []
    if args.draft:
        drafts.append(Path(args.draft))
    if args.draft_dir:
        d = Path(args.draft_dir)
        drafts.extend(sorted(d.glob("*.md")))
        drafts.extend(sorted(d.glob("**/*.tex")))
    if args.thread:
        td = thread_store.thread_dir(Path(args.wiki_root), args.thread) / "drafts" / "paper_draft"
        if td.is_dir():
            drafts.extend(sorted(td.glob("*.md")))
            latex = td.parent / "latex" / "main.tex"
            if not latex.is_file():
                latex = td / "latex" / "main.tex"
            if latex.is_file():
                drafts.append(latex)
    metrics: list[Path] = []
    if args.metrics:
        metrics.extend(Path(p) for p in _split_csv(args.metrics))
    if args.exp_dir:
        metrics.extend(discover_exp_metrics(Path(args.exp_dir)))
        if getattr(args, "write_registry", False) or getattr(args, "hard_gate", False):
            persist_registry(Path(args.exp_dir), metrics)
    out = verify_paths(drafts, metrics, tolerance=args.tolerance)
    if getattr(args, "hard_gate", False):
        reg = load_registry(metrics)["values"]
        text = "\n".join(p.read_text(encoding="utf-8") for p in drafts if p.is_file())
        gate = hard_gate(text, reg, tolerance=args.tolerance)
        out["hard_gate"] = gate
        out["ok"] = bool(gate.get("ok"))
        out["blocked"] = bool(gate.get("blocked"))
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    keys = ("ok", "verified_n", "unverified_n", "unverified", "registry_n", "metrics_sources", "blocked", "hard_gate")
    print(json.dumps({k: out[k] for k in keys if k in out}, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else (1 if args.strict or getattr(args, "hard_gate", False) else 0)


def cmd_exp_eval_hook(args: argparse.Namespace) -> int:
    """Write/refresh eval metrics bundle then optionally number-verify drafts."""
    from .number_verify import discover_exp_metrics, verify_paths

    exp_dir = Path(args.exp_dir)
    metrics_dir = exp_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    bundle_info: dict[str, Any] = {}
    if args.metrics_json:
        raw = json.loads(Path(args.metrics_json).read_text(encoding="utf-8-sig"))
        # Prefer skill-exp eval_hook if importable; else write summary locally
        try:
            sys.path.insert(0, str(workspace_root_from_here() / "skill-exp"))
            from reference.eval_hook import write_eval_bundle  # type: ignore

            eid = args.experiment_id or exp_dir.name
            content_root = exp_dir.parent
            target = {}
            if args.target_metric:
                target = {
                    "metric": args.target_metric,
                    "threshold": args.target_threshold,
                    "direction": args.direction,
                }
            bundle_info = write_eval_bundle(
                eid,
                raw if isinstance(raw, dict) else {"value": raw},
                content_root=content_root,
                target=target or None,
                plan_id=args.plan_id or "",
            )
        except Exception:
            summary = metrics_dir / "summary.json"
            payload = raw if isinstance(raw, dict) else {"metrics": raw}
            if "metrics" not in payload and isinstance(payload, dict):
                payload = {"metrics": payload, "number_verify_ready": True}
            summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (metrics_dir / "final.json").write_text(summary.read_text(encoding="utf-8"), encoding="utf-8")
            bundle_info = {"summary_path": str(summary)}

    verify_report = None
    if args.thread or args.draft or args.draft_dir:
        drafts: list[Path] = []
        if args.draft:
            drafts.append(Path(args.draft))
        if args.draft_dir:
            drafts.extend(sorted(Path(args.draft_dir).glob("*.md")))
        if args.thread:
            td = thread_store.thread_dir(Path(args.wiki_root), args.thread) / "drafts" / "paper_draft"
            if td.is_dir():
                drafts.extend(sorted(td.glob("*.md")))
        metrics = discover_exp_metrics(exp_dir)
        verify_report = verify_paths(drafts, metrics, tolerance=args.tolerance)
        out_path = metrics_dir / "number_verify.json"
        out_path.write_text(json.dumps(verify_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        verify_report["report_path"] = str(out_path)

    result = {
        "exp_dir": str(exp_dir),
        "bundle": bundle_info,
        "number_verify": verify_report,
        "metrics_files": [str(p) for p in discover_exp_metrics(exp_dir)],
    }
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if verify_report is not None and args.strict and not verify_report.get("ok"):
        return 1
    return 0


def cmd_exp_tree(args: argparse.Namespace) -> int:
    """Manage lightweight experiment tree under content/exp/<id>/trace/exp_tree.json."""
    # Import from skill-exp reference
    skill_exp = workspace_root_from_here() / "skill-exp"
    if str(skill_exp) not in sys.path:
        sys.path.insert(0, str(skill_exp))
    from reference.exp_tree import (  # type: ignore
        expand_from_best,
        load_tree,
        mark_buggy,
        ready_for_next_stage,
        render_tree_md,
        save_tree,
    )

    content_root = Path(args.content_root)
    tree = load_tree(content_root, args.experiment_id)
    action = args.action
    if action == "show":
        out = {"tree": tree.to_dict(), "markdown": render_tree_md(tree), "ready": ready_for_next_stage(tree)}
    elif action == "add":
        node = expand_from_best(
            tree,
            plan_id=args.plan_id or "P?",
            metric=args.metric,
            metric_name=args.metric_name or "",
            as_ablation=args.ablation,
        )
        if args.buggy:
            mark_buggy(tree, node.id, notes=args.notes or "")
        path = save_tree(tree, content_root)
        out = {"node": node.id, "path": str(path), "ready": ready_for_next_stage(tree)}
    elif action == "buggy":
        if not args.node_id:
            print(json.dumps({"error": "--node-id required"}, ensure_ascii=False))
            return 2
        mark_buggy(tree, args.node_id, notes=args.notes or "")
        path = save_tree(tree, content_root)
        out = {"node": args.node_id, "path": str(path), "ready": ready_for_next_stage(tree)}
    elif action == "ready":
        out = ready_for_next_stage(tree)
    else:
        print(json.dumps({"error": f"unknown action {action}"}, ensure_ascii=False))
        return 2
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_gather_evidence(args: argparse.Namespace) -> int:
    from .evidence_score import gather_evidence

    docs = json.loads(Path(args.documents).read_text(encoding="utf-8-sig"))
    if isinstance(docs, dict):
        docs = list(docs.get("documents") or docs.get("papers") or docs.get("fulltexts") or [])
    out = gather_evidence(args.question, docs, cutoff=args.cutoff)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "kept_n": out["kept_n"],
                "dropped_n": out["dropped_n"],
                "cannot_answer": out["cannot_answer"],
                "out": args.out or None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if out.get("cannot_answer") and args.strict else 0


def cmd_stats_rigor(args: argparse.Namespace) -> int:
    from .stats_rigor import check_stats_rigor

    text = Path(args.draft).read_text(encoding="utf-8") if args.draft else ""
    if args.thread and not text:
        td = thread_store.thread_dir(Path(args.wiki_root), args.thread) / "drafts" / "paper_draft"
        parts = []
        if td.is_dir():
            for p in sorted(td.glob("*.md")):
                parts.append(p.read_text(encoding="utf-8"))
        text = "\n\n".join(parts)
    out = check_stats_rigor(text)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("ok", "claim_sentences", "issue_n", "section_has_variance_cue")}, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else (1 if args.strict else 0)


def cmd_survey_draft(args: argparse.Namespace) -> int:
    from .survey_write import build_survey_draft

    papers = json.loads(Path(args.json).read_text(encoding="utf-8-sig"))
    if isinstance(papers, dict):
        papers = list(papers.get("papers") or papers.get("documents") or [])
    out = build_survey_draft(
        papers,
        chunk_size=args.chunk_size,
        rag_k=args.rag_k,
        topic=getattr(args, "topic", "") or "",
    )
    if args.out:
        Path(args.out).write_text(out["markdown"], encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "section_n": out["section_n"],
                "outline_chunks": out["outline_chunks"],
                "cite_ok": (out.get("cite_audit") or {}).get("ok"),
                "out": args.out or None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if out.get("ok", True) else (1 if getattr(args, "strict", False) else 0)


def cmd_novelty_check(args: argparse.Namespace) -> int:
    from .novelty_check import check_idea_novelty

    papers = []
    if args.papers_json:
        raw = json.loads(Path(args.papers_json).read_text(encoding="utf-8-sig"))
        papers = raw if isinstance(raw, list) else list(raw.get("papers") or raw.get("documents") or [])
    out = check_idea_novelty(args.idea, papers, use_openalex=args.openalex, mailto=args.mailto)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"novel": out["novel"], "decision": out["decision"]}, ensure_ascii=False, indent=2))
    return 0 if out.get("novel") else (1 if args.strict else 0)


def cmd_fig_review(args: argparse.Namespace) -> int:
    from .fig_review import load_vlm_reviews_file, review_figures

    text = Path(args.draft).read_text(encoding="utf-8") if args.draft else ""
    paths = _split_csv(args.figure_paths) if args.figure_paths else []
    vlm = load_vlm_reviews_file(Path(args.vlm_json)) if getattr(args, "vlm_json", "") and args.vlm_json else None
    out = review_figures(
        text,
        figure_paths=paths or None,
        abstract=getattr(args, "abstract", "") or "",
        vlm_reviews=vlm,
        emit_vlm_prompts=bool(getattr(args, "emit_vlm_prompts", False)),
    )
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("ok", "figure_n", "ref_n", "issue_n", "vlm_applied") if k in out}, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else (1 if args.strict else 0)


def cmd_feedback_edit(args: argparse.Namespace) -> int:
    from .feedback_edit import feedback_edit_loop

    answer = args.answer or ""
    if args.answer_file:
        answer = Path(args.answer_file).read_text(encoding="utf-8")
    evs = json.loads(Path(args.evidences_json).read_text(encoding="utf-8-sig"))
    if isinstance(evs, dict):
        evs = list(evs.get("evidences") or evs.get("contexts") or [])
    cands = []
    if args.candidates_json:
        raw = json.loads(Path(args.candidates_json).read_text(encoding="utf-8-sig"))
        cands = raw if isinstance(raw, list) else list(raw.get("papers") or raw.get("documents") or [])
    out = feedback_edit_loop(args.question, answer, evs, candidate_docs=cands, lang=args.lang)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": out["ok"],
                "feedback_n": out["feedback_n"],
                "needs_retrieve": out["needs_retrieve"],
                "followup_queries": out["followup_queries"],
                "new_evidence_n": out["new_evidence_n"],
                "out": args.out or None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if out.get("ok") else (1 if args.strict else 0)


def cmd_deep_research(args: argparse.Namespace) -> int:
    from .deep_research import build_deep_research_plan

    papers = json.loads(Path(args.json).read_text(encoding="utf-8-sig"))
    if isinstance(papers, dict):
        papers = list(papers.get("papers") or papers.get("documents") or [])
    out = build_deep_research_plan(args.topic, papers, max_depth=args.max_depth, breadth=args.breadth)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"next_queries": out["next_queries"], "out": args.out or None}, ensure_ascii=False, indent=2))
    return 0


def cmd_research_session(args: argparse.Namespace) -> int:
    from . import research_session as rs

    root = Path(args.wiki_root)
    if args.action == "create":
        sources = []
        context = {}
        if args.sources_json:
            sources = json.loads(Path(args.sources_json).read_text(encoding="utf-8-sig"))
            if isinstance(sources, dict):
                sources = list(sources.get("sources") or sources.get("papers") or [])
        if args.context_json:
            context = json.loads(Path(args.context_json).read_text(encoding="utf-8-sig"))
        out = rs.create_session(root, topic=args.topic, sources=sources, context=context, thread_id=args.thread or "")
    elif args.action == "sources":
        out = rs.get_sources(root, args.research_id)
    elif args.action == "write-report":
        out = rs.write_report_payload(root, args.research_id)
    else:
        out = {"error": f"unknown action {args.action}"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok", True) and "error" not in out else 1


def cmd_exp_reflect(args: argparse.Namespace) -> int:
    skill_exp = workspace_root_from_here() / "skill-exp"
    if str(skill_exp) not in sys.path:
        sys.path.insert(0, str(skill_exp))
    from reference.exp_reflect import build_findings  # type: ignore

    out = build_findings(Path(args.exp_dir), hypothesis=args.hypothesis or "")
    print(json.dumps({"findings_path": out["findings_path"], "state_path": out["state_path"]}, ensure_ascii=False, indent=2))
    return 0


def cmd_repro_check(args: argparse.Namespace) -> int:
    skill_exp = workspace_root_from_here() / "skill-exp"
    if str(skill_exp) not in sys.path:
        sys.path.insert(0, str(skill_exp))
    from reference.repro_design import (  # type: ignore
        default_design,
        double_exec_check,
        load_design,
        save_design,
        validate_design,
        write_repro_report,
    )

    exp_dir = Path(args.exp_dir)
    if args.init_design:
        path = exp_dir / "trace" / "exp_design.json"
        save_design(path, default_design(args.metric or "F1"))
        print(json.dumps({"wrote": str(path)}, ensure_ascii=False, indent=2))
        return 0
    design_path = Path(args.design) if args.design else exp_dir / "trace" / "exp_design.json"
    design = load_design(design_path) if design_path.is_file() else default_design(args.metric or "F1")
    v = validate_design(design)
    if args.run_a and args.run_b:
        a = json.loads(Path(args.run_a).read_text(encoding="utf-8-sig"))
        b = json.loads(Path(args.run_b).read_text(encoding="utf-8-sig"))
        if isinstance(a, dict) and "metrics" in a:
            a = a["metrics"]
        if isinstance(b, dict) and "metrics" in b:
            b = b["metrics"]
        check = double_exec_check(
            a,
            b,
            metric=args.metric or design.metric,
            max_rel_diff=args.max_rel_diff,
        )
        report = {"design_ok": v["ok"], "design_issues": v["issues"], "double_exec": check}
        write_repro_report(exp_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if check.get("ok") else (1 if args.strict else 0)
    print(json.dumps(v, ensure_ascii=False, indent=2))
    return 0 if v.get("ok") else (1 if args.strict else 0)


def cmd_discovery_curve(args: argparse.Namespace) -> int:
    from .discovery_curve import analyze_snapshots

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    snaps = payload if isinstance(payload, list) else list(payload.get("snapshots") or [])
    out = analyze_snapshots(snaps)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if out.get("warn_low_progress") and args.strict else 0


def cmd_reflect_search(args: argparse.Namespace) -> int:
    from .reflect_search import reflect_coverage

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        papers = payload
    else:
        papers = list(payload.get("documents") or payload.get("papers") or payload.get("candidates") or [])
    out = reflect_coverage(
        papers,
        query=args.query or "",
        since_year=args.since_year or None,
        max_papers=args.max_papers,
        code_filter=args.code_filter,
    )
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_screen_next(args: argparse.Namespace) -> int:
    from .screen_next import build_label_map, screen_next

    cands = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    if isinstance(cands, dict):
        cands = list(cands.get("documents") or cands.get("papers") or cands.get("candidates") or [])
    labels: dict[str, int] = {}
    if args.labels_json:
        raw = json.loads(Path(args.labels_json).read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "labels" in raw:
            labels = {str(k): int(v) for k, v in raw["labels"].items()}
        elif isinstance(raw, list):
            labels = build_label_map(raw)
        else:
            labels = {str(k): int(v) for k, v in raw.items()}
    elif args.thread:
        data = thread_store.load_thread(Path(args.wiki_root), args.thread)
        events = list(data.get("events") or []) + list(data.get("feedback") or [])
        labels = build_label_map(events)
    out = screen_next(
        cands,
        labels,
        batch_size=args.batch_size,
        strategy=args.strategy,
        consecutive_irrelevant_stop=args.stop_n,
    )
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**{k: out[k] for k in out if k != "batch"}, "batch_titles": [x.get("title") for x in out.get("batch") or []]}, ensure_ascii=False, indent=2))
    return 1 if out.get("stopped") else 0


def cmd_posthoc_cite(args: argparse.Namespace) -> int:
    from .posthoc_cite import posthoc_attribute

    md = Path(args.markdown).read_text(encoding="utf-8") if args.markdown else ""
    if args.thread and not md:
        td = thread_store.thread_dir(Path(args.wiki_root), args.thread) / "drafts" / "paper_draft"
        parts = []
        if td.is_dir():
            for p in sorted(td.glob("*.md")):
                parts.append(p.read_text(encoding="utf-8"))
        md = "\n\n".join(parts)
    evs = json.loads(Path(args.evidences_json).read_text(encoding="utf-8"))
    if isinstance(evs, dict):
        evs = list(evs.get("evidences") or evs.get("papers") or evs.get("contexts") or [])
    out = posthoc_attribute(md, evs, max_sentences=args.max_sentences)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("scanned_claims", "attributed_n", "needs_attribution_n")}, ensure_ascii=False, indent=2))
    return 1 if out.get("needs_attribution_n") and args.strict else 0


def cmd_research_brief(args: argparse.Namespace) -> int:
    from .research_brief import build_research_brief

    must = _split_csv(args.must_answer) if args.must_answer else []
    oos = _split_csv(args.out_of_scope) if args.out_of_scope else []
    packs = _split_csv(args.packs) if args.packs else []
    out = build_research_brief(
        topic=args.topic,
        must_answer=must,
        out_of_scope=oos,
        packs=packs,
        language=args.lang,
    )
    if args.out:
        Path(args.out).write_text(out["markdown"], encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"topic": out["topic"], "must_answer": out["must_answer"], "out": args.out or None}, ensure_ascii=False, indent=2))
    return 0


def cmd_wiki_filter_parse(args: argparse.Namespace) -> int:
    from .wiki_filters import parse_wiki_query

    out = parse_wiki_query(args.query).to_dict()
    print(json.dumps(out, ensure_ascii=False, indent=2))
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


def cmd_arxiv_watch(args: argparse.Namespace) -> int:
    from .arxiv_watch import run_arxiv_watch

    cats = [c.strip() for c in (args.cats or "").split(",") if c.strip()] or None
    out = run_arxiv_watch(
        Path(args.wiki_root),
        cats=cats,
        config_path=Path(args.config) if args.config else None,
        state_dir=Path(args.state_dir) if args.state_dir else None,
        last_update_date=args.since if args.since else None,
        max_per_cat=args.max_per_cat,
        page_size=args.page_size,
        wait_time=args.wait_time,
        time_gap=args.time_gap,
        keyword=args.keyword,
        ingest=args.ingest,
        fetch_pdf=not args.no_fetch,
        dry_run=args.dry_run,
        keep_pdf=not args.no_keep,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 1


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


def cmd_litsearch_eval(args: argparse.Namespace) -> int:
    from .litsearch_eval import evaluate, load_fixture, load_hf, write_result

    bench = Path(args.bench_root) if args.bench_root else Path("benchmarks/litsearch")
    if not bench.is_dir():
        wiki = Path(args.wiki_root).resolve()
        cand = wiki / "benchmarks" / "litsearch"
        bench = cand if cand.is_dir() else bench
    if args.fixture:
        queries, corpus = load_fixture(bench / "fixtures")
        tag = "fixture"
    else:
        cache = Path(args.cache_dir) if args.cache_dir else bench / "cache"
        queries, corpus = load_hf(cache_dir=cache)
        tag = "full"
    result = evaluate(
        queries,
        corpus,
        method=args.method,
        top_k=args.top_k,
        limit_queries=args.limit_queries or None,
        candidate_pool=args.candidate_pool,
    )
    result["tag"] = tag
    out = Path(args.out) if args.out else bench / "runs" / f"{args.method}_{tag}.json"
    write_result(out, result, slim=not args.full_per_query)
    print(json.dumps({"out": str(out), "metrics_mean": result["metrics_mean"], "method": args.method, "tag": tag, "n_queries": result["n_queries"]}, ensure_ascii=False, indent=2))
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
    s.add_argument(
        "--evidence-level",
        default="",
        help="CEBM-lite 1a|1b|2a|2b|3a|3b|4|5 (aliases: meta,rct,cohort,anecdote,…)",
    )
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

    s = sub.add_parser("ris-export", help="Export RIS (Zotero/EndNote) from wiki paths")
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--paths", default="")
    s.add_argument("--thread", default="")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_ris_export)

    s = sub.add_parser(
        "rank-intent",
        help="Strip journal-rank / language markers from query (CAS/JCR/SJR)",
    )
    s.add_argument("--query", required=True)
    s.add_argument("--strict", action="store_true", help="exit 1 if ambiguous platform")
    s.set_defaults(func=cmd_rank_intent)

    s = sub.add_parser(
        "filter-code",
        help="Filter candidates by code availability (any|required|none)",
    )
    s.add_argument("--json", required=True, help="JSON list or {documents/papers/candidates}")
    s.add_argument("--mode", default="any", choices=["any", "required", "none"])
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_filter_code)

    s = sub.add_parser("matrix-build", help="Build literature matrix rows (+ optional MD table)")
    s.add_argument("--json", required=True, help="JSON list or {documents/papers}")
    s.add_argument("--out", default="", help="write matrix JSON")
    s.add_argument("--md-out", default="", help="write Markdown table")
    s.set_defaults(func=cmd_matrix_build)

    s = sub.add_parser(
        "claim-ledger",
        help="Scan draft MD/JSON for uncited claims (MATERIAL GAP gate)",
    )
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--thread", default="", help="scan drafts/paper_draft/*.md")
    s.add_argument("--draft-dir", default="")
    s.add_argument("--markdown", default="", help="single .md path")
    s.add_argument("--claims-json", default="", help="optional claims JSON")
    s.add_argument("--known-keys", default="", help="comma-separated allowed cite keys")
    s.add_argument("--out", default="")
    s.add_argument("--strict", action="store_true", help="exit 1 if any material_gap")
    s.set_defaults(func=cmd_claim_ledger)

    s = sub.add_parser(
        "answer-ground",
        help="Expand (E12) cites → References; cannot-answer if no usable evidence",
    )
    s.add_argument("--answer", default="", help="raw answer text with (E1) markers")
    s.add_argument("--answer-file", default="")
    s.add_argument("--evidences-json", required=True, help="list or {evidences:[...]}")
    s.add_argument("--claims-json", default="", help="with --check-nli: claims to verify")
    s.add_argument("--check-nli", action="store_true", help="AutoSurvey Yes/No abstract support check")
    s.add_argument("--strict", action="store_true", help="exit 1 if any No under --check-nli")
    s.add_argument("--lang", default="en", help="en|zh for cannot-answer phrase")
    s.add_argument(
        "--relevance-cutoff",
        type=float,
        default=0.0,
        help="drop evidences with relevance_score below this (use after gather-evidence)",
    )
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_answer_ground)

    s = sub.add_parser(
        "number-verify",
        help="Reject draft/LaTeX floats not present in experiment metrics whitelist",
    )
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--thread", default="")
    s.add_argument("--draft", default="", help="single md/tex file")
    s.add_argument("--draft-dir", default="")
    s.add_argument("--exp-dir", default="", help="content/exp/<id> — auto-discover metrics/*.json")
    s.add_argument("--metrics", default="", help="comma-separated metric JSON paths")
    s.add_argument("--tolerance", type=float, default=0.011)
    s.add_argument("--strict", action="store_true", help="exit 1 if any unverified float")
    s.add_argument("--hard-gate", action="store_true", help="BLOCK on unverified Results floats / empty registry")
    s.add_argument("--write-registry", action="store_true", help="persist metrics/verified_registry.json under --exp-dir")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_number_verify)

    s = sub.add_parser(
        "exp-eval-hook",
        help="Write metrics/summary.json from eval JSON, then optional number-verify",
    )
    s.add_argument("--exp-dir", required=True, help="content/exp/<id>")
    s.add_argument("--experiment-id", default="", help="defaults to exp-dir name")
    s.add_argument("--metrics-json", default="", help="eval metrics JSON to persist")
    s.add_argument("--plan-id", default="")
    s.add_argument("--target-metric", default="")
    s.add_argument("--target-threshold", type=float, default=None)
    s.add_argument("--direction", default="maximize")
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--thread", default="", help="if set, number-verify thread drafts")
    s.add_argument("--draft", default="")
    s.add_argument("--draft-dir", default="")
    s.add_argument("--tolerance", type=float, default=0.011)
    s.add_argument("--strict", action="store_true")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_exp_eval_hook)

    s = sub.add_parser("exp-tree", help="Lightweight experiment tree (draft/improve/ablation)")
    s.add_argument("--content-root", default="content/exp")
    s.add_argument("--experiment-id", required=True)
    s.add_argument("--action", required=True, choices=["show", "add", "buggy", "ready"])
    s.add_argument("--plan-id", default="")
    s.add_argument("--metric", type=float, default=None)
    s.add_argument("--metric-name", default="")
    s.add_argument("--ablation", action="store_true")
    s.add_argument("--buggy", action="store_true")
    s.add_argument("--node-id", default="")
    s.add_argument("--notes", default="")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_exp_tree)

    s = sub.add_parser("gather-evidence", help="Chunk docs, score relevance 0-10, keep above cutoff")
    s.add_argument("--question", required=True)
    s.add_argument("--documents", required=True, help="JSON list of {fulltext|abstract|text}")
    s.add_argument("--cutoff", type=float, default=3.0)
    s.add_argument("--strict", action="store_true")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_gather_evidence)

    s = sub.add_parser("stats-rigor", help="Results claims need ±/std/CI/seeds cues")
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--thread", default="")
    s.add_argument("--draft", default="")
    s.add_argument("--strict", action="store_true")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_stats_rigor)

    s = sub.add_parser("survey-draft", help="Outline-merge + subsection RAG related-work draft")
    s.add_argument("--json", required=True, help="papers JSON")
    s.add_argument("--topic", default="")
    s.add_argument("--chunk-size", type=int, default=8)
    s.add_argument("--rag-k", type=int, default=5)
    s.add_argument("--out", default="", help="markdown path")
    s.add_argument("--json-out", default="")
    s.add_argument("--strict", action="store_true", help="exit 1 if cite audit fails")
    s.set_defaults(func=cmd_survey_draft)

    s = sub.add_parser("novelty-check", help="Idea novelty vs local corpus (+ optional OpenAlex)")
    s.add_argument("--idea", required=True)
    s.add_argument("--papers-json", default="")
    s.add_argument("--openalex", action="store_true")
    s.add_argument("--mailto", default="paper-rec@local")
    s.add_argument("--strict", action="store_true")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_novelty_check)

    s = sub.add_parser("fig-review", help="Figure/caption/ref consistency (+ optional VLM JSON)")
    s.add_argument("--draft", required=True)
    s.add_argument("--figure-paths", default="")
    s.add_argument("--abstract", default="")
    s.add_argument("--vlm-json", default="", help="precomputed VLM review JSON list")
    s.add_argument("--emit-vlm-prompts", action="store_true", help="include prompt bundles for a vision model")
    s.add_argument("--strict", action="store_true")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_fig_review)

    s = sub.add_parser("feedback-edit", help="Critique answer → rewrite markers → re-retrieve queries")
    s.add_argument("--question", required=True)
    s.add_argument("--answer", default="")
    s.add_argument("--answer-file", default="")
    s.add_argument("--evidences-json", required=True)
    s.add_argument("--candidates-json", default="", help="extra docs for re-retrieve")
    s.add_argument("--lang", default="en")
    s.add_argument("--strict", action="store_true")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_feedback_edit)

    s = sub.add_parser("deep-research", help="Learnings tree → follow-up queries (depth×breadth)")
    s.add_argument("--topic", required=True)
    s.add_argument("--json", required=True, help="current paper hits JSON")
    s.add_argument("--max-depth", type=int, default=2)
    s.add_argument("--breadth", type=int, default=3)
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_deep_research)

    s = sub.add_parser("research-session", help="Deferred gather→write_report session store")
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--action", required=True, choices=["create", "sources", "write-report"])
    s.add_argument("--topic", default="")
    s.add_argument("--thread", default="")
    s.add_argument("--research-id", default="")
    s.add_argument("--sources-json", default="")
    s.add_argument("--context-json", default="")
    s.set_defaults(func=cmd_research_session)

    s = sub.add_parser("exp-reflect", help="Outer-loop findings.md + research-state from exp dir")
    s.add_argument("--exp-dir", required=True)
    s.add_argument("--hypothesis", default="")
    s.set_defaults(func=cmd_exp_reflect)

    s = sub.add_parser("repro-check", help="Control/experimental design + double-exec gate")
    s.add_argument("--exp-dir", required=True)
    s.add_argument("--init-design", action="store_true")
    s.add_argument("--design", default="")
    s.add_argument("--run-a", default="", help="metrics JSON run A")
    s.add_argument("--run-b", default="", help="metrics JSON run B")
    s.add_argument("--metric", default="F1")
    s.add_argument("--max-rel-diff", type=float, default=0.02)
    s.add_argument("--strict", action="store_true")
    s.set_defaults(func=cmd_repro_check)

    s = sub.add_parser("discovery-curve", help="Advisory saturation fit on retrieval wave snapshots")
    s.add_argument("--json", required=True, help="list of {papers_evaluated, highly_relevant_count}")
    s.add_argument("--out", default="")
    s.add_argument("--strict", action="store_true", help="exit 1 when warn_low_progress")
    s.set_defaults(func=cmd_discovery_curve)

    s = sub.add_parser("reflect-search", help="Coverage reflection → improved follow-up queries")
    s.add_argument("--json", required=True, help="ranked candidates JSON")
    s.add_argument("--query", default="")
    s.add_argument("--since-year", type=int, default=0)
    s.add_argument("--max-papers", type=int, default=50)
    s.add_argument("--code-filter", default="any", choices=["any", "required", "none"])
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_reflect_search)

    s = sub.add_parser("screen-next", help="Active screening next batch from accept/skip labels")
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--thread", default="", help="read feedback events from thread")
    s.add_argument("--candidates", required=True, help="candidate pool JSON")
    s.add_argument("--labels-json", default="", help="path→0/1 map or feedback event list")
    s.add_argument("--strategy", default="hybrid", choices=["hybrid", "max", "uncertainty"])
    s.add_argument("--batch-size", type=int, default=10)
    s.add_argument("--stop-n", type=int, default=10, help="stop after N irrelevant labels (cold skip storm)")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_screen_next)

    s = sub.add_parser("posthoc-cite", help="Bind uncited claim sentences to evidence pool")
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--thread", default="")
    s.add_argument("--markdown", default="")
    s.add_argument("--evidences-json", required=True)
    s.add_argument("--max-sentences", type=int, default=20)
    s.add_argument("--strict", action="store_true")
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_posthoc_cite)

    s = sub.add_parser("research-brief", help="Write research brief before Module 1 rewrite")
    s.add_argument("--topic", required=True)
    s.add_argument("--must-answer", default="", help="comma-separated questions")
    s.add_argument("--out-of-scope", default="")
    s.add_argument("--packs", default="")
    s.add_argument("--lang", default="en")
    s.add_argument("--out", default="", help="write markdown brief")
    s.add_argument("--json-out", default="")
    s.set_defaults(func=cmd_research_brief)

    s = sub.add_parser("wiki-filter-parse", help="Parse +term -term dt>=YYYY file:pdf library query")
    s.add_argument("--query", required=True)
    s.set_defaults(func=cmd_wiki_filter_parse)

    s = sub.add_parser(
        "citation-verify",
        help="Verify BibTeX against arXiv/CrossRef/OpenAlex (hallucination gate)",
    )
    s.add_argument("--bib", required=True, help="path to .bib")
    s.add_argument("--out", default="", help="JSON report path")
    s.add_argument("--filtered-bib", default="", help="write cleaned .bib (drop hallucinated)")
    s.add_argument("--write-filtered", action="store_true", help="auto-write *.clean.bib")
    s.add_argument("--mailto", default="paper-rec@local")
    s.set_defaults(func=cmd_citation_verify)

    s = sub.add_parser(
        "latex-export",
        help="Export paper_draft Markdown → Overleaf-ready latex/main.tex",
    )
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--thread", default="", help="use content/threads/<id>/drafts/paper_draft")
    s.add_argument("--draft-dir", default="", help="explicit draft directory")
    s.add_argument("--venue", default="generic", help="neurips|icml|iclr|cvpr|acl|generic")
    s.add_argument("--title", default="")
    s.add_argument("--bib", default="", help="optional references.bib path")
    s.add_argument("--exp-dir", default="", help="with --hard-gate: metrics for Results BLOCK")
    s.add_argument("--hard-gate", action="store_true", help="refuse export if Results floats fail verified registry")
    s.set_defaults(func=cmd_latex_export)

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

    s = sub.add_parser(
        "arxiv-watch",
        help="Multi-cat arXiv harvest → day JSON + watermark; optional wiki stub + pdf-fetch",
    )
    s.add_argument("--wiki-root", required=True)
    s.add_argument("--cats", default="", help="comma-separated, e.g. cs.IR,cs.CL,cs.LG")
    s.add_argument("--config", default="", help="JSON config (cats, wait_time, keyword, …)")
    s.add_argument("--state-dir", default="", help="default: content/arxiv_watch")
    s.add_argument("--since", default="", help="watermark override YYYY-MM-DD (published > since)")
    s.add_argument("--max-per-cat", type=int, default=100)
    s.add_argument("--page-size", type=int, default=50)
    s.add_argument("--wait-time", type=float, default=3.0, help="seconds between API pages/cats")
    s.add_argument("--time-gap", type=float, default=5.0, help="seconds between PDF fetches")
    s.add_argument("--keyword", default="arxiv-watch", help="wiki keyword folder for new stubs")
    s.add_argument("--ingest", action="store_true", help="write wiki stubs (+ pdf-fetch unless --no-fetch)")
    s.add_argument("--no-fetch", action="store_true", help="with --ingest: stubs only, skip PDF")
    s.add_argument("--no-keep", action="store_true", help="do not keep PDF under _pdf/")
    s.add_argument("--dry-run", action="store_true", help="harvest only; no files/state/ingest")
    s.set_defaults(func=cmd_arxiv_watch)

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

    s = sub.add_parser("litsearch-eval", help="LitSearch Recall@K / MRR / nDCG (fixture or HF full)")
    s.add_argument("--wiki-root", default=".")
    s.add_argument("--bench-root", default="")
    s.add_argument("--fixture", action="store_true", help="offline smoke fixtures")
    s.add_argument("--method", choices=("bm25", "prerank"), default="bm25")
    s.add_argument("--limit-queries", type=int, default=0)
    s.add_argument("--top-k", type=int, default=100)
    s.add_argument("--candidate-pool", type=int, default=500)
    s.add_argument("--cache-dir", default="")
    s.add_argument("--out", default="")
    s.add_argument("--full-per-query", action="store_true")
    s.set_defaults(func=cmd_litsearch_eval)

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
