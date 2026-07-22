"""Verified value registry + hard writing gate for Results floats.

Extends soft ``number-verify``: when ``hard_gate`` is on, unverified Results
floats (or empty registry with numeric Results claims) BLOCK export.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .number_verify import (
    discover_exp_metrics,
    extract_reported_numbers,
    is_verified,
    load_registry,
    verify_text,
)

_RESULTS_HDR = re.compile(
    r"(?im)^(?:\#+\s*)?(?:\d+(\.\d+)*\s+)?(results?|experiments?|evaluation|实验结果|实验|结果)\b.*$"
)
_NEXT_H = re.compile(r"(?im)^\#+\s+")
_POINT = re.compile(
    r"(?i)(achieve[sd]?|obtain[sd]?|reach(?:es|ed)?|report[sd]?|improve[sd]?|"
    r"outperform[sd]?|accuracy|F1|AUC|准确率|达到|提升|优于)\b"
)


def extract_results_body(text: str) -> str:
    lines = (text or "").splitlines()
    out: list[str] = []
    capture = False
    for line in lines:
        if _RESULTS_HDR.search(line.strip()):
            capture = True
            out.append(line)
            continue
        if capture and _NEXT_H.match(line) and not _RESULTS_HDR.search(line.strip()):
            if line.strip().startswith("#"):
                break
        if capture:
            out.append(line)
    return "\n".join(out) if out else ""


def build_verified_registry(metrics_paths: list[Path]) -> dict[str, Any]:
    """Persistable registry artifact (values keyed as strings for JSON)."""
    raw = load_registry(metrics_paths)
    values = {str(k): v for k, v in raw["values"].items()}
    return {
        "version": "1.0",
        "sources": raw["sources"],
        "count": raw["count"],
        "values": values,
        "policy": "Results floats must match registry within tolerance or hard_gate BLOCKS.",
    }


def registry_float_map(reg: dict[str, Any]) -> dict[float, str]:
    out: dict[float, str] = {}
    for k, src in (reg.get("values") or {}).items():
        try:
            out[float(k)] = str(src)
        except (TypeError, ValueError):
            continue
    return out


def persist_registry(exp_dir: Path, metrics_paths: list[Path] | None = None) -> Path:
    paths = metrics_paths or discover_exp_metrics(exp_dir)
    reg = build_verified_registry(paths)
    out = Path(exp_dir) / "metrics" / "verified_registry.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def load_persisted_registry(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def hard_gate(
    text: str,
    registry: dict[float, str],
    *,
    tolerance: float = 0.011,
    results_only: bool = True,
) -> dict[str, Any]:
    """BLOCK if Results numeric claims are not in the verified registry.

    Empty registry + Results numeric claims → BLOCK (zero-values policy).
    Soft verify still reports all floats; hard gate focuses Results section.
    """
    body = extract_results_body(text) if results_only else (text or "")
    if results_only and not body.strip():
        soft = verify_text(text or "", registry, tolerance=tolerance)
        return {
            "ok": True,
            "blocked": False,
            "skipped": True,
            "reason": "no_results_section",
            "soft": soft,
            "unverified": [],
            "unverified_n": 0,
        }

    reported = extract_reported_numbers(body)
    claim_floats: list[float] = []
    for sent in re.split(r"(?<=[.!?。！？])\s+", body):
        if _POINT.search(sent) or re.search(r"\d+\.\d+", sent):
            claim_floats.extend(extract_reported_numbers(sent))
    targets = claim_floats or reported

    unverified: list[float] = []
    for v in targets:
        if not is_verified(v, registry, tolerance=tolerance):
            unverified.append(v)

    empty_reg = len(registry) == 0
    block_empty = empty_reg and len(targets) > 0
    blocked = block_empty or len(unverified) > 0
    reason = (
        "empty_registry_with_results_claims"
        if block_empty
        else ("unverified_results_floats" if unverified else "ok")
    )
    soft = verify_text(text or "", registry, tolerance=tolerance)
    return {
        "ok": not blocked,
        "blocked": blocked,
        "skipped": False,
        "reason": reason,
        "results_float_n": len(targets),
        "unverified": unverified,
        "unverified_n": len(unverified),
        "registry_n": len(registry),
        "soft": soft,
        "policy": "HARD GATE — fix metrics registry or remove fabricated Results floats",
    }


def build_results_table(registry: dict[float, str], *, max_rows: int = 40) -> dict[str, Any]:
    """Emit markdown table rows only from verified values (no invented cells)."""
    rows = []
    by_src: dict[str, list[float]] = {}
    for v, src in registry.items():
        if not math.isfinite(v):
            continue
        by_src.setdefault(src.split(" (")[0], []).append(v)
    lines = ["| Source | Values |", "|--------|--------|"]
    for src, vals in list(by_src.items())[:max_rows]:
        uniq = sorted(set(round(x, 4) for x in vals))[:8]
        cell = ", ".join(str(x) for x in uniq)
        lines.append(f"| `{src}` | {cell} |")
        rows.append({"source": src, "values": uniq})
    return {"markdown": "\n".join(lines), "rows": rows, "ok": True}
