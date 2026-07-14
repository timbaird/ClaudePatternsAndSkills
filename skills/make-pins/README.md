# make-pins

Deterministic **2:3 (1000×1500) Pinterest pin** from a scene still + a headline. Blurred-fill layout
(scene in a centre band; blurred enlarged copy fills top/bottom and holds the text), a headline up top +
optional CTA/handle at the bottom. The pin's destination link is set at post time, not baked into the
image.

Brand is **data** — text colour, font, CTA, handle are parameters. `--font` optional (Pillow built-in
fallback).

**Internally created** (from yt-music-factory). **Dependency-carrying** (Pillow → per-skill gitignored
`.venv/`, [skill-dependencies convention](../../docs/skill-dependencies.md)).

- `make_pins.py` — the engine (`build_pin` + CLI).
- `tests.py` — pure helper + render round-trips (no external font needed).

See [SKILL.md](SKILL.md) for parameters and usage.
