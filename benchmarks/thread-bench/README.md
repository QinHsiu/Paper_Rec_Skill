# Thread-Bench

Evaluates **Cognitive Thread–conditioned ranking**, not daily personalized recommendation (that is PaperFlow-Bench).

## Layout

```text
benchmarks/thread-bench/
  cases/<case_id>/
    thread.json     # fixed thread snapshot
    pool.jsonl      # candidates + gold labels
  README.md
```

### pool.jsonl fields

| Field | Meaning |
|-------|---------|
| `paper_id` | Stable id |
| `title` / `summary` / `tags` / `keyword` | Scoring inputs |
| `relevant` / `oracle_score` | Relevance (≥0.5 or `relevant:true`) |
| `gold_claims` | Claim ids this paper should support |
| `gold_gaps` | Gap keys (`claim_id`) this paper fills |

## Metrics (at K, default 5)

| Metric | Definition |
|--------|------------|
| `recall_at_k` | Relevant papers recalled in Top-K / all relevant |
| `mrr_at_k` | 1 / rank of first relevant in Top-K |
| `claim_coverage_at_k` | Fraction of thread claims with ≥1 gold paper in Top-K |
| `gap_fill_rate_at_k` | Fraction of gaps with ≥1 gold gap-filler in Top-K |

## Run

```powershell
cd packages/wiki-bridge
$env:PYTHONPATH="."
python -m wiki_bridge.cli thread-bench --wiki-root ../.. --k 5
python -m wiki_bridge.cli thread-bench --wiki-root ../.. --case mm-align --k 5 --out ../../benchmarks/thread-bench/last_run.json
```

From repo root:

```powershell
$env:PYTHONPATH="packages\wiki-bridge"
python -m wiki_bridge.cli thread-bench --wiki-root . --k 5
```

## Cases

| Case | Focus |
|------|--------|
| `mm-align` | Multimodal preference / RLHF |
| `rag-eval` | RAG faithfulness metrics |
| `code-agents` | Repo-level code agents |

Add a case by copying a folder under `cases/` and filling `thread.json` + `pool.jsonl`.
