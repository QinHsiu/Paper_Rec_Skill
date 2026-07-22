# Model routing / 模型分级

Host runtime (Cursor / Claude / Codex / OpenClaw) must map tiers to concrete models.
**Never invent API keys** — only use user-provided slots.

| Tier | When | Example use |
|------|------|-------------|
| **fast** | Latency-sensitive, mechanical | emit task cards, JSON format, `rank-intent` strip, file checks, screen labels, status |
| **standard** | Balanced judgment | retrieve rewrite, plan draft, mini-verify, critique, reflect, draw params |
| **deep** | High-stakes / long-form | Brain dispatch, accept/reject, paper sections, novelty kill-switch |

## Role defaults

| Role | Default tier |
|------|----------------|
| brain | deep |
| retrieve | standard |
| plan | standard |
| verify | standard |
| experiment | standard |
| accept | deep |
| write | deep |
| critique | standard |
| reflect | standard |
| draw | fast |

Override per run in `content/lab/<run_id>/routing.yaml` or via Brain decision.

## Python

```python
from reference.model_routing import recommend_tier
recommend_tier(role="write", task="paper_section")
# → {tier: deep, hint: ...}
```
