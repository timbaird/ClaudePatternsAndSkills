---
name: upscale-image
version: 1.0.0
description: |
  Deterministic Pillow image upscaler to an exact print-resolution size. Takes a
  source image and produces a print-resolution copy at an exact target size (e.g.
  5175x2625 at 300 DPI for an 8.5x8.5 full-bleed spread): Lanczos resample +
  cover-fit centre-crop + DPI stamp. No model, no network, no API key — same
  input+params give the same pixels.
allowed-tools:
  - Bash
---

# upscale-image

> **⚠ This skill has Python dependencies — one-time setup per machine.**
> It needs the packages in [`requirements.txt`](requirements.txt) (Pillow). Before first use, create a
> **virtualenv inside this skill folder** (if `.venv/` isn't already here) and install the requirements
> into it:
>
> ```bash
> # from the project root (the umbrella root in a multi-repo project)
> python -m venv .claude/skills/upscale-image/.venv
> .claude/skills/upscale-image/.venv/Scripts/python -m pip install -r .claude/skills/upscale-image/requirements.txt   # Windows
> .claude/skills/upscale-image/.venv/bin/python     -m pip install -r .claude/skills/upscale-image/requirements.txt   # macOS/Linux
> ```
>
> Then **invoke the skill with the venv's Python** (not the system `python`):
>
> ```bash
> .claude/skills/upscale-image/.venv/Scripts/python .claude/skills/upscale-image/upscale.py <input> --out <dir> --width 5175 --height 2625
> ```
>
> The `.venv/` is **gitignored** (machine-specific binaries); `requirements.txt` is the committed
> manifest. The script fails with this exact setup hint if Pillow is missing. Full convention:
> `docs/skill-dependencies.md` (vendored into every project).

## What it does

Given a source image and a target size, it: opens → converts RGB → Lanczos-resizes to **cover** the
target → centre-crops to the exact `width x height` → saves a lossless PNG stamped at `--dpi`. Cover-fit
means a slightly different source aspect is absorbed by a small symmetric crop (the bleed area), never
letterbox bars.

## Parameters

| Flag | Required | Meaning |
|---|---|---|
| `input` | yes | source image path |
| `--out` | yes | output folder (created if absent) |
| `--width` / `--height` | yes | exact target pixel size (e.g. 5175 x 2625) |
| `--dpi` | no (300) | DPI metadata stamped into the file |
| `--name` | no | output filename stem (default: the input's stem) → `<name>.png` |

Prints a `RESULT {...}` json line (in/out size, scale factor, saved path).

## Notes

- **Deterministic** — pure Lanczos geometry; no model, no randomness, no network.
- **Tests** — run with the venv python: `.claude/skills/upscale-image/.venv/Scripts/python .claude/skills/upscale-image/tests.py`
  (geometry helpers + a real Pillow round-trip).
- **Print target example** — an 8.5x8.5 full-bleed spread at 300 DPI is 5175 x 2625 px; upscaling a
  ~1456 x 720 screen-res source to that is ~3.6x. Quality at high upscale factors depends on the source
  art — judge the print proof.
