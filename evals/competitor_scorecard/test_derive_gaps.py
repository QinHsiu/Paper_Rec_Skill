import json
from pathlib import Path

from derive_gaps import derive_gaps, render_gap_markdown

HERE = Path(__file__).resolve().parent


def test_no_critical_or_high_gaps_after_w2():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    gaps = derive_gaps(data)
    assert not [g for g in gaps if g["severity"] in ("Critical", "High")], [(g["severity"], g["dimension"]) for g in gaps if g["severity"] in ("Critical", "High")]
    dims = {g["dimension"] for g in gaps}
    for must in ("b_novelty", "b_survey", "c_drift_watch", "c_wiki_filter"):
        assert must not in dims, must


def test_render_gap_markdown_has_table():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    md = render_gap_markdown(derive_gaps(data))
    assert "| Medium |" in md or "|Medium|" in md.replace(" ", "")
    assert "| Critical |" not in md and "| High |" not in md
    assert "Gap Priority" in md
