---
name: skill-dependencies-convention
description: How skills declare third-party deps (per-skill gitignored .venv, never vendored) + the universal-doc / universal-hook-file / conditional-wiring split for the Python preflight.
metadata:
  type: project
---

A skill that needs a **third-party package** carries its own setup, self-contained in the skill folder:
`requirements.txt` (committed manifest) + a **per-skill `.venv/`** (gitignored, **never vendored** —
recreated in each consuming project) + a `try/except` import guard that prints the venv setup hint +
**venv-python invocation**. Pure-stdlib skills need none of this. The canonical doc is
`docs/skill-dependencies.md` and the canonical example skill is `upscale-image` (Pillow). Born in the
KDP-factory project; generalised + centralised here.

**Why the venv is never vendored:** it holds machine-specific binaries; only the manifest travels, and
the venv is built on install. (Same spirit as [[memory-hook-is-node]] treating Node as a prerequisite.)

**The universal-doc / universal-hook-file / conditional-wiring split (decided with Tim):**
- `docs/skill-dependencies.md` (the convention) is a **standing doc vendored into EVERY project** by
  `doco-setup`, alongside `doco-structure.md` — "this is how we do skill dependencies, full stop."
- `hooks/ensure-python.mjs` (the Node SessionStart preflight that checks Python ≥3.9 is on PATH) is
  **vendored into every project too** (so the doc's reference to it always resolves) but is **WIRED**
  into `settings.json` **only when the project actually carries a Python skill** — wiring is done by
  `skill-vendoring` (appended to the `hooks.SessionStart` array alongside the memory hook; the array
  holds several). doco-setup ships it unwired.

**How to apply:** see [[docs-surface-conventions]] (docs/ is top-level-only, INDEX is required-reading)
— `skill-dependencies.md` rides the same vendored-doc mechanism as `doco-structure.md`. For a new
dependency-carrying skill, copy `upscale-image`'s shape. See [[vendoring-model]].
