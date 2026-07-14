# make-short

Deterministic **9:16 vertical short** (1080×1920) from a 16:9 loop/clip + one audio track + a text hook
— for YouTube Shorts / Reels / TikTok. Blurred-fill reframe (scene in a centre band; blurred enlarged
copy fills top/bottom and holds the text), a top hook + optional bottom CTA/handle, the visual looped to
length, one track snippet with a fade in/out. Reuses long-form assets, so a short costs nothing extra.

Brand is **data** — text colour, font, CTA, handle are parameters. `--font` optional (Pillow built-in
fallback).

**Internally created** (from yt-music-factory). **Dependency-carrying** — Pillow + **ffmpeg** (system
PATH, falling back to the bundled `imageio-ffmpeg`); per-skill gitignored `.venv/`
([skill-dependencies convention](../../docs/skill-dependencies.md)).

- `make_short.py` — the engine (overlay via Pillow; reframe/loop/mux via ffmpeg).
- `tests.py` — pure helpers + command assembly (injected runner) + a real end-to-end render.

See [SKILL.md](SKILL.md) for parameters and usage.
