# Skill & tool dependencies — the convention

> How importable units (predominantly Python **skills**, but also any agent/tool helper script) declare
> and install third-party dependencies so they're reproducible on any machine. **Most skills are pure
> standard library and need none of this** — it applies only to a skill that imports a third-party
> package.

## The rule

**Prefer pure stdlib.** A skill that can be written with the Python standard library should be — it then
"just runs" anywhere Python 3 exists, zero setup.

**When a skill genuinely needs a third-party package** (e.g. `upscale-image` needs Pillow), it carries
its own dependency setup, self-contained in the skill folder:

1. **`requirements.txt`** in the skill folder — the committed manifest of what it needs (pinned with a
   sensible floor, e.g. `Pillow>=10.0`).
2. **A setup note at the top of `SKILL.md`** — tells whoever runs it to create the venv (if absent) and
   install the requirements, with the exact commands.
3. **A per-skill virtualenv** at `<skill>/.venv/` — created locally, **gitignored** (machine-specific
   binaries; only `requirements.txt` is committed). Isolated from system Python and from other skills.
   It is **never vendored** — it is recreated in each project that installs the skill.
4. **An import guard** at the top of the script — a `try/except ImportError` that exits with the venv
   setup hint instead of a raw traceback (the new-machine case).
5. **Invoke with the venv's Python**, not the system `python`:
   - Windows: `<skill>/.venv/Scripts/python <skill>/script.py …`
   - macOS/Linux: `<skill>/.venv/bin/python <skill>/script.py …`
   Any agent or doc that calls the skill uses this, so it runs against the right environment.

## Canonical example

The **`upscale-image`** skill is the reference implementation — copy its shape for any new
dependency-carrying skill: `requirements.txt` (Pillow), the SKILL.md setup note, the gitignored
`.venv/`, the `try/except` import guard in `upscale.py`, and the venv-python invocation.

## Runtime prerequisite — Python 3

All of the above assumes a working **Python 3** in the environment. The SessionStart preflight hook
`.claude/hooks/ensure-python.mjs` checks for it at session start (Node-based, so it doesn't depend on
the very thing it verifies): silent when a usable Python ≥3.9 is on PATH, and on a miss it surfaces
install guidance into the session so Claude can help — the same defensive pattern as the import guard,
one level up. The hook **ships in every project** (so this reference always resolves); it is **wired**
into `settings.json` only when the project actually carries a Python skill.

## Why this shape

- **Copyable machine** — the dependency setup travels *with* the skill folder; clone it, make the venv,
  install the manifest, run. No hidden global state.
- **Isolation** — a per-skill venv avoids version conflicts between skills and never pollutes system Python.
- **Fail loud, fail helpful** — the import guard (and the preflight hook) turn "missing dependency" from a
  cryptic traceback into a copy-paste fix.
