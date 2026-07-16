# wiki-bridge

Sync Paper_Rec structured reports into **content/wiki/pages** (Git Markdown) and regenerate reading indexes.

## Install

```bash
cd packages/wiki-bridge
pip install -e .
```

## Commands

```bash
python -m wiki_bridge.cli sync-report \
  --wiki-root ../.. \
  --report ./examples/sample_report.json \
  --query-id demo \
  --mode query_chinese \
  --mark-reading

python -m wiki_bridge.cli rebuild-index --wiki-root ../..
```

`--wiki-root` may be the workspace root (`Paper_Rec_Skill`), `content/`, or `content/wiki/pages`.

## Path layout

`content/wiki/pages/<keyword>/<year>/<slug>.md`

Each `sync-report` also updates `content/wiki/pages/<keyword>/README.md` with the `/query_*` command log.
