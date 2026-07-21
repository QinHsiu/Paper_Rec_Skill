# Exp workspace starter (Curie-inspired)

Minimal layout for a new experiment id:

```text
content/exp/<id>/
  question.txt          # research / debugging question (1 paragraph)
  context/              # notes, prior reports, constraints
  scripts/              # user-owned train/eval entrypoints (paths only)
  plans/                # P*.md three-pillar plans
  metrics/              # curves / tables for /draw
  figures/              # /draw outputs
  trace/
    dead_ends.md        # required on failed mini-verify
  task_notes.yaml       # optional AgentLaboratory-style constraints
```

Bootstrap: copy `question.txt` + empty dirs; do not invent scripts — only wire paths the user provides.
