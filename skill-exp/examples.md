# Examples — exp-sandbox

## 1. Train-set analysis

```text
/exp_analysis train
target_score: ASR WER <= 12% on test_zh_v1
tool/function:
  - sources: data root /mnt/data/asr_zh, train=train.jsonl, eval=test_zh_v1.jsonl
  - open_models: whisper-large-v3 via local vLLM http://127.0.0.1:8000
analysis_tool: none (use default audio stats)
```

Expected: duration/sample-rate histograms, label/text length, noise proxies, quality issues, multi-plans (e.g. filter short clips, balance accents).

---

## 2. Eval badcase analysis

```text
/exp_analysis eval
（当前 checkpoint ckpt-12 在 test_handwriting_v2 上 F1=0.81，目标 0.92）
请聚类 badcase，并给出至少 3 个可验证方案
```

Expected: clusters such as “handwritten pinyin”, “low-res scan”, “rare characters”; ranked plans with mini-val suggestions.

---

## 3. Training only

```text
/exp_training
run config: configs/ocr_v3.yaml
train_infra: ssh gpu-box-3；启动脚本 scripts/train.sh
请监控 train loss 与 val F1，并保存曲线说明
```

---

## 4. Evaluation only

```text
/exp_eval
target_score: OCR F1 >= 0.92 on test_handwriting_v2
checkpoint: outputs/ocr_v3/best.pt
```

---

## 5. Full self-loop

```text
/exp_loop
target_score:
  task: handwriting_ocr
  eval_set: test_handwriting_v2
  metric: F1
  threshold: 0.92
tool/function:
  - train_infra: ...
  - closed_models: [{name: gpt-labeler, use_method: relabel uncertain}]
  - sources: train/val/test paths ...
other_source_model: 可参考 wiki 中 OCR 相关笔记与 HF 开源结果
```

Expected rounds: analysis → multi-plan → Top-1 mini-val → train → eval → iterate → final report.
