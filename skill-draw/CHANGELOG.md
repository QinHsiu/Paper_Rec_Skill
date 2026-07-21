# Changelog · plot-draw

## 1.2.1

- Step 0 input→chart/diagram decision table (AI-Research-SKILLs academic-plotting)

## 1.2.0

- Venue style presets: `lib/venues.py` (`cvpr|icml|neurips|acl|nature|default`)
- `draw(..., venue=)` and CLI `--venue`; figsize/linewidth follow preset

## 1.1.0

- Self-contained `lib/` (style, charts, io, select, draw, cli) — no `../plot_demo` import
- Slim parameterized APIs; headless Agg; PDF+PNG
- Docs/catalog/palettes point at `lib/` only

## 1.0.0

- Initial `/draw` skill with chart catalog and academic palettes
