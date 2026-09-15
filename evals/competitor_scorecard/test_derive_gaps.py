import json
from pathlib import Path

from derive_gaps import derive_gaps, render_gap_markdown

HERE = Path(__file__).resolve().parent


def test_derive_includes_pass5_criticals():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    gaps = derive_gaps(data)
    dims = {g["dimension"] for g in gaps}
    for must in ("b_fig_vlm", "b_parallel_deep", "b_citation_trust", "b_al_stop"):
        assert must in dims, must
    assert any(g["severity"] == "Critical" and g["wave"] == "W1" for g in gaps)


def test_render_gap_markdown_has_table():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    md = render_gap_markdown(derive_gaps(data))
    assert "| Critical |" in md or "|Critical|" in md.replace(" ", "")
    assert "fig-review" in md
