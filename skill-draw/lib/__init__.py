"""Self-contained plotting library for skill-draw (/draw)."""

from __future__ import annotations

from typing import Any

__all__ = ["draw", "charts", "io_data", "style", "select_chart"]


def __getattr__(name: str) -> Any:
    if name == "draw":
        from .draw import draw as _draw

        return _draw
    if name in ("charts", "io_data", "style", "select_chart"):
        import importlib

        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(name)
