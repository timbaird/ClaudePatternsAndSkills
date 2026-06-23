# upscale-image · v1.0.0

A standalone, drop-in skill: a **deterministic Pillow image upscaler** that resizes a source image to an
exact target pixel size (Lanczos resample + cover-fit centre-crop + DPI stamp) — no model, no network,
no API key, same input+params → same pixels. The classic use is producing a print-resolution export
(e.g. 5175×2625 @ 300 DPI for an 8.5×8.5 full-bleed spread), but it is fully general.

## Dependency-carrying skill

Unlike the stdlib-only skills in this library, `upscale-image` needs a **third-party package** (Pillow),
so it follows the **skill-dependencies convention** (`docs/skill-dependencies.md`) — it is the canonical
example of that pattern:

- `requirements.txt` — the committed manifest (`Pillow>=10.0`).
- A **setup note** at the top of `SKILL.md` — create a per-skill `.venv/` and install the manifest.
- A **per-skill `.venv/`** — created on install, **gitignored** (machine-specific binaries; never
  vendored — it is recreated in each project that uses the skill).
- An **import guard** in `upscale.py` — exits with the venv setup hint instead of a raw traceback.
- **Invoke with the venv's Python**, not the system `python`.

The runtime prerequisite (a working Python 3) is checked by the `ensure-python.mjs` SessionStart hook
(`hooks/ensure-repo-memory.mjs`'s sibling) — wired into a project when a Python-dependent skill like
this one is vendored in.

## Files
- `SKILL.md` — the skill (setup note + usage).
- `upscale.py` — the engine (pure-helper geometry + the Pillow op).
- `tests.py` — geometry unit tests + a real Pillow round-trip.
- `requirements.txt` — Pillow manifest.

## Origin & versioning
Internally created (in the KDP-factory project) and centralised here for reuse; **generalised** from its
original framing (dropped the project-specific pipeline/"illustrate step" wording — the engine was
already IP-agnostic). The `version` tracks **our** iteration of the skill.
