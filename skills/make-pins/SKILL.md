---
name: make-pins
version: 1.0.0
description: |
  Deterministic 2:3 (1000×1500) Pinterest pin from a scene still + a headline — Pinterest's preferred
  aspect ratio. Blurred-fill layout (the scene in a centre band; a blurred enlarged copy fills top/bottom
  and holds the text), a headline up top + optional CTA/handle at the bottom. Plain text only (a rounded
  font renders emoji as tofu — put emoji in the pin's typed description). The pin's destination LINK is
  set when you post it, not baked into the image. Brand is data (text colour, font, CTA, handle are
  params). Pure Pillow — no LLM, no network; same args build the same pin.
allowed-tools:
  - Bash
---

# make-pins

Turn a scene still into a **2:3 Pinterest pin** with a headline. The scene sits in a centre band; a
blurred enlarged copy fills the top/bottom bands and holds the text.

> **⚠ Python dependency — one-time setup per machine.** Needs [`requirements.txt`](requirements.txt)
> (`Pillow`). From the repo root:
>
> ```bash
> python3 -m venv .claude/skills/make-pins/.venv
> .claude/skills/make-pins/.venv/bin/python -m pip install -r .claude/skills/make-pins/requirements.txt
> ```
>
> `.venv/` is gitignored. Full convention: [docs/skill-dependencies.md](../../docs/skill-dependencies.md).

## Run

```bash
.claude/skills/make-pins/.venv/bin/python .claude/skills/make-pins/make_pins.py \
  --scene scene.png --title "Cozy Rainy Lofi to Study" \
  --cta "Full mix on YouTube" --handle "@yourchannel" \
  --out pin_01.jpg
```

## Parameters

| Flag | Default | Meaning |
|---|---|---|
| `--scene` | required | source scene image |
| `--title` | required | headline (plain text, no emoji) |
| `--out` | required | output `.jpg` (2:3) |
| `--cta` | — | bottom call-to-action (omit → none) |
| `--handle` | — | brand line under the CTA (omit → none) |
| `--font` | Pillow built-in | TrueType font path |
| `--text-color` | `239,227,207` (cream) | text colour `R,G,B` |
| `--width` / `--height` | `1000` / `1500` | pin size (2:3) |

## Notes

- **Deterministic + free** — pure Pillow; re-run freely. Prints `RESULT saved <path> (W×H)`.
- **Set the link at post time** — Pinterest is the platform that carries a clickable destination; put the
  target URL on the pin when you post it (it isn't part of the image).
- **Tests** — `.venv/bin/python tests.py`: `parse_rgb` + render round-trips (exact 2:3 size, wide/square
  scenes both fill the frame, empty CTA/handle, custom dimensions, and that the centre band is sharper
  than the blurred edges). They use Pillow's built-in font, so they run with no external asset.
