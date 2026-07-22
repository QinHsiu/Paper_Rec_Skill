# Examples — Multi-Agent Lab

## Create a run

```text
/lab_run
title: OCR label-clean chase
hypothesis: Cleaning handwritten_pinyin labels raises F1 without global drop
target_score:
  task: handwriting_ocr
  eval_set: test_handwriting_v2
  metric: F1
  threshold: 0.92
thread: mm-llm-alignment
models:
  fast: gpt-4.1-mini   # example names — use whatever the host provides
  standard: gpt-4.1
  deep: o3
```

## Status

```text
/lab_status
```

## Python ledger (optional)

```python
from pathlib import Path
from reference.orchestrator import init_lab_run, status_summary, mark_task

root = Path("../content")
info = init_lab_run(root, title="demo", hypothesis="h", thread_id="mm-llm-alignment")
print(status_summary(root, info["run_id"]))
# After Retrieve finishes:
# mark_task(root, info["run_id"], task_id, status="done", result={"paper_n": 12})
```
