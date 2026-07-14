---
name: make-short
version: 1.0.0
description: |
  Deterministic 9:16 vertical short (1080×1920) from an existing 16:9 loop/clip + one audio track + a
  text hook — for YouTube Shorts / Instagram Reels / TikTok. Blurred-fill reframe (the 16:9 scene in a
  centre band; a blurred, enlarged copy fills top/bottom and holds the text), a top hook line + optional
  bottom CTA/handle, the visual looped to length, one track snippet with a fade in/out. Reuses long-form
  assets, so a short costs nothing extra to generate. Brand is data (text colour, font, CTA, handle are
  params). Local ffmpeg + Pillow — no LLM, no network; same args build the same short.
allowed-tools:
  - Bash
---

# make-short

Turn a 16:9 loop/clip you already have into a **9:16 vertical short** with a burned-in hook, over one
music track. The scene sits in a centre band; a blurred enlarged copy fills the top/bottom bands (so the
scene stays clear) and holds the text.

## Dependencies

- **ffmpeg** — resolved from the system `ffmpeg` on PATH, falling back to the **bundled
  `imageio-ffmpeg`** binary (in `requirements.txt`), so it works even without a system install.
- **Pillow** — the venv dependency (for the text overlay). Per the skill-dependencies convention
  (`docs/skill-dependencies.md`): committed `requirements.txt` + per-skill gitignored `.venv/`.

**One-time setup** (from the repo root):

```bash
python3 -m venv .claude/skills/make-short/.venv
.claude/skills/make-short/.venv/bin/python -m pip install -r .claude/skills/make-short/requirements.txt
```

## Run

```bash
.claude/skills/make-short/.venv/bin/python .claude/skills/make-short/make_short.py \
  --loop clip_16x9.mp4 --audio track.mp3 \
  --hook "1 hour of rain to study to" \
  --cta "Full mix on YouTube" --handle "@yourchannel" \
  --out short_01.mp4
```

## Parameters

| Flag | Default | Meaning |
|---|---|---|
| `--loop` | required | 16:9 loop/clip to reframe |
| `--audio` | required | track to snippet |
| `--hook` | required | top hook line (plain text, **no emoji** — this font renders them as tofu; put emoji in the platform caption) |
| `--out` | required | output `.mp4` (1080×1920) |
| `--cta` | — | bottom call-to-action (omit → none) |
| `--handle` | — | handle under the CTA (omit → none) |
| `--font` | Pillow built-in | TrueType font path |
| `--text-color` | `239,227,207` (cream) | overlay text colour `R,G,B` |
| `--duration` | `70` | seconds (keeping it >60 leaves shorts eligible for TikTok Creator Rewards; still within YouTube Shorts ≤3 min and Reels ≤90 s) |
| `--audio-start` | `20` | seconds into the track to start the snippet |

## Notes

- **Deterministic + free** — local ffmpeg + Pillow; re-run freely. Prints `RESULT saved <path> (1080x1920, Ns)`.
- **Making a set distinct** — vary the `--hook` (and the `--audio` snippet) per short while keeping the
  loop visual constant; the constant visual is the brand thread, the varying hook/track is the difference.
- **Tests** — `.venv/bin/python tests.py`: `render_overlay`, `parse_rgb`, `find_ffmpeg`, the ffmpeg
  command assembly (via an injected runner, no ffmpeg needed), and a real end-to-end render that
  generates its own test clip + tone (skips if no ffmpeg is resolvable).
