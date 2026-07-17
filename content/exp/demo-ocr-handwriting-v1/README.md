---
title: Handwriting OCR — Predict-then-Verify demo
type: experiment
experiment_id: demo-ocr-handwriting-v1
status: done
target_met: true
paper_refs: llm/2025/getting-started
---

# Handwriting OCR — Predict-then-Verify demo

- task: `handwriting_ocr`
- eval_set: `test_handwriting_v2`
- metric: `F1` ≥ `0.92`
- target_met: **True**
- paper_refs: llm/2025/getting-started

### train_loss

- sparkline: `█▅▃▂▂▁▁▁`

- points: [(1, 1.82), (2, 1.41), (3, 1.12), (4, 0.95), (5, 0.81), (6, 0.72), (7, 0.66), (8, 0.61)]

```mermaid
xychart-beta
  title "train_loss"
  x-axis [1, 2, 3, 4, 5, 6, 7, 8]
  line [1.82, 1.41, 1.12, 0.95, 0.81, 0.72, 0.66, 0.61]
```

### val_F1

- sparkline: `▁▃▄▅▆▇▇█`

- points: [(1, 0.62), (2, 0.71), (3, 0.78), (4, 0.84), (5, 0.88), (6, 0.9), (7, 0.92), (8, 0.93)]

```mermaid
xychart-beta
  title "val_F1"
  x-axis [1, 2, 3, 4, 5, 6, 7, 8]
  line [0.62, 0.71, 0.78, 0.84, 0.88, 0.9, 0.92, 0.93]
```

| Metric | Value |
|---|---|
| F1 | 0.93 |
| CER | 0.07 |
| precision | 0.94 |
| recall | 0.92 |

