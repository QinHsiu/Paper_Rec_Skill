# Examples / 示例

---

## Language Mode Examples / 语言模式示例

### `/query_english`

**Input**:
```
/query_english Recommend papers on LoRA for fine-tuning large language models
```

**Input module output** (English):
- Summary, keywords, rewritten queries — all English
- Report title: `Paper Recommendation Report`

---

### `/query_chinese`

**Input**:
```
/query_chinese 帮我找关于大模型 LoRA 微调的相关论文
```

**Input module output** (Chinese):
- 摘要、关键词、改写检索式 — 全中文
- 国际源附加英文检索词：`LoRA, low-rank adaptation, LLM fine-tuning`
- 报告标题：`论文推荐报告`

---

### `/query_other` — adaptive

**Input A** (detected: Chinese):
```
/query_other 多模态大模型对齐的最新进展有哪些？
```
→ Output same as `/query_chinese`; header: `模式：自适应 → 中文`

**Input B** (detected: English):
```
/query_other What are the latest papers on RLHF for alignment?
```
→ Output same as `/query_english`; header: `Mode: Adaptive → English`

**Input C** (detected: mixed):
```
/query_other 帮我找 efficient object detection 在 Jetson 上部署的论文
```
→ Main question is Chinese → Chinese output; English retrieval terms preserved for arXiv/GitHub

---

## Example 1: Short query / 短查询

**User input**:
> Recommend papers on LoRA for fine-tuning large language models

### Module 1 — Input

**Summary**: User seeks parameter-efficient fine-tuning methods, specifically LoRA and related techniques applied to LLMs.

**Keywords**:
```
Primary: LoRA, low-rank adaptation, LLM fine-tuning
Secondary: QLoRA, PEFT, adapter, parameter-efficient
Exclude: full fine-tuning
```

**Rewritten queries**:
- Broad: `parameter-efficient fine-tuning large language models survey`
- Specific: `LoRA low-rank adaptation LLM fine-tuning`
- Keywords: `LoRA QLoRA PEFT arxiv`
- Recent: `LoRA LLM 2024 2025`

### Module 2 — Retrieval (abbreviated)

Top 3 of 50:

| Rank | Title | Source | Final |
|------|-------|--------|-------|
| 1 | LoRA: Low-Rank Adaptation of Large Language Models | arXiv | 9.2 |
| 2 | QLoRA: Efficient Finetuning of Quantized LLMs | NeurIPS | 9.0 |
| 3 | Scaling LoRA for LLM fine-tuning | arXiv | 7.8 |

### Module 3 — Output (one paper sample)

```markdown
### [Rank 1] LoRA: Low-Rank Adaptation of Large Language Models

**Meta / 发表信息**
- **Authors & Affiliation / 团队**: Hu et al. (Microsoft)
- **Date / 时间**: 2021-06
- **Source / 来源**: arXiv (ICLR 2022) | [Link](https://arxiv.org/abs/2106.09685)
- **Type / 类型**: peer-reviewed

**Core Idea / 核心观点**
Injects trainable low-rank matrices into frozen pretrained weights so only a small fraction of parameters are updated during fine-tuning. This preserves base model knowledge while adapting to downstream tasks efficiently.

**Contribution / 核心贡献**
Introduces LoRA as a general PEFT method with no inference latency overhead after merging weights. Demonstrates competitive or superior results vs full fine-tuning on RoBERTa, GPT-2, and GPT-3 scales.

**Metrics / 指标**
On GPT-3 175B, LoRA matches full fine-tuning on WikiSQL and MNLI while reducing trainable parameters by ~10,000×. Reported 3× GPU memory reduction vs full fine-tuning at comparable quality.

**Reference Value / 参考价值**
Foundational reference for any LLM fine-tuning literature review; directly answers the user's LoRA-focused query with widely adopted implementation support.

**Strengths / 强项**
Simple, modular, and supported across Hugging Face and major LLM stacks. Strong empirical validation from small to very large models.

**Weaknesses / 不足之处**
Rank choice and layer targeting require tuning; extreme efficiency gains may need combination with quantization (e.g., QLoRA) for consumer hardware.
```

---

## Example 2: Long query / 长查询

**User input** (truncated):
> I'm building a real-time object detection system for edge devices like Jetson Nano. We need small models with good mAP on COCO but inference under 30ms. We've tried YOLOv8 but want to know if there are newer architectures like DETR variants or efficient backbones that work better on ARM GPUs...

### Module 1 — Input

**Summary** (~150 words): Edge deployment object detection on Jetson-class hardware. Constraints: COCO-level accuracy, <30ms latency, small model size. User has YOLOv8 baseline; open to DETR-family and efficient backbones.

**Keywords**:
```
Primary: edge object detection, real-time, Jetson, COCO mAP
Secondary: YOLO, DETR, efficient backbone, TensorRT, ARM GPU
Exclude: cloud-only, billion-parameter
```

**Rewritten queries**:
- Broad: `efficient real-time object detection edge device COCO`
- Specific: `lightweight DETR YOLO Jetson TensorRT latency`
- Keywords: `edge detection mAP 30ms COCO small model`

### Module 2 — Notes

- Primary: arXiv, PwC (COCO leaderboard), GitHub (`jetson`, `tensorrt`, `yolo`)
- Supplementary: NVIDIA Jetson forums, Kaiming He / ultralytics ecosystem
- Importance boost: papers with Jetson/TensorRT benchmarks

### Module 3 — Output note

For long user context, the **Query Summary** section should restate constraints in 2 sentences before listing papers.

---

## Example 3: Chinese query / 中文查询

**User input**:
> 帮我找几篇关于多模态大模型对齐的最新论文，最好是2024年以后的

### Module 1

**摘要**: 用户关注多模态大模型（MLLM）的对齐方法，时间范围限定为2024年及以后。

**关键词**: 多模态对齐, MLLM alignment, vision-language, RLHF, DPO, instruction tuning

**改写 query**:
- Broad: `multimodal large language model alignment 2024 2025`
- Specific: `MLLM vision-language alignment RLHF DPO`
- Filter: `submittedDate:2024-*`

### Module 3 language

Report body may use Chinese for narrative fields; keep paper titles in original English with optional Chinese gloss.
