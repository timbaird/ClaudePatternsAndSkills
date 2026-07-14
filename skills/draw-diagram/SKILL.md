---
name: draw-diagram
version: 1.0.0
description: |
  Author an editable draw.io (.drawio) technical diagram from a simple node/edge
  spec, then render it to PNG with Pillow — no draw.io app, no system binary, same
  input -> same pixels. The .drawio is the single source of truth (anyone can open +
  edit it in draw.io free); the PNG is rendered from it for dropping straight into a
  document or slide. Covers the shapes this skill authors — boxes, ellipse/stadium
  terminators, decision diamonds, ER entity boxes, labelled orthogonal arrows — so
  one spec can express a network/cloud-architecture diagram, a flowchart, or a
  simple ERD; it is not a general draw.io renderer. Edge geometry honours fixed
  ports + waypoints in the file, so hand-edited diagrams re-render true to source.
allowed-tools:
  - Bash
---

# draw-diagram

Generate a labelled box-and-arrow technical diagram (network / cloud architecture / tiers / flow) as
an **editable `.drawio`**, and **render it to PNG with Pillow** so it drops straight into a document —
no draw.io application, no system install, fully cross-platform and headless.

> **⚠ This skill has a Python dependency — one-time setup per machine.**
> It needs [`requirements.txt`](requirements.txt) (Pillow). Before first use, create a **virtualenv
> inside this skill folder** (if `.venv/` isn't already here) and install the requirements:
>
> ```bash
> # from the repo root
> python -m venv .claude/skills/draw-diagram/.venv
> .claude/skills/draw-diagram/.venv/Scripts/python -m pip install -r .claude/skills/draw-diagram/requirements.txt   # Windows
> .claude/skills/draw-diagram/.venv/bin/python     -m pip install -r .claude/skills/draw-diagram/requirements.txt   # macOS/Linux
> ```
>
> Then **invoke with the venv's Python** (not system `python`):
>
> ```bash
> .claude/skills/draw-diagram/.venv/Scripts/python .claude/skills/draw-diagram/draw_diagram.py \
>   --spec <spec.json> --out <diagram.drawio> --png
> ```
>
> `.venv/` is gitignored; `requirements.txt` is the committed manifest. The script fails with this
> exact hint if Pillow is missing. Full convention: `docs/skill-dependencies.md`.

## What it does

1. **`build_drawio(spec)`** (stdlib) writes an editable `.drawio` — rounded colour-coded boxes laid out
   on a grid, with orthogonal labelled connectors.
2. **`render_drawio(.drawio)`** (Pillow) parses that file and renders a PNG (150 DPI × scale). The
   `.drawio` is the **single source of truth** — edit it and re-render, or hand it to someone else.

`--png` renders the PNG next to the `.drawio` (or `--png <path>`).

## The spec

```json
{
  "title": "Small office network",
  "nodes": [
    {"id": "fw",  "label": "Firewall / Router", "row": 1, "col": 1, "fill": "red"},
    {"id": "sw",  "label": "Core Switch",        "row": 2, "col": 1, "fill": "blue"},
    {"id": "pc1", "label": "PC-1\n10.0.0.11",    "row": 3, "col": 0, "fill": "green"}
  ],
  "edges": [
    {"from": "fw", "to": "sw", "label": "LAN"},
    {"from": "sw", "to": "pc1", "label": ""}
  ]
}
```

- **nodes** lay out on a grid by `(row, col)`; a node missing both auto-stacks. `fill` is a palette name
  (`blue`/`green`/`amber`/`grey`/`purple`/`red`) or a `#hex`. `\n` in a label is a line break.
  - optional **`shape`**: `rounded` (default) · `rect` · `ellipse` · `stadium` · `diamond` · `entity`.
    This is what makes one spec express a **network** (boxes), a **flowchart** (`stadium` start/end +
    `diamond` decisions, branch edges labelled Yes/No), or a simple **ERD** (`entity` = name on the
    first line then attributes, left/top-aligned; relationships carry cardinality as the edge `label`).
  - optional **`w`** / **`h`**: per-node size override (e.g. taller `entity` boxes). The grid pitch grows
    to fit the largest node, so tall/wide nodes don't collide.
- **edges** connect node ids; orthogonal routing + arrowhead + optional `label`. Edge endpoints honour
  any **fixed exit/entry ports** and **waypoints** present in the `.drawio` (so a hand-edited diagram
  re-renders true to source); diagrams this skill authors get **explicit ports** written in, so they
  render identically in draw.io and in Pillow.
  - optional **`start`** / **`end`** crow's-foot (ER) endings for ERDs: `one` · `many` · `zero-one` ·
    `zero-many` · `one-many`. Authored as draw.io's native ER arrows (`ERone`/`ERmany`/…), so draw.io
    shows proper crow's foot and Pillow draws the matching tick / circle / foot glyphs.

## Validation + fallback (always offer this)

A generated PNG is **good enough for most diagrams**, but the Pillow renderer is a likeness of the
`.drawio`, not draw.io's own engine. So whenever a diagram is produced, **ask the human if the PNG is
good enough.** If they say no, have them open the `.drawio` in draw.io ([app.diagrams.net](https://app.diagrams.net))
and compare — the answer is one of two things:

- **Rendering problem** — the `.drawio` is *correct* (right boxes, links, labels) but the PNG isn't a
  close-enough likeness. **Fallback: the human exports the PNG straight from draw.io** (File ▸ Export as ▸
  PNG) and uses that. The diagram is right; only our render fell short. *No need to change anything.*
- **Underlying error** — the `.drawio` *itself* is wrong (a missing box, a wrong link). **Fix the spec
  and regenerate** — re-rendering won't help; the source is wrong.

This keeps auto-render the default while guaranteeing a human fallback that never blocks delivery.

## What it renders (and what it doesn't)

- **Covers:** rounded/rect boxes, ellipse/stadium terminators, decision diamonds, ER entity boxes; fill +
  stroke colours; multi-line labels (centred, or left/top-aligned for entities); orthogonal arrows with
  arrowheads + edge labels; fixed exit/entry ports + waypoints honoured from the `.drawio`. Enough for a
  network / cloud-tier diagram, a flowchart, or a simple ERD.
- **Doesn't:** vendor icon stencils (e.g. the AWS service glyphs), gradients/shadows, curved connectors,
  and **obstacle-avoidance routing** — a connector whose path crosses another node draws *behind* it, so
  lay diagrams out to avoid running a line through a box (draw.io's live router detours; this one doesn't).
  For richer notation use the draw.io app + the manual-export fallback.

## Notes

- **Deterministic** — same spec + same `.drawio` → same pixels; no model, no network.
- **Tests** — run with the venv python: `.claude/skills/draw-diagram/.venv/Scripts/python .claude/skills/draw-diagram/tests.py`
  (build/parse/geometry helpers + a real Pillow render round-trip).
