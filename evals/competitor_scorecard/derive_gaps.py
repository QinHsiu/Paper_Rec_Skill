from __future__ import annotations

from collections import defaultdict

_RULES = {
    "b_fig_vlm": ("Critical", "W1", "fig-review"),
    "b_parallel_deep": ("Critical", "W1", "deep-research"),
    "b_citation_trust": ("Critical", "W1", "trust-meta"),
    "b_al_stop": ("Critical", "W1", "screen-next"),
    "b_survey": ("High", "W2", "survey-draft"),
    "b_novelty": ("High", "W2", "novelty-check"),
    "c_drift_watch": ("High", "W2", "thread-delta"),
    "c_wiki_filter": ("High", "W2", "wiki-filter-apply"),
}


def derive_gaps(data: dict) -> list[dict]:
    by_dim: dict[str, list[str]] = defaultdict(list)
    notes: dict[str, str] = {}
    for name, row in data["competitors"].items():
        for did, cell in row["cells"].items():
            if cell.get("state") == "落后":
                by_dim[did].append(name)
                notes.setdefault(did, cell.get("note", ""))
    gaps = []
    for did, comps in sorted(by_dim.items()):
        sev, wave, cli = _RULES.get(did, ("Medium", "W3", "tbd-cli"))
        if cli == "tbd-cli":
            cli = did.replace("_", "-")
        gaps.append(
            {
                "id": f"gap-{did}",
                "severity": sev,
                "dimension": did,
                "competitors": comps,
                "target_cli": cli,
                "wave": wave,
                "rationale": notes.get(did, ""),
            }
        )
    order = {"Critical": 0, "High": 1, "Medium": 2}
    gaps.sort(key=lambda g: (order.get(g["severity"], 9), g["dimension"]))
    return gaps


def render_gap_markdown(gaps: list[dict]) -> str:
    lines = [
        "# Gap Priority",
        "",
        "Derived from `evals/competitor_scorecard/data.json` cells with state `落后`.",
        "",
        "| Severity | Dimension | Wave | Target CLI | Competitors | Rationale |",
        "|----------|-----------|------|------------|-------------|-----------|",
    ]
    for g in gaps:
        comps = ", ".join(g["competitors"][:6])
        if len(g["competitors"]) > 6:
            comps += ", …"
        rat = g["rationale"].replace("|", "/")
        lines.append(
            f"| {g['severity']} | {g['dimension']} | {g['wave']} | `{g['target_cli']}` | {comps} | {rat} |"
        )
    lines.append("")
    lines.append("## Wave mapping")
    lines.append("")
    lines.append("- **W1:** Critical trust/depth engines only.")
    lines.append("- **W2:** High coverage + thread.")
    lines.append("- **W3:** Medium polish + prove narrative.")
    lines.append("")
    lines.append("SP1+ plans must not start until this file exists and Critical rows are acknowledged.")
    lines.append("")
    return "\n".join(lines)
