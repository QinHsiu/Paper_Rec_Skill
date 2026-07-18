# Benchmark report (credibility / 公信力)

Public scorecard for **Paper_Rec**. Reproduce from this repo; do not treat marketing screenshots as evidence.

| Field | Value |
|-------|--------|
| Workspace | [`VERSION`](../VERSION) **2.22.0** |
| Full LitSearch run | **2026-07-18** · see CHANGELOG 2.22.0 |
| Scorecard | this file + [`litsearch/fixtures/full_result_summary.json`](litsearch/fixtures/full_result_summary.json) |

## Protocol principles

1. Fixed commit + documented flags.
2. External search **off** unless a row explicitly says compose-with-MCP.
3. Non-goals remain: LaTeX成稿竞赛 · Sci-Hub · second search-MCP product.

## Scoreboard

| Bench | Split | Method | Metric | Score | Notes |
|-------|-------|--------|--------|-------|-------|
| **Thread-Bench** | 3 cases · K=5 | thread R-rank | R@5 / MRR / claim / gap | **1.00 / 1.00 / 1.00 / 1.00** | synthetic; easy ceiling |
| **LitSearch** | fixture (3q×10d) | bm25 | Recall@5 / MRR / nDCG@10 | **1.00 / 1.00 / 1.00** | offline smoke |
| **LitSearch** | fixture (3q×10d) | prerank | Recall@5 / MRR / nDCG@10 | **1.00 / 1.00 / 1.00** | BM25→prerank |
| **LitSearch** | **full** 597×64183 | **bm25** | Recall@5 / nDCG@10 / MRR | **0.452 / 0.397 / 0.363** | Hit@5=**0.459** · primary row |
| **LitSearch** | **full** 597×64183 | **prerank** | Recall@5 / nDCG@10 / MRR | **0.357 / 0.310 / 0.283** | Hit@5=**0.363** · see note below |
| SciNet Path-wise | — | — | — | planned P1 | [`scinet/`](scinet/) stub |
| RWGBench | related_work only | — | — | planned P1 | [`rwgbench/`](rwgbench/) stub |

Committed summary: [`litsearch/fixtures/full_result_summary.json`](litsearch/fixtures/full_result_summary.json).  
Raw runs (gitignored): `benchmarks/litsearch/runs/*_full.json`.

### LitSearch full — detail (2026-07-18)

| Method | Recall@1 | Hit@1 | Recall@5 | Hit@5 | Recall@10 | Hit@10 | nDCG@10 | MRR | wall |
|--------|----------|-------|----------|-------|-----------|--------|--------|-----|------|
| bm25 | 0.269 | 0.275 | **0.452** | **0.459** | 0.537 | 0.548 | **0.397** | **0.363** | ~290s |
| prerank | 0.203 | 0.206 | 0.357 | 0.363 | 0.428 | 0.434 | 0.310 | 0.283 | ~345s |

**Protocol:** `corpus_clean` only · no external arXiv/S2 · inverted BM25 index · `prerank` = BM25 top-500 → `wiki_bridge.prerank` (lexical + recency; citations off).

**Note on prerank &lt; bm25:** `corpus_clean` often lacks reliable `year`; recency boost can reorder true lexical hits downward. On this bench, **report bm25 as the lexical baseline**; treat prerank as a stack experiment until year/cite metadata is richer (e.g. `corpus_s2orc`).

**Context (not a head-to-head claim):** public LitSearch Hit@10 figures in recent literature (e.g. Lacuna ~0.54 / OpenScholar-v3 ~0.42) use their own stacks; our Hit@10 **0.548** (bm25) is in a similar ballpark for a pure lexical run — still not advertising SOTA.

### How to refresh Thread-Bench

```powershell
$env:PYTHONPATH = "packages\wiki-bridge"
python -m wiki_bridge.cli thread-bench --wiki-root . --k 5
```

### How to refresh LitSearch (smoke)

```powershell
$env:PYTHONPATH = "packages\wiki-bridge"
python benchmarks/litsearch/run_litsearch.py --fixture --method bm25
python benchmarks/litsearch/run_litsearch.py --fixture --method prerank
```

### How to refresh LitSearch (full)

```powershell
pip install datasets
$env:PYTHONPATH = "packages\wiki-bridge"
python benchmarks/litsearch/run_litsearch.py --method bm25 --out benchmarks/litsearch/runs/bm25_full.json
python benchmarks/litsearch/run_litsearch.py --method prerank --out benchmarks/litsearch/runs/prerank_full.json
```

Then update this file’s scoreboard + `fixtures/full_result_summary.json`.

## Layout

```text
benchmarks/
  REPORT.md              # this file
  thread-bench/          # Cognitive Thread ranking
  litsearch/             # princeton-nlp/LitSearch adapter
  scinet/                # stub (P1)
  rwgbench/              # stub (P1)
```

## Citation

- LitSearch: Princeton NLP — https://huggingface.co/datasets/princeton-nlp/LitSearch
- Thread-Bench: in-repo synthetic cases (not a published IR dataset)
