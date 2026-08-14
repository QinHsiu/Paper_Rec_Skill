#!/usr/bin/env python3
"""Thin wrapper: skill/scripts/deep_search.py → wiki_bridge deep-search."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BRIDGE = _ROOT / "packages" / "wiki-bridge"
if str(_BRIDGE) not in sys.path:
    sys.path.insert(0, str(_BRIDGE))

from wiki_bridge.cli import main


if __name__ == "__main__":
    sys.argv = [sys.argv[0], "deep-search", *sys.argv[1:]]
    raise SystemExit(main())
