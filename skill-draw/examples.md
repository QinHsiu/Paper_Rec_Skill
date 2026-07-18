# Examples · /draw

## 1. Auto (training curves)

```text
/draw
data: content/exp/demo-ocr-handwriting-v1/metrics/curves.json
desc: train_loss 与 val_F1 随 step 变化，双曲线，突出收敛
out: content/exp/demo-ocr-handwriting-v1/figures
format: pdf,png
```

Expected: `chart=line`, tomato/blue markers, PDF+PNG under `figures/`.

## 2. Forced multi-bar

```text
/draw multi_bar
data: ./bench/hr20_by_data_ratio.csv
desc: Model1/2/3/Ours 在 20%–100% 数据量上的 HR@20，论文主结果图
```

## 3. Eval confusion

```text
/draw heatmap
data: content/exp/run-2/metrics/confusion.json
desc: 测试集混淆矩阵，行真实列预测
palette: heatmap_warm
```

## 4. Label distribution (analysis)

```text
/draw
data: /path/to/ocr/train_label_counts.json
desc: 训练标签类别分布，检查长尾
```

Expected auto: `bar` (or `violin` if raw score lists).

## 5. From exp skill

```text
/exp_training
…（训练中）
请按 /draw 规范输出 loss 与 val 曲线到 content/exp/<id>/figures
```
