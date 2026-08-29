# Method: ICIO

**id:** `icio` · **load this file before drafting when ICIO is selected.**

## When

翻译、摘要、格式转换、简单改写等**轻量变换**。

## Slots

| Slot | Meaning |
|------|---------|
| **I** Instruction | 要做什么 |
| **C** Context | 背景（领域、读者） |
| **I₂** Input Data | 待处理原文（完整粘贴） |
| **O** Output Indicator | 语言、长度、格式 |

## Fill template

```text
【ICIO】
Instruction：…
Context：…
Input Data：
<<<
…原文…
>>>
Output Indicator：…
```

## Draft procedure

1. Emit ICIO block（Input 可截断展示，但起草须基于全文）。
2. Output **only** the transformed result unless user asks otherwise.
3. Footer: `framework: ICIO`.

## Mini example

```text
Instruction：译为英文摘要
Context：学术语气，面向会议审稿人
Input Data：<<<中文段落>>>
Output Indicator：≤100 words, one paragraph
```
