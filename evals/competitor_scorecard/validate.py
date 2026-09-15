from __future__ import annotations

from schema import CELL_STATES, CLOSED_COMPETITORS, DIMENSIONS, OSS_COMPETITORS


def validate_scorecard(data: dict) -> list[str]:
    errors: list[str] = []
    comps = data.get("competitors")
    if not isinstance(comps, dict):
        return ["competitors must be an object"]

    expected = set(OSS_COMPETITORS) | set(CLOSED_COMPETITORS)
    missing = expected - set(comps)
    extra = set(comps) - expected
    if missing:
        errors.append(f"missing competitors: {sorted(missing)}")
    if extra:
        errors.append(f"unknown competitors: {sorted(extra)}")

    dim_ids = [d["id"] for d in DIMENSIONS]
    for name, row in comps.items():
        if not isinstance(row, dict):
            errors.append(f"{name}: row must be object")
            continue
        cells = row.get("cells")
        if not isinstance(cells, dict):
            errors.append(f"{name}: missing cells object")
            continue
        for did in dim_ids:
            cell = cells.get(did)
            if not isinstance(cell, dict):
                errors.append(f"{name}.{did}: missing cell")
                continue
            state = cell.get("state")
            if state not in CELL_STATES:
                errors.append(f"{name}.{did}: bad state {state!r}")
            note = cell.get("note")
            if not isinstance(note, str) or not note.strip():
                errors.append(f"{name}.{did}: note required")
            if name in CLOSED_COMPETITORS and cell.get("evidence") != "public-docs":
                errors.append(f"{name}.{did}: closed must evidence=public-docs")
    return errors
