"""Smart lab notebook: scaffold, H→E→F entries, mechanical verify, synthesize.

Used by `/labnote` and `/labnote_loop` (exp-sandbox) via wiki_bridge CLI.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_BAR_LINE = re.compile(
    r"^(\s*-\s*)\[([ xX\-])\](\s*)(.+)$",
    re.MULTILINE,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_snapshot(exp_dir: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"sha": None, "dirty": None, "summary": ""}
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(exp_dir.resolve()),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=str(exp_dir.resolve()),
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        )
        info["sha"] = sha
        info["dirty"] = dirty
        info["summary"] = f"HEAD={sha} dirty={dirty}"
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        # Try repo root walk
        try:
            root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            dirty = bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=root, text=True
                ).strip()
            )
            info["sha"] = sha
            info["dirty"] = dirty
            info["summary"] = f"HEAD={sha} dirty={dirty}"
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            info["summary"] = "git unavailable"
    return info


def labbook_dir(exp_dir: Path) -> Path:
    return Path(exp_dir) / "labbook"


def next_entry_id(lb: Path) -> str:
    entries = lb / "entries"
    entries.mkdir(parents=True, exist_ok=True)
    nums = []
    for p in entries.glob("E*.md"):
        m = re.match(r"E(\d+)", p.stem)
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) + 1) if nums else 1
    return f"E{n:04d}"


def init_labbook(
    exp_dir: Path,
    *,
    hypothesis: str = "",
    target_score: dict[str, Any] | None = None,
    bars: list[str] | None = None,
    thread_id: str = "",
) -> dict[str, Any]:
    exp_dir = Path(exp_dir)
    lb = labbook_dir(exp_dir)
    (lb / "entries").mkdir(parents=True, exist_ok=True)
    (lb / "verify").mkdir(parents=True, exist_ok=True)
    (lb / "git_snapshots").mkdir(parents=True, exist_ok=True)

    ts = target_score or {}
    bar_lines = bars or []
    if not bar_lines and ts:
        metric = ts.get("metric") or ts.get("primary_metric") or "metric"
        thr = ts.get("threshold")
        split = ts.get("eval_set") or ts.get("split") or "eval"
        if thr is not None:
            bar_lines = [f"{metric} >= {thr} on {split}"]
    if not bar_lines:
        bar_lines = ["primary_metric meets target_score.threshold on eval split"]

    config = [
        f"# Labbook config — {exp_dir.name}",
        "",
        f"_Locked at: {_utc_now()}_",
        "",
        "## Thread",
        "",
        thread_id or "_(none)_",
        "",
        "## Global hypothesis",
        "",
        hypothesis or "_(fill)_",
        "",
        "## target_score",
        "",
        "```json",
        json.dumps(ts, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pre-locked bars (do not edit thresholds after lock)",
        "",
    ]
    for b in bar_lines:
        config.append(f"- [ ] {b}")
    config.extend(
        [
            "",
            "## Rules",
            "",
            "- Numbers in entries must come from metrics/ or number-verify registry.",
            "- Mechanical verdict from bar checkboxes only.",
            "- Read dead_ends before proposing the next hypothesis.",
            "",
        ]
    )
    cfg_path = lb / "config.md"
    if not cfg_path.is_file():
        cfg_path.write_text("\n".join(config), encoding="utf-8")

    for name, body in [
        ("INDEX.md", f"# Labbook index — {exp_dir.name}\n\n_No entries yet._\n"),
        ("log.md", f"# Lab notebook log — {exp_dir.name}\n\n"),
        ("parking-lot.md", "# Parking lot\n\nIdeas deferred for later.\n"),
    ]:
        p = lb / name
        if not p.is_file():
            p.write_text(body, encoding="utf-8")

    tsv = lb / "results.tsv"
    if not tsv.is_file():
        tsv.write_text(
            "entry_id\tstatus\tverdict\tplan_id\tmetric\tvalue\tgit_sha\tcreated\ttitle\n",
            encoding="utf-8",
        )

    return {"labbook": str(lb), "config": str(cfg_path), "created": True}


def append_entry(
    exp_dir: Path,
    *,
    title: str,
    hypothesis: str,
    plan_id: str = "",
    change: str = "",
    bars: list[str] | None = None,
    evidence_files: list[str] | None = None,
    narrative: list[str] | None = None,
    decision: str = "continue",
) -> dict[str, Any]:
    exp_dir = Path(exp_dir)
    lb = labbook_dir(exp_dir)
    if not (lb / "config.md").is_file():
        init_labbook(exp_dir, hypothesis=hypothesis)

    eid = next_entry_id(lb)
    git = _git_snapshot(exp_dir)
    snap = lb / "git_snapshots" / f"{eid}.txt"
    snap.write_text(git.get("summary") or "", encoding="utf-8")

    # Prefer bars from config if not provided
    cfg_bars: list[str] = []
    cfg = (lb / "config.md").read_text(encoding="utf-8")
    for m in _BAR_LINE.finditer(cfg):
        cfg_bars.append(m.group(4).strip())
    use_bars = bars or cfg_bars or ["primary_metric meets target"]

    metrics = _load_metrics(exp_dir)
    evid = evidence_files or []
    if (exp_dir / "metrics" / "summary.json").is_file():
        evid = list(dict.fromkeys(evid + ["metrics/summary.json"]))

    lines = [
        f"# {eid} — {title or hypothesis[:60]}",
        f"- status: open",
        f"- created: {_utc_now()}",
        f"- git: {git.get('sha') or 'unknown'} dirty={git.get('dirty')}",
        f"- links: plan={plan_id or '-'} node=- thread_claim=- paper_refs=[]",
        "",
        "## Hypothesis",
        "",
        hypothesis or "_(missing)_",
        "",
        "## Pre-locked bars (crux-style)",
        "",
    ]
    for b in use_bars:
        lines.append(f"- [ ] {b}")
    lines.extend(
        [
            "",
            "## Experiment",
            "",
            f"- change: {change or '_(describe data/model/train pillar)_'}",
            f"- command_or_run: _(fill)_",
            f"- evidence_files: {json.dumps(evid, ensure_ascii=False)}",
            "",
            "## Finding",
            "",
            "- mechanical_verdict: inconclusive",
            "- narrative:",
        ]
    )
    if narrative:
        for n in narrative:
            lines.append(f"  - {n}")
    elif metrics:
        pv = metrics.get("primary_value")
        pm = metrics.get("primary_metric")
        lines.append(
            f"  - latest metrics snapshot: `{pm}={pv}` "
            f"(status open until verify; locus=metrics/summary.json)"
        )
    else:
        lines.append("  - _(pending verify)_")
    lines.extend(
        [
            "- lesson:",
            "",
            "## Next",
            "",
            f"- decision: {decision}",
            "- proposed_plans: []",
            "",
        ]
    )
    path = lb / "entries" / f"{eid}.md"
    path.write_text("\n".join(lines), encoding="utf-8")

    _append_log(lb, f"## {eid} created\n- title: {title}\n- hypothesis: {hypothesis}\n")
    return {"entry_id": eid, "path": str(path), "git": git}


def _load_metrics(exp_dir: Path) -> dict[str, Any]:
    for rel in ("metrics/summary.json", "metrics/metrics.json"):
        p = Path(exp_dir) / rel
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError:
                return {}
    return {}


def _append_log(lb: Path, chunk: str) -> None:
    log = lb / "log.md"
    prev = log.read_text(encoding="utf-8") if log.is_file() else ""
    log.write_text(prev + f"\n{_utc_now()}\n{chunk}\n", encoding="utf-8")


def parse_bars(entry_text: str) -> list[dict[str, Any]]:
    bars = []
    in_bars = False
    for line in entry_text.splitlines():
        if line.strip().startswith("## Pre-locked bars"):
            in_bars = True
            continue
        if in_bars and line.startswith("## "):
            break
        if not in_bars:
            continue
        m = _BAR_LINE.match(line)
        if m:
            mark = m.group(2).lower()
            bars.append(
                {
                    "text": m.group(4).strip(),
                    "mark": mark,
                    "met": mark == "x",
                    "na": mark == "-",
                }
            )
    return bars


def mechanical_verdict(bars: list[dict[str, Any]]) -> str:
    active = [b for b in bars if not b.get("na")]
    if not active:
        return "inconclusive"
    mets = sum(1 for b in active if b.get("met"))
    if mets == len(active):
        return "supported"
    if mets == 0:
        return "refuted"
    return "partial"


def apply_bar_marks_from_metrics(
    entry_path: Path,
    metrics: dict[str, Any],
    *,
    auto_mark: bool = True,
) -> str:
    """Optionally tick bars when metrics.target_met / primary matches simple '>=' patterns."""
    text = entry_path.read_text(encoding="utf-8")
    if not auto_mark:
        return text
    thr = None
    if isinstance(metrics.get("target_score"), dict):
        thr = metrics["target_score"].get("threshold")
    thr = metrics.get("threshold", thr)
    primary = metrics.get("primary_value")
    target_met = metrics.get("target_met")

    def repl(m: re.Match[str]) -> str:
        body = m.group(4).strip()
        mark = m.group(2)
        if mark.lower() in ("x", "-"):
            return m.group(0)
        # Heuristic: if target_met true → check first unmet bar; if false leave
        if target_met is True:
            return f"{m.group(1)}[x]{m.group(3)}{body}"
        if target_met is False:
            return f"{m.group(1)}[ ]{m.group(3)}{body}"
        if primary is not None and thr is not None and ">=" in body.replace("≥", ">="):
            try:
                if float(primary) >= float(thr):
                    return f"{m.group(1)}[x]{m.group(3)}{body}"
            except (TypeError, ValueError):
                pass
        return m.group(0)

    # Only rewrite inside bars section
    parts = text.split("## Pre-locked bars")
    if len(parts) < 2:
        return text
    head, rest = parts[0], parts[1]
    sec_parts = rest.split("\n## ", 1)
    bar_sec = sec_parts[0]
    tail = ("\n## " + sec_parts[1]) if len(sec_parts) > 1 else ""
    bar_sec2 = _BAR_LINE.sub(repl, bar_sec)
    return head + "## Pre-locked bars" + bar_sec2 + tail


def verify_entry(
    exp_dir: Path,
    entry_id: str,
    *,
    auto_mark: bool = True,
) -> dict[str, Any]:
    exp_dir = Path(exp_dir)
    lb = labbook_dir(exp_dir)
    path = lb / "entries" / f"{entry_id}.md"
    if not path.is_file():
        return {"ok": False, "error": f"missing entry {entry_id}"}

    metrics = _load_metrics(exp_dir)
    text = apply_bar_marks_from_metrics(path, metrics, auto_mark=auto_mark)
    path.write_text(text, encoding="utf-8")
    bars = parse_bars(text)
    verdict = mechanical_verdict(bars)

    # Registry / metrics presence gate
    issues: list[str] = []
    if not metrics:
        issues.append("no metrics/summary.json — cannot cite numeric findings")
    # Scan narrative for bare numbers without locus hint
    if "## Finding" in text:
        finding = text.split("## Finding", 1)[1].split("## ", 1)[0]
        if re.search(r"\d+\.\d+", finding) and "locus=" not in finding and "metrics/" not in finding:
            if "registry" not in finding.lower():
                issues.append("numeric tokens in Finding without metrics/ or locus= hint")

    status = "verified" if verdict == "supported" and not issues else (
        "refuted" if verdict == "refuted" else "open"
    )
    if verdict == "partial":
        status = "open"

    # Update entry fields
    text2 = re.sub(r"^- status:.*$", f"- status: {status}", text, count=1, flags=re.M)
    text2 = re.sub(
        r"^- mechanical_verdict:.*$",
        f"- mechanical_verdict: {verdict}",
        text2,
        count=1,
        flags=re.M,
    )
    path.write_text(text2, encoding="utf-8")

    report = {
        "ok": verdict == "supported" and not issues,
        "entry_id": entry_id,
        "verdict": verdict,
        "status": status,
        "bars": bars,
        "issues": issues,
        "metrics_present": bool(metrics),
        "primary_value": metrics.get("primary_value"),
        "primary_metric": metrics.get("primary_metric"),
        "target_met": metrics.get("target_met"),
    }
    (lb / "verify" / f"{entry_id}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # TSV row upsert
    _upsert_tsv(
        lb,
        {
            "entry_id": entry_id,
            "status": status,
            "verdict": verdict,
            "plan_id": _field(text2, "plan=") or "",
            "metric": str(metrics.get("primary_metric") or ""),
            "value": str(metrics.get("primary_value") if metrics.get("primary_value") is not None else ""),
            "git_sha": (_git_snapshot(exp_dir).get("sha") or ""),
            "created": _utc_now(),
            "title": path.stem,
        },
    )
    _append_log(lb, f"## {entry_id} verify\n- verdict: {verdict}\n- issues: {issues}\n")
    return report


def _field(text: str, key: str) -> str | None:
    for line in text.splitlines():
        if key in line and "links:" in line:
            # plan=P2 inside links line
            m = re.search(rf"{re.escape(key)}([^\s]+)", line)
            if m:
                return m.group(1).strip()
    return None


def _upsert_tsv(lb: Path, row: dict[str, str]) -> None:
    tsv = lb / "results.tsv"
    fields = [
        "entry_id",
        "status",
        "verdict",
        "plan_id",
        "metric",
        "value",
        "git_sha",
        "created",
        "title",
    ]
    rows: list[dict[str, str]] = []
    if tsv.is_file():
        with tsv.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for r in reader:
                if r.get("entry_id") != row["entry_id"]:
                    rows.append({k: r.get(k) or "" for k in fields})
    rows.append({k: row.get(k) or "" for k in fields})
    with tsv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def synthesize(exp_dir: Path, *, hypothesis: str = "") -> dict[str, Any]:
    """Rebuild INDEX.md + findings.md + research-state (labnote-aware)."""
    from .exp_reflect import build_findings  # local package

    exp_dir = Path(exp_dir)
    lb = labbook_dir(exp_dir)
    entries = sorted((lb / "entries").glob("E*.md")) if (lb / "entries").is_dir() else []

    idx = [
        f"# Labbook index — {exp_dir.name}",
        "",
        f"_Updated: {_utc_now()}_",
        "",
        "## Entries",
        "",
        "| id | status | verdict | file |",
        "|----|--------|---------|------|",
    ]
    verified_n = 0
    for p in entries:
        text = p.read_text(encoding="utf-8")
        status_m = re.search(r"^- status:\s*(\S+)", text, re.M)
        verd_m = re.search(r"^- mechanical_verdict:\s*(\S+)", text, re.M)
        status = status_m.group(1) if status_m else "?"
        verd = verd_m.group(1) if verd_m else "?"
        if status == "verified":
            verified_n += 1
        idx.append(f"| {p.stem} | {status} | {verd} | `{p.name}` |")
    idx.extend(["", f"Verified entries: **{verified_n}** / {len(entries)}", ""])
    if (lb / "config.md").is_file():
        idx.extend(["## Config", "", "See `labbook/config.md` (bars locked).", ""])
    (lb / "INDEX.md").write_text("\n".join(idx), encoding="utf-8")

    findings = build_findings(exp_dir, hypothesis=hypothesis)
    # Append labbook section into findings
    extra = [
        "",
        "## Labbook",
        "",
        f"- entries: {len(entries)}; verified: {verified_n}",
        f"- index: `labbook/INDEX.md`",
        "",
    ]
    fp = Path(findings["findings_path"])
    fp.write_text(fp.read_text(encoding="utf-8") + "\n".join(extra), encoding="utf-8")

    state_path = Path(findings["state_path"])
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        state = {}
    state.setdefault("labbook", {})
    state["labbook"].update(
        {
            "entries": len(entries),
            "verified": verified_n,
            "index": str(lb / "INDEX.md"),
            "updated_at": _utc_now(),
        }
    )
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "index": str(lb / "INDEX.md"),
        "findings_path": findings["findings_path"],
        "state_path": str(state_path),
        "entries": len(entries),
        "verified": verified_n,
    }


def status(exp_dir: Path) -> dict[str, Any]:
    exp_dir = Path(exp_dir)
    lb = labbook_dir(exp_dir)
    entries = list((lb / "entries").glob("E*.md")) if (lb / "entries").is_dir() else []
    dead = (exp_dir / "trace" / "dead_ends.md").is_file()
    metrics = _load_metrics(exp_dir)
    return {
        "exp_dir": str(exp_dir),
        "labbook_ready": (lb / "config.md").is_file(),
        "entries": len(entries),
        "has_dead_ends": dead,
        "target_met": metrics.get("target_met"),
        "primary": {
            "metric": metrics.get("primary_metric"),
            "value": metrics.get("primary_value"),
        },
        "suggest_next": _suggest_next(metrics, len(entries), dead),
    }


def _suggest_next(metrics: dict[str, Any], n_entries: int, has_dead: bool) -> str:
    if metrics.get("target_met") is True and n_entries:
        return "synthesize + sync-exp; consider Thread evidence accept"
    if not n_entries:
        return "labnote init → append first H→E→F after a run"
    if metrics.get("target_met") is False:
        return "Decide new plans; read dead_ends; optional /exp_loop slice"
    if has_dead:
        return "Avoid dead_end lessons; prefer ablation on best tree node"
    return "verify latest entry then synthesize"


def research_signals(exp_dir: Path) -> dict[str, Any]:
    """Gather phase for /labnote_loop."""
    exp_dir = Path(exp_dir)
    from .exp_reflect import collect_exp_signals

    sig = collect_exp_signals(exp_dir)
    sig["labnote_status"] = status(exp_dir)
    sig["git"] = _git_snapshot(exp_dir)
    return sig
