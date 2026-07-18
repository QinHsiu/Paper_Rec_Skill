"""Load tables / curves / matrices for /draw (self-contained)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def load_any(path: str | Path) -> Any:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    suf = path.suffix.lower()
    if suf == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if suf in {".csv", ".tsv"}:
        import csv

        delim = "\t" if suf == ".tsv" else ","
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f, delimiter=delim))
        return rows
    if suf == ".npy":
        return np.load(path)
    if suf in {".npz", ".npzz"}:
        return np.load(path)
    raise ValueError(f"unsupported format: {suf}")


def as_curves(obj: Any) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Normalize {name: {steps|x, values|y}} or list-of-dicts."""
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    if isinstance(obj, dict) and "curves" in obj:
        obj = obj["curves"]
    if isinstance(obj, dict):
        for name, series in obj.items():
            if not isinstance(series, dict):
                continue
            y = np.asarray(series.get("values") or series.get("y") or [], dtype=float)
            x = series.get("steps") or series.get("x")
            x = np.asarray(x if x is not None else range(1, len(y) + 1), dtype=float)
            if len(y):
                out[str(name)] = (x, y)
    return out


def as_matrix(obj: Any) -> np.ndarray:
    if isinstance(obj, dict):
        m = obj.get("matrix") or obj.get("confusion") or obj.get("data")
        if m is None:
            raise ValueError("JSON has no matrix/confusion/data field")
        return np.asarray(m, dtype=float)
    return np.asarray(obj, dtype=float)


def table_columns(rows: list[dict]) -> tuple[list[str], dict[str, list]]:
    if not rows:
        return [], {}
    keys = list(rows[0].keys())
    cols = {k: [] for k in keys}
    for r in rows:
        for k in keys:
            cols[k].append(r.get(k))
    return keys, cols
