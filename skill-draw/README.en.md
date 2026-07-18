# Plot_Draw (EN)

`/draw` skill: **data path + description** → paper-ready PDF/PNG. Auto-picks chart type via `lib.select_chart` when unspecified.

Implementation is entirely under [`lib/`](lib/) (no external plot repo). Venue presets: `--venue cvpr|icml|neurips|acl|nature` ([`lib/venues.py`](lib/venues.py)).

```bash
cd skill-draw
pip install -r requirements.txt
python -m lib.cli --data <path> --desc "..." --out <stem> --venue cvpr
```

See [SKILL.md](SKILL.md).
