# Idea / workshop topic stub (AI-Scientist-v2)

Use when seeding a Cognitive Thread from a vague interest (not a finished paper).

```markdown
# Title: <working title>

## Keywords
k1, k2, k3

## TL;DR
≤2 sentences

## Abstract
1 short paragraph — problem, gap, proposed angle (no fake results)

## Reflections (optional, --num-reflections ≤ 3)
1. What would falsify this idea?
2. What related-work pack should Module 2 open first?
3. Minimal experiment that would change the TL;DR?
```

Then: `thread-create` with hypothesis = TL;DR; keywords from the Keywords line; optional `seed_queries` from reflection #2.
