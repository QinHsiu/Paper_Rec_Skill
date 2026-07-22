"""Tests for arxiv_watch (Atom parse, day partition, watermark, wiki dedup)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.arxiv_watch import (
    harvest_categories,
    index_wiki_arxiv_ids,
    load_state,
    parse_atom_feed,
    run_arxiv_watch,
    save_state,
    write_day_partitions,
)
from wiki_bridge.conventions import PaperRecord
from wiki_bridge.writer import write_paper_page

SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2204.10254v1</id>
    <published>2022-04-21T12:00:00Z</published>
    <title>Paper Alpha Title</title>
    <summary>Alpha abstract here.</summary>
    <author><name>Alice A</name></author>
    <author><name>Bob B</name></author>
    <link title="pdf" href="http://arxiv.org/pdf/2204.10254v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.IR"/>
    <category term="cs.IR"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2204.10230v2</id>
    <published>2022-04-20T12:00:00Z</published>
    <title>Paper Beta Title</title>
    <summary>Beta abstract.</summary>
    <author><name>Carol C</name></author>
    <link title="pdf" href="https://arxiv.org/pdf/2204.10230v2.pdf" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
  </entry>
</feed>
"""


def test_parse_atom_strips_version_and_https():
    docs = parse_atom_feed(SAMPLE_ATOM.encode("utf-8"), source_cat="cs.IR")
    assert len(docs) == 2
    assert docs[0]["arxiv"] == "2204.10254"
    assert docs[0]["published"] == "2022-04-21"
    assert docs[0]["authors"] == ["Alice A", "Bob B"]
    assert docs[0]["paper_link"].startswith("https://")
    assert docs[1]["arxiv"] == "2204.10230"  # v2 stripped


def test_write_day_partitions_merge(tmp_path):
    docs = parse_atom_feed(SAMPLE_ATOM.encode("utf-8"), source_cat="cs.IR")
    written = write_day_partitions(tmp_path, docs)
    assert written["metadata"]
    day_path = tmp_path / "Metadata" / "2022-04-21.json"
    assert day_path.is_file()
    data = json.loads(day_path.read_text(encoding="utf-8"))
    assert any(x["arxiv"] == "2204.10254" for x in data)
    write_day_partitions(tmp_path, docs)
    data2 = json.loads(day_path.read_text(encoding="utf-8"))
    assert len([x for x in data2 if x["arxiv"] == "2204.10254"]) == 1
    link = (tmp_path / "Link" / "2022-04-21.txt").read_text(encoding="utf-8")
    assert "2204.10254" in link


def test_harvest_watermark_and_rrf_dedup():
    def fake_fetch(cat, **kwargs):
        return parse_atom_feed(SAMPLE_ATOM.encode("utf-8"), source_cat=cat)

    with patch("wiki_bridge.arxiv_watch.fetch_cat_page", side_effect=fake_fetch):
        out = harvest_categories(
            ["cs.IR", "cs.CL"],
            last_update_date="2022-04-20",
            max_per_cat=10,
            page_size=10,
            wait_time=0,
        )
    assert out["fused_n"] == 1
    assert out["documents"][0]["arxiv"] == "2204.10254"
    assert out["newest_seen"] == "2022-04-21"


def test_run_watch_persists_watermark_and_skips_wiki_dup(tmp_path):
    wiki = tmp_path / "ws"
    (wiki / "content" / "wiki" / "pages").mkdir(parents=True)
    write_paper_page(
        wiki,
        PaperRecord(title="Paper Alpha Title", year=2022, arxiv="2204.10254", keyword="old"),
    )
    assert "2204.10254" in index_wiki_arxiv_ids(wiki)

    def fake_harvest(cats, **kwargs):
        docs = parse_atom_feed(SAMPLE_ATOM.encode("utf-8"), source_cat="cs.IR")
        return {
            "lanes": {"cs.IR": 2},
            "fused_n": 2,
            "newest_seen": "2022-04-21",
            "watermark": kwargs.get("last_update_date") or "",
            "documents": docs,
            "errors": [],
            "rrf": {"kept_n": 2, "input_n": 2, "rejected_merges": 0},
        }

    state_dir = wiki / "content" / "arxiv_watch"
    with patch("wiki_bridge.arxiv_watch.harvest_categories", side_effect=fake_harvest):
        out = run_arxiv_watch(
            wiki,
            cats=["cs.IR"],
            state_dir=state_dir,
            last_update_date="2022-04-19",
            wait_time=0,
            ingest=False,
            dry_run=False,
        )
    assert out["dup_wiki"] == 1
    assert out["novel_n"] == 1
    assert out["watermark_after"] == "2022-04-21"
    state = json.loads((state_dir / "state.json").read_text(encoding="utf-8"))
    assert state["last_update_date"] == "2022-04-21"
    assert (state_dir / "Metadata" / "2022-04-20.json").is_file()


def test_save_state_roundtrip(tmp_path):
    save_state(tmp_path, {"last_update_date": "2026-07-01", "cats": ["cs.IR"]})
    st = load_state(tmp_path)
    assert st["last_update_date"] == "2026-07-01"
