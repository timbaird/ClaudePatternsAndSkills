# library-standards-linter · v1.0.0 (created 2026-06-19)

## Purpose
**The mechanical half of the library-standards audit.** A deterministic linter that checks each reusable
library under `libraries/` against the *machine-decidable* parts of [docs/library-standards.md](../../../docs/library-standards.md)
— required files, src layout, naming consistency, `pyproject` fields, package `__version__`, SPDX
headers, the required `docs/` files, and absence of a per-repo `documentation-structure.md` or memory
surface. No model in the loop: same input always gives the same findings. It stops where judgment begins
— chiefly *whether a deviation is a sanctioned divergence* — leaving that to a human or a future
`library-standards-auditor` agent that consumes its `--json` output.

## Provenance — internally created
Internally created (originated in the FCM project; generalized for reuse) — not vendored from a third
party. The version tracks *our* iteration. Pure Python standard library (`tomllib` for pyproject parsing,
present in Python 3.11+) — no third-party dependencies, so it runs anywhere Python 3.11+ does and ships
complete with its own tests.

## Stack scope — Python/Evennia instance
This linter encodes the **Python/Evennia instantiation** of `library-standards.md` (checks `pyproject`
fields, src layout, package `__version__`, and `SPDX-License-Identifier: BSD-3-Clause` headers). Reuse
as-is on the same stack; for a different **license** / language / layout, edit the constants at the top of
`lint_library.py` (`SPDX`, the license string, the required files) or write a sibling checker. The
generic, stack-agnostic standard is `library-standards.md` (in the `library-setup` pattern); this skill
is one concrete checker for it.

## What's in the folder
- `SKILL.md` — the model/user-facing contract: what it checks, how to run it, how to read the output.
- `lint_library.py` — the linter. Each library is read once into a `LibContext`; every check is a
  single-purpose `LibContext -> list[Finding]` validator in the `CHECKS` list.
- `tests.py` — stdlib `unittest`: a compliant synthetic library is clean; each check in isolation; the
  placeholder-satisfies-structure calibration; migrations excluded from SPDX. Zero dependencies.

## How it works
Discovers every directory under `libraries/` that carries a `pyproject.toml` (auxiliary fixture repos
have none and are skipped), runs the structural checks per library, and reports findings carrying
`check`, `severity` (`error` / `warn`), `library`, `path`, `message`. Exit code is non-zero when any
`error` exists (or any `warn` under `--strict`), so it doubles as a CI gate.

**Calibration:** structural folders (`tests/`, `docs/archive/`) are checked at folder-presence level — a
placeholder satisfies them; `examples/` is optional. The linter surfaces a gap; resolving it (add the
structure, placeholder OK, or document the divergence in `CLAUDE.md`) is the judgment layer's call.

## Running the tests
```bash
python .claude/skills/library-standards-linter/tests.py
```
Run it after any change to `lint_library.py`.

## Deploying
Copy the `library-standards-linter/` folder into a project's `.claude/skills/`. Adjust the rule set in
`lint_library.py` to match that project's library conventions. No dependencies beyond Python 3.11+.
