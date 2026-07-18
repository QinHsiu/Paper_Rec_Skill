# Color & style · `lib/style.py`

Self-contained academic palette (inspired by common paper figures; **no external repo import**).

| Role | Hex |
|------|-----|
| Ours | `#FF6347` (tomato) |
| Series cycle | blue → green → orange → tomato → royalblue → peru → gray → maroon |
| Heatmap | `YlOrRd` / `Blues` |

Markers: `s o D X ^ v p * +` — **Ours** prefers `X` / `*`.  
Bars: white edge + hatch for grayscale print.

Configured in `lib/style.apply_style()` (`pdf.fonttype=42`, Times New Roman + CJK fallback).
