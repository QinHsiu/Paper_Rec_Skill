# LitSearch (Paper_Rec adapter)

Official bench: [princeton-nlp/LitSearch](https://huggingface.co/datasets/princeton-nlp/LitSearch) (597 queries · 64,183 docs).

Paper: *LitSearch: A Retrieval Benchmark for Scientific Literature Search*.

## Protocol (Paper_Rec Phase 1A)

| Rule | Choice |
|------|--------|
| Corpus | Official `corpus_clean` only |
| External search | **Off** (no arXiv / S2 / scholar-mcp injection) |
| Methods | `bm25` (lexical baseline) · `prerank` (`wiki_bridge.prerank` = BM25 + recency) |
| Metrics | Recall@{1,5,10} · Hit@{1,5,10} · MRR · nDCG@10 |
| Gold | query field `corpusids` (paper ids in corpus) |

This measures **Paper_Rec’s local ranking stack**, not an end-to-end web search agent.

## Quick start (offline smoke)

No HuggingFace download — uses `fixtures/` (10 docs · 3 queries):

```powershell
$env:PYTHONPATH = "packages\wiki-bridge"
python benchmarks/litsearch/run_litsearch.py --fixture --method bm25
python benchmarks/litsearch/run_litsearch.py --fixture --method prerank
# or CLI:
python -m wiki_bridge.cli litsearch-eval --fixture --method bm25
```

## Full benchmark

```powershell
pip install datasets
$env:PYTHONPATH = "packages\wiki-bridge"
# optional: --limit-queries 50 for a faster subset
python benchmarks/litsearch/run_litsearch.py --method bm25 --out benchmarks/litsearch/runs/bm25_full.json
python benchmarks/litsearch/run_litsearch.py --method prerank --out benchmarks/litsearch/runs/prerank_full.json
```

Cache: `benchmarks/litsearch/cache/` (gitignored). Full corpus ~ tens of thousands of docs; first run downloads from HF.

## Layout

```text
benchmarks/litsearch/
  README.md
  run_litsearch.py
  fixtures/          # offline smoke (committed)
  cache/             # HF cache (ignored)
  runs/              # result JSON (ignored except samples)
```

Core code: `packages/wiki-bridge/wiki_bridge/litsearch_eval.py`.

## Reporting

Paste `metrics_mean` into [`../REPORT.md`](../REPORT.md). Always record:

- git SHA / `VERSION`
- `--method` / `--limit-queries`
- whether run was fixture vs full
