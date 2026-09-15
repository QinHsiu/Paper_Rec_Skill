# Gold-set

Offline regression cases for competitor-exceed gates.

## Run

```powershell
python evals/goldset/run_goldset.py
python -m pytest evals/goldset/test_run_goldset.py -v
```

## Families

- `hard_gate` — fabricated metrics blocked
- `citation_fidelity` — uncited claims flagged
- `retrieval` — gold docs in top-k after prerank
- `screening_stop` — N-consecutive irrelevant stops (harness helper until W1)

W0 does not claim beating closed-source SaaS; it locks the gate machinery.
