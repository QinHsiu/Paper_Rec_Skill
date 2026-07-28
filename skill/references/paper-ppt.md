# Paper deep-read → PPT (`/ppt`)

Anti-hallucination + slide contracts + **three-layer QA** + **Paper_Rec closed loop**.

## Positioning (它无我有 · 它有我优)

| Axis | Typical competitors | This skill |
|------|---------------------|------------|
| Evidence | Tags or QA alone | Tags **and** content/structural/visual QA gates |
| Delivery | PPTX **or** outline | Marp + speaker notes + PPTX + `asset_manifest.json` |
| Figures | Optional extract | `slides+fig` inventory + caption binding + optional `/draw` |
| Context | Single PDF session | Wiki `fulltext` · Thread takeaways · claim/evidence · related-work |
| After deck | Stop | Optional sync note → thread gap / next `/exp_*` |

Do **not** compete only on “prettier slides”; win on **traceable group-meeting packs inside the research OS**.

## Evidence tags (required)

| Tag | Meaning |
|-----|---------|
| `[原文]` / `[Source]` | Bound to PDF/abstract/HTML; cite page/section/fig if known |
| `[归纳]` / `[Inference]` | Synthesis only; never invent numbers / venues / baselines |
| `[未找到]` / `[Missing]` | Absent in sources — say so |

Numbers: only `[原文]` + locus, else `[未找到]`.

## Paper type → analysis lens

| Type | Emphasize |
|------|-----------|
| DL / LLM | Task I/O, architecture, training, inference, ablations |
| Theory / algorithm | Formal problem, steps, complexity, assumptions |
| Systems | Components, latency/throughput, comparisons |
| Empirical | Design, data, stats, threats to validity |
| Survey | Scope, taxonomy, axes, open problems |

## Modes & duration presets

| Mode | Alias | Output |
|------|-------|--------|
| `quick` | 速览 | Meta + 3 contributions + 1 limit (chat) |
| `standard` | 精读 | Full deep-read + evidence tags |
| `extended` | 前作 / 脉络 | `standard` + self-cite / prior-work map **from this PDF only** |
| `slides` | 组会 / ppt | `standard` + Marp + notes + QA + optional PPTX |
| `slides+fig` | 带图 | `slides` + figure inventory (+ extract when feasible) |

Natural triggers (`组会PPT` / `精读转PPT`) → `slides`.

### Duration → slide budget (它有我优: venue-aware length)

| Preset | Flag | Minutes | Slides |
|--------|------|---------|--------|
| `meeting` | default 组会 | 10–15 | 8–12 (cap 14) |
| `journal-club` | `club` | 20–30 | 12–16 |
| `spotlight` | `spotlight` | 5–8 | 6–9 |
| `oral` | `oral` | 15–20 | 14–18 |

One idea per slide; body bullets ≤ 5; no walls of text.

## Closed-loop hooks (它无我有)

Before drafting slides, **Gather** in order:

1. Wiki page / `fulltext.md` if `path` or arXiv matches library (`/wiki pdf` · `pdf-fetch` if needed).
2. Active `thread:<id>` → inject hypothesis, open claims/gaps into **Takeaways for us**.
3. If thread has `paper_refs` / matrix → optional 1-slide “vs our line”.
4. After QA pass: offer `thread-evidence-add` / gap note; never auto-mutate thread without ask.

## Deep-read sections (`standard`+)

1. Meta — title, authors, venue/year, links  
2. Problem & motivation  
3. Method (names/equations only if in source)  
4. Experiments (metrics `[原文]`)  
5. Strengths & limits  
6. **Takeaways for us** — prefer thread-linked; else 3 generic why-care bullets  

`extended`: add **Prior-work map** (self-cites / lineage) strictly from this paper’s bibliography — no invented external narrative.

## Figure inventory (`slides+fig`)

Write `figures/inventory.md`:

| fig_id | caption (short) | page/source | used_on_slide | status |
|--------|-----------------|-------------|-----------------|--------|
| F1 | … | p.4 / PDF | 7 | `embedded` \| `caption_only` \| `missing` |

Rules:

- Prefer real PDF assets under `figures/`; if extract fails → `caption_only` + path note.  
- Never hallucinate a plot. Optional: suggest `/draw` from **user** metrics for *our* experiments (not the paper’s fake redraw).

## Slide deck + speaker notes

Marp front matter:

```markdown
---
marp: true
paginate: true
title: "<paper title>"
---
```

Per slide:

```markdown
## Title

- bullet

<!--
SPEAKER: 20–40s oral note; cite [原文] locus for any number spoken
SOURCE: Sec/Fig/Table …
-->
```

### Default skeleton (`meeting`)

| # | Slide |
|---|--------|
| 1 | Title |
| 2 | Why this paper |
| 3 | Problem setup |
| 4–5 | Method |
| 6 | Setup / data |
| 7–8 | Results (+ fig if any) |
| 9 | Ablation (iff in paper) |
| 10 | Limits |
| 11 | Discussion Qs |
| 12 | Links + **Our thread takeaways** |

## Persist layout

```
content/wiki/pages/<keyword>/<year>/<slug>/slides/   # preferred
  deep_read.md
  slides.md
  qa_report.md
  asset_manifest.json
  figures/inventory.md
  figures/*                 # optional extracts
  deck.pptx                 # optional

content/presentations/<slug>/   # fallback if no wiki path
  ...
```

### `asset_manifest.json`

```json
{
  "slug": "",
  "source": "arxiv: | path: | url:",
  "mode": "slides+fig",
  "preset": "meeting",
  "thread_id": null,
  "files": ["deep_read.md", "slides.md", "qa_report.md"],
  "qa": { "content": "pass|fail", "structural": "pass|fail", "visual": "pass|fail" },
  "metrics_unchecked": []
}
```

## Three-layer QA (absorb Paper2PPT; gate before “done”)

Write `qa_report.md`. **All three must be `pass`** (or explicit `waive:<reason>` by user).

### 1) Content QA

- Every spoken/slide number has `[原文]` locus or listed under `metrics_unchecked`.  
- No causal overclaim beyond paper.  
- Limits slide not empty.

### 2) Structural QA

- Slide count in preset band; title slide present; one idea / slide.  
- Speaker notes present on ≥80% content slides.  
- `asset_manifest.json` lists all artifacts.

### 3) Visual QA (heuristic)

- Bullets ≤ 5; title ≤ 12 words.  
- If `slides+fig`: each `embedded` fig referenced by a slide; no orphan binaries.  
- PPTX exported **or** install note recorded (not silent skip).

## PPTX export

```bash
python skill/scripts/md_slides_to_pptx.py \
  --input <dir>/slides.md \
  --out <dir>/deck.pptx
```

Parses `SPEAKER:` HTML comments into PowerPoint notes. Needs `python-pptx`.

## Verify checklist

- [ ] Evidence tags clean; no fabricated metrics  
- [ ] Duration preset respected  
- [ ] `qa_report.md` three gates pass/waive  
- [ ] Thread takeaways filled when `thread:` set  
- [ ] Paths returned: deep_read / slides / qa / manifest / pptx?
