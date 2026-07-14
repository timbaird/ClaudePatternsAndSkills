---
name: thumbnail
version: 1.0.0
description: |
  Deterministic YouTube-thumbnail compositor (Pillow) — one hero/scene image + a title → a 1280×720
  JPEG, in one of two house-template LAYOUTS. `band`: a fixed translucent title band across the bottom
  with an auto-fit, auto-contrast title, a soft shade, and an optional corner wordmark (great for a
  branded, recognisable channel look; `--variants N` sweeps the crop for a human to pick the framing).
  `caption`: a shadowed title (+ optional subtitle) bottom-left over an optional dark scrim for bright
  scenes. Brand is DATA — colours, font, wordmark, sizes are all parameters; nothing is tied to a
  specific channel. Cover-fit + centre-crop (no distortion). No LLM, no network — same args, same image.
allowed-tools:
  - Bash
---

# thumbnail

Compose a consistent, recognisable YouTube thumbnail from a per-video hero/scene image + a title. The
*rendering* is deterministic tooling; the recognisable **template** is what makes a channel read at a
glance. Two layouts cover the common house styles:

- **`band`** — a fixed translucent title band across the bottom, an **auto-fit + auto-contrast** title
  (dark on a light band, white on a dark one), a soft shade rising into the band so art never fights the
  title, and an optional **corner wordmark**. The band colour is a parameter (e.g. a per-item signature
  colour). `--variants N` sweeps the **crop** and writes N candidates for a human to pick the framing.
- **`caption`** — a shadowed **title** (+ optional **subtitle**) set bottom-left, over an optional dark
  bottom **scrim** for bright scenes where light text would otherwise wash out.

> **⚠ Python dependency — one-time setup per machine.** Needs [`requirements.txt`](requirements.txt)
> (`Pillow`). From the repo root:
>
> ```bash
> python3 -m venv .claude/skills/thumbnail/.venv
> .claude/skills/thumbnail/.venv/bin/python -m pip install -r .claude/skills/thumbnail/requirements.txt
> ```
>
> `.venv/` is gitignored; `requirements.txt` is the committed manifest. Full convention:
> [docs/skill-dependencies.md](../../docs/skill-dependencies.md).

## Run it

```bash
# band layout (branded)
.claude/skills/thumbnail/.venv/bin/python .claude/skills/thumbnail/thumb.py \
  --image hero.png --title "Episode Title" --layout band \
  --font brand.ttf --band-color 255,200,70 --wordmark "My Channel" \
  --out thumbnail.jpg

# caption layout (scene + shadowed caption)
… thumb.py --image scene.png --title "Cabin Study" --subtitle "1 hour of calm" \
  --layout caption --scrim --out thumbnail.jpg
```

`--image` also accepts `--hero` / `--scene` as aliases. `--font` is optional — omit it and Pillow's
built-in font is used (fine for a quick render; pass a brand TrueType font for the real look).

## Parameters

| Flag | Layout | Meaning |
|---|---|---|
| `--image` / `--hero` / `--scene` | both | source image (cover-fit + centre-cropped to the frame) |
| `--title` | both | title text |
| `--out` | both | output `.jpg` (or a dir, with `--variants`) |
| `--layout` | both | `band` (default) or `caption` |
| `--font` | both | TrueType font path; omit → Pillow's built-in font |
| `--width` / `--height` | both | frame size (default `1280`×`720`) |
| `--focus-y` | both | vertical crop bias `0`=top..`1`=bottom (lower favours faces near the top) |
| `--band-color` | band | band colour `R,G,B` |
| `--ink` | band | dark text/contrast colour `R,G,B` |
| `--band-alpha` / `--band-h` | band | band opacity `0..1` / band height px |
| `--wordmark` | band | fixed corner wordmark (omit → none) |
| `--variants N` | band | render N crop candidates into `--out` (a dir) for a human to pick |
| `--subtitle` | caption | small line under the title |
| `--scrim` | caption | dark bottom scrim for bright scenes |
| `--title-size` / `--subtitle-size` | caption | text sizes |
| `--caption-color` | caption | caption text colour `R,G,B` |

## Notes

- **Deterministic** — same args → same pixels; no model, no network.
- **1280×720 default** = the YouTube thumbnail spec (under the 2MB cap at quality 90). Override
  `--width`/`--height` for other still sizes; for a 2:3 Pinterest pin or a 9:16 short use the dedicated
  `make-pins` / `make-short` skills.
- **Tests** — `.venv/bin/python tests.py`: pure helpers (`parse_rgb`, `cover_fit`, `fit_font`) + render
  round-trips for both layouts (exact size, under 2MB, auto-fit, auto-contrast, the scrim genuinely
  darkens, crop candidates). They use Pillow's built-in font, so they run with no external asset.
