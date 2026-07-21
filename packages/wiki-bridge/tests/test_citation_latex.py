"""Offline tests for citation_verify + latex_export (no network)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wiki_bridge.citation_verify import (  # noqa: E402
    VerifyStatus,
    filter_bibtex,
    parse_bibtex_entries,
    title_similarity,
    verify_bibtex,
)
from wiki_bridge.latex_export import export_latex_pack, markdown_to_latex  # noqa: E402


def test_parse_and_similarity() -> None:
    bib = """
@article{Good2024abc,
  title = {Attention Is All You Need},
  author = {Vaswani and others},
  year = {2017},
  eprint = {1706.03762},
}
@misc{Fake2099xyz,
  title = {Completely Fabricated Quantum Banana Networks},
  author = {Nobody},
  year = {2099},
}
"""
    entries = parse_bibtex_entries(bib)
    assert len(entries) == 2
    assert entries[0]["key"] == "Good2024abc"
    assert title_similarity("Attention Is All You Need", "Attention is all you need") >= 0.8
    assert title_similarity("Attention Is All You Need", "Banana Networks") < 0.5


def test_filter_hallucinated() -> None:
    from wiki_bridge.citation_verify import CitationResult, VerificationReport

    bib = "@misc{A, title={T},}\n\n@misc{B, title={U},}\n"
    report = VerificationReport(total=2, hallucinated=1, verified=1)
    report.results = [
        CitationResult("A", "T", VerifyStatus.VERIFIED, 0.9, "doi"),
        CitationResult("B", "U", VerifyStatus.HALLUCINATED, 0.2, "openalex_title"),
    ]
    cleaned = filter_bibtex(bib, report)
    assert "A," in cleaned or "@misc{A" in cleaned
    assert "B," not in cleaned and "@misc{B" not in cleaned


def test_latex_export_offline() -> None:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "01_intro.md").write_text("# Intro\n\nWe cite [Good2024abc].\n", encoding="utf-8")
        (d / "references.bib").write_text("@misc{Good2024abc, title={T},}\n", encoding="utf-8")
        out = export_latex_pack(d, venue="neurips", title="Demo")
        main = Path(out["main_tex"])
        assert main.is_file()
        tex = main.read_text(encoding="utf-8")
        assert r"\cite{Good2024abc}" in tex
        assert r"\section{" in tex or "Intro" in tex
        assert Path(out["references_bib"]).is_file()


def test_markdown_to_latex_escapes() -> None:
    tex = markdown_to_latex("## Method\n\nUse 100% accuracy & $x_1$.\n", title="T&T")
    assert r"\%" in tex and r"\&" in tex


if __name__ == "__main__":
    test_parse_and_similarity()
    test_filter_hallucinated()
    test_latex_export_offline()
    test_markdown_to_latex_escapes()
    # offline integrity: empty bib
    r = verify_bibtex("")
    assert r.total == 0 and r.integrity_score == 1.0
    print("OK citation_verify + latex_export offline tests")
