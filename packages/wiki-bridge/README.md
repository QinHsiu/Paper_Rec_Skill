# wiki-bridge

Sync Paper_Rec structured reports into **content/wiki/pages** (Git Markdown), experiments into **content/exp**, and Cognitive Threads into **content/threads**.

## Install

```bash
cd packages/wiki-bridge
pip install -e .
```

## Commands

```bash
# Papers
python -m wiki_bridge.cli sync-report \
  --wiki-root ../.. \
  --report ./examples/sample_report.json \
  --query-id demo \
  --mode query_chinese \
  --mark-reading \
  --thread mm-llm-alignment

# Experiments
python -m wiki_bridge.cli sync-exp \
  --wiki-root ../.. \
  --report ./examples/sample_exp_report.json \
  --thread mm-llm-alignment

# Cognitive Threads
python -m wiki_bridge.cli thread-create --wiki-root ../.. --title "..." --hypothesis "..."
python -m wiki_bridge.cli thread-list --wiki-root ../..
python -m wiki_bridge.cli thread-show --wiki-root ../.. --id mm-llm-alignment
python -m wiki_bridge.cli thread-link-paper --wiki-root ../.. --thread mm-llm-alignment --path keyword/year/slug
python -m wiki_bridge.cli thread-link-exp --wiki-root ../.. --thread mm-llm-alignment --exp-id my-exp
python -m wiki_bridge.cli thread-delta --wiki-root ../.. --id mm-llm-alignment --mode auto
python -m wiki_bridge.cli thread-claim --wiki-root ../.. --id mm-llm-alignment

# Thread template marketplace
python -m wiki_bridge.cli thread-template-list --wiki-root ../.. --seed
python -m wiki_bridge.cli thread-template-import --wiki-root ../.. --template rag-evaluation
python -m wiki_bridge.cli thread-template-export --wiki-root ../.. --thread mm-llm-alignment

python -m wiki_bridge.cli rebuild-index --wiki-root ../..
```

`--wiki-root` may be the workspace root (`Paper_Rec_Skill`), `content/`, or `content/wiki/pages`.

`sync-report --thread` scores papers into the cognitive ledger (`gate: suggested` by default). Add `--auto-link` to accept membership when `R ≥ --auto-link-threshold` (default 0.75).

## Path layout

- Papers: `content/wiki/pages/<keyword>/<year>/<slug>/README.md`
- Experiments: `content/exp/<id>/` + `pages/_exp/<id>/`
- Threads: `content/threads/<id>/thread.json` + `events.jsonl`
- Templates: `content/thread-templates/<id>/` (`template.json` + `thread.json`)

Contract: [`docs/THREAD_DESIGN.md`](../../docs/THREAD_DESIGN.md).  
Bots (Feishu / Telegram / WeCom / QQ): [`docs/BOTS.md`](../../docs/BOTS.md).
