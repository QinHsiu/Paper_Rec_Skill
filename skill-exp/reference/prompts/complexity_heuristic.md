---SYSTEM---
You are an expert ML engineer. Score solution complexity as a BASELINE HEURISTIC only
(Exp_Sandbox must NOT use this as the primary selector — ForeAgent shows complexity heuristics ≈ random).
Output JSON only.

---USER---
Analyze the following solution / plan and score 1-10 on:
1. code_engineering_score
2. model_arch_score
3. data_pipeline_score

Solution:
{code_snippet}

Respond ONLY with:
{{"code_engineering_score": <int>, "model_arch_score": <int>, "data_pipeline_score": <int>, "reasoning": "<brief>"}}
