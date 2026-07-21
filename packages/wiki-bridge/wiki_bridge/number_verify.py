"""Whitelist experiment metrics and reject unlisted floats in drafts/LaTeX.

Prevents fabricated Results numbers: every reported float must appear in
``metrics`` / ``summary.json`` (with rounding / ×100 variants).
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

_NUM_RE = re.compile(
    r"(?<![A-Za-z0-9_/])"  # not part of identifier
    r"([+-]?(?:\d+\.\d+|\d+\.|\.\d+|\d+)"
    r"(?:[eE][+-]?\d+)?)"
    r"(?![A-Za-z_/])"
)

# Years / section numbers / common non-metric integers to ignore
_SKIP_INT_RANGE = range(1900, 2101)


def _is_finite(v: float) -> bool:
    return math.isfinite(v)


def _add_variants(registry: dict[float, str], value: float, source: str) -> None:
    if not _is_finite(value):
        return
    registry[value] = source
    for dp in (1, 2, 3, 4):
        rounded = round(value, dp)
        registry.setdefault(rounded, f"{source} (round {dp}dp)")
    if 0.0 < abs(value) <= 1.0:
        pct = value * 100.0
        registry.setdefault(pct, f"{source} (×100)")
        for dp in (1, 2, 3, 4):
            registry.setdefault(round(pct, dp), f"{source} (×100,{dp}dp)")


def _walk_numbers(obj: Any, path: str, registry: dict[float, str]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        _add_variants(registry, float(obj), path)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            _walk_numbers(v, f"{path}.{k}" if path else str(k), registry)
        return
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk_numbers(v, f"{path}[{i}]", registry)


def load_registry(metrics_paths: list[Path]) -> dict[str, Any]:
    registry: dict[float, str] = {}
    loaded: list[str] = []
    for p in metrics_paths:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() == ".json":
            data = json.loads(text)
            _walk_numbers(data, p.name, registry)
            loaded.append(str(p))
        else:
            for m in _NUM_RE.finditer(text):
                try:
                    _add_variants(registry, float(m.group(1)), p.name)
                except ValueError:
                    pass
            loaded.append(str(p))
    return {"values": registry, "sources": loaded, "count": len(registry)}


def extract_reported_numbers(text: str) -> list[float]:
    out: list[float] = []
    for m in _NUM_RE.finditer(text or ""):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if not _is_finite(v):
            continue
        # skip likely years / figure indices
        if abs(v - int(v)) < 1e-12 and int(v) in _SKIP_INT_RANGE:
            continue
        if abs(v - int(v)) < 1e-12 and 0 <= int(v) <= 20:
            continue  # small integers often ranks / counts of sections
        out.append(v)
    return out


def is_verified(value: float, registry: dict[float, str], *, tolerance: float = 0.011) -> bool:
    if value in registry:
        return True
    for known in registry:
        if abs(known - value) <= tolerance * max(1.0, abs(known)):
            return True
    return False


def verify_text(
    text: str,
    registry: dict[float, str],
    *,
    tolerance: float = 0.011,
) -> dict[str, Any]:
    reported = extract_reported_numbers(text)
    ok: list[float] = []
    bad: list[float] = []
    for v in reported:
        if is_verified(v, registry, tolerance=tolerance):
            ok.append(v)
        else:
            bad.append(v)
    return {
        "reported_n": len(reported),
        "verified_n": len(ok),
        "unverified": bad,
        "unverified_n": len(bad),
        "ok": len(bad) == 0,
        "registry_n": len(registry),
    }


def verify_paths(
    draft_paths: list[Path],
    metrics_paths: list[Path],
    *,
    tolerance: float = 0.011,
) -> dict[str, Any]:
    reg = load_registry(metrics_paths)
    chunks: list[str] = []
    for p in draft_paths:
        if p.is_file():
            chunks.append(p.read_text(encoding="utf-8"))
    report = verify_text("\n".join(chunks), reg["values"], tolerance=tolerance)
    report["metrics_sources"] = reg["sources"]
    report["draft_files"] = [str(p) for p in draft_paths if p.is_file()]
    return report


def discover_exp_metrics(exp_dir: Path) -> list[Path]:
    """Common metric locations under ``content/exp/<id>/``."""
    candidates = [
        exp_dir / "metrics" / "summary.json",
        exp_dir / "metrics" / "final.json",
        exp_dir / "eval" / "summary.json",
        exp_dir / "experiment_summary.json",
    ]
    found = [p for p in candidates if p.is_file()]
    metrics = exp_dir / "metrics"
    if metrics.is_dir():
        found.extend(sorted(metrics.glob("*.json")))
    # unique preserve order
    seen: set[str] = set()
    out: list[Path] = []
    for p in found:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out
