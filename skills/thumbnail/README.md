# thumbnail

Deterministic **YouTube-thumbnail compositor** (Pillow) — one hero/scene image + a title → a 1280×720
JPEG, in one of two house-template layouts:

- **`band`** — translucent bottom title band + auto-fit, auto-contrast title + optional corner wordmark;
  `--variants N` sweeps the crop for a human to pick the framing.
- **`caption`** — shadowed title (+ optional subtitle) bottom-left over an optional dark scrim.

Brand is **data** — colours, font, wordmark, sizes are all parameters. Cover-fit + centre-crop (no
distortion). `--font` is optional (falls back to Pillow's built-in font).

**Internally created** (consolidates two channel-specific variants — KDP `thumbnail` + music `make-thumbnail`
— into one parameterised skill). **Dependency-carrying** (Pillow → per-skill gitignored `.venv/`,
[skill-dependencies convention](../../docs/skill-dependencies.md)).

- `thumb.py` — the engine (band + caption layouts; CLI + pure helpers).
- `tests.py` — pure helpers + render round-trips for both layouts (no external font needed).

See [SKILL.md](SKILL.md) for parameters and usage.
