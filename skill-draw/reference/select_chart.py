"""Re-export selectors from lib (compat for old doc links)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.select_chart import (  # noqa: E402
    ChartDecision,
    DataSchema,
    infer_schema_from_obj,
    select_chart,
)

__all__ = ["ChartDecision", "DataSchema", "infer_schema_from_obj", "select_chart"]
