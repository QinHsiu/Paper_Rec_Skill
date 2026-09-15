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

# arXiv category watch (day JSON + watermark; optional ingest)
python -m wiki_bridge.cli arxiv-watch --wiki-root ../.. --cats cs.IR,cs.CL --dry-run
python -m wiki_bridge.cli arxiv-watch --wiki-root ../.. --config ./examples/arxiv_watch_config.json --ingest
```

`--wiki-root` may be the workspace root (`Paper_Rec_Skill`), `content/`, or `content/wiki/pages`.

`arxiv-watch` writes under `content/arxiv_watch/` (`state.json`, `Metadata/YYYY-MM-DD.json`, `Link/YYYY-MM-DD.txt`). `--ingest` creates wiki stubs then runs legal OA `pdf-fetch`→ingest; duplicates skipped via normalized arXiv id / RRF keys.

`sync-report --thread` scores papers into the cognitive ledger (`gate: suggested` by default). Add `--auto-link` to accept membership when `R ≥ --auto-link-threshold` (default 0.75).

## Path layout

- Papers: `content/wiki/pages/<keyword>/<year>/<slug>/README.md`
- Experiments: `content/exp/<id>/` + `pages/_exp/<id>/`
- Threads: `content/threads/<id>/thread.json` + `events.jsonl`
- Templates: `content/thread-templates/<id>/` (`template.json` + `thread.json`)
- arXiv watch: `content/arxiv_watch/` (`state.json`, `Metadata/`, `Link/`)

Contract: [`docs/THREAD_DESIGN.md`](../../docs/THREAD_DESIGN.md).  
Bots (Feishu / Telegram / WeCom / QQ): [`docs/BOTS.md`](../../docs/BOTS.md).

## Trust & screening CLIs (W1)

| Command | Purpose |
|---------|---------|
| `trust-meta --json hits.json [--conflict-ratio 0.30] [--offline]` | Retraction + OpenAlex/S2 citation-count conflict; `unknown` when a source is missing |
| `fig-review --draft ... --use-vlm off\|auto\|required` | Figure/caption/ref consistency; real OpenAI-compatible VLM when key set (`PAPER_REC_VLM_*` / `OPENAI_API_KEY`) |
| `deep-research --topic ... --json hits.json --parallel [--max-concurrent N] [--search-cmd CMD]` | Learnings tree → follow-up queries; concurrent lanes + compression |
| `screen-next --candidates pool.json [--stop-n N] [--stop-max-labels N] [--stop-window W] [--stop-max-relevant R] [--min-labels N]` | Active screening next batch + configurable stoppers |
