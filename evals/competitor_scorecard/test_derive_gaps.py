import json
from pathlib import Path

from derive_gaps import derive_gaps, render_gap_markdown

HERE = Path(__file__).resolve().parent


def test_no_critical_gaps_after_w1():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    gaps = derive_gaps(data)
    assert not [g for g in gaps if g["severity"] == "Critical"], [g["dimension"] for g in gaps if g["severity"] == "Critical"]
    dims = {g["dimension"] for g in gaps}
    for must in ("b_fig_vlm", "b_parallel_deep", "b_citation_trust", "b_al_stop"):
        assert must not in dims, must


def test_render_gap_markdown_has_table():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    md = render_gap_markdown(derive_gaps(data))
    assert "| High |" in md or "|High|" in md.replace(" ", "")
    assert "| Critical |" not in md
    assert "Gap Priority" in md
