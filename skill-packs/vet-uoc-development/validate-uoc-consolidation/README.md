# validate-uoc-consolidation · v1.0.0 (updated 2026-06-14)

## Purpose
Prove a cluster's `consolidated_uoc.md` references **every** assessable item (PC/FS/PE/KE/AC) from
each source unit **exactly once** — flagging `MISSING`, `UNEXPECTED`, or `DUPLICATED`. It's the
standalone form of the completeness gate that `consolidate-uocs` runs at the end, exposed so an
existing consolidation can be re-checked anytime. It checks **tag coverage, not wording**, and does
**not** build or group a consolidation.

## Prerequisites
- A **Python 3 interpreter** on PATH (`python3`, or `python` / `py -3` on Windows) — standard library only (no venv, no `pip install`).
- Shared script in `.claude/skills/scripts/`: **`validate_consolidated.py`**.
- The cluster's **`consolidated_uoc.md`** and each **source unit `.md`**.

## Inputs & outputs
- **In:** `--cluster <dir>`, `--unit CODE=PATH` (one per unit, repeatable), optional `--assessor-ac`
  (must match how the consolidation tags the trailing assessor paragraph).
- **Out:** `RESULT: PASS — every expected item appears exactly once`, or a list of `MISSING` /
  `UNEXPECTED` / `DUPLICATED`. **Exit 0/1.**

## How it works
Parses each source unit `.md` to build the expected set of `[UNIT SECTION numbering]` tags, parses
`consolidated_uoc.md`, and compares. Wording fidelity is a separate concern (guaranteed upstream by
extracting rather than retyping). Internals: `references/validator-internals.md`.

## Version history
- **v1.0.0 (2026-06-14)** — initial documented version.
