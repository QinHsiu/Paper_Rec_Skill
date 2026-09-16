from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.wiki_filters import apply_filters, iter_wiki_pages, match_meta, parse_wiki_query
from wiki_bridge.writer import resolve_content_root


def _page(root: Path, kw: str, year: int, slug: str, title: str, tags: str, body: str = "", pdf: bool = False):
    d = resolve_content_root(root) / kw / str(year) / slug
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        f"---\ntitle: {title}\nyear: {year}\ntags: [{tags}]\nkeyword: {kw}\nsummary: {title} summary\n---\n\n{body}\n",
        encoding="utf-8",
    )
    if pdf:
        (d / "paper.pdf").write_bytes(b"%PDF-1.4")


def _wiki(tmp_path: Path) -> Path:
    root = tmp_path / "wiki"
    _page(root, "retrieval", 2024, "dense-a", "Dense Transformer Retrieval", "transformer, dense", pdf=True)
    _page(root, "retrieval", 2022, "bm25-b", "BM25 Sparse Baseline", "sparse", body="uses a transformer reranker")
    _page(root, "survey", 2023, "survey-c", "A Survey of Transformer Retrieval", "transformer, survey")
    return root


def test_iter_pages_reads_frontmatter_and_pdf_flag(tmp_path):
    pages = list(iter_wiki_pages(_wiki(tmp_path)))
    assert len(pages) == 3
    dense = next(p for p in pages if p["path"].endswith("dense-a"))
    assert dense["meta"]["title"] == "Dense Transformer Retrieval" and dense["has_pdf"] is True


def test_apply_must_dt_and_exclusion_with_reasons(tmp_path):
    out = apply_filters(_wiki(tmp_path), "+transformer -survey dt>=2023")
    assert out["scanned_n"] == 3 and out["matched_n"] == 1
    m = out["matched"][0]
    assert m["path"].endswith("dense-a") and m["year"] == 2024
    assert set(m["reasons"]) == {"must:transformer", "not:survey", "dt>=2023"}


def test_fulltext_matches_body_only_when_enabled(tmp_path):
    root = _wiki(tmp_path)
    assert {m["path"].split("/")[-1] for m in apply_filters(root, "+reranker")["matched"]} == set()
    assert {m["path"].split("/")[-1] for m in apply_filters(root, "+reranker", fulltext=True)["matched"]} == {"bm25-b"}


def test_file_pdf_limit_and_order(tmp_path):
    root = _wiki(tmp_path)
    assert [m["path"].split("/")[-1] for m in apply_filters(root, "file:pdf")["matched"]] == ["dense-a"]
    out = apply_filters(root, "transformer", limit=1)  # dense-a + survey-c (bm25-b only has it in body)
    assert out["matched_n"] == 2 and len(out["matched"]) == 1 and out["truncated"] is True
    assert out["matched"][0]["year"] == 2024  # year desc


def test_missing_root_is_empty_not_error(tmp_path):
    out = apply_filters(tmp_path / "nope", "+x")
    assert out["scanned_n"] == 0 and out["matched"] == []


def test_apply_filters_non_numeric_year_defaults_zero(tmp_path):
    root = tmp_path / "wiki"
    d = resolve_content_root(root) / "retrieval" / "unknown" / "nd-paper"
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        "---\ntitle: ND Paper\nyear: n.d.\ntags: [x]\nkeyword: retrieval\n---\n\n",
        encoding="utf-8",
    )
    out = apply_filters(root, "")
    assert out["matched_n"] == 1
    assert out["matched"][0]["year"] == 0


def test_date_filter_rejects_missing_year():
    f = parse_wiki_query("dt>=2023")
    assert match_meta({"title": "x"}, f) is False
    assert match_meta({"title": "x", "year": ""}, f) is False
    assert match_meta({"title": "x", "year": 2024}, f) is True
