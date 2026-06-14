# validate-uoc-transcription · v1.0.0 (updated 2026-06-14)

## Purpose
Prove a UoC transcription (`.md`) reproduces its source Word document (`.docx`) **verbatim**, via a
word-level diff that separates **substantive** differences (added/removed/changed content —
blocking) from **cosmetic** ones (smart quotes, dashes, whitespace — acceptable). It's the
standalone form of the gate `transcribe-uoc` runs, and it makes self-marking honest when the same
agent both wrote and is checking the `.md`. It only checks; it does **not** create transcriptions.

## Prerequisites
- A **Python 3 interpreter** on PATH (`python3`, or `python` / `py -3` on Windows) — standard library only (no venv, no `pip install`).
- Shared script in `.claude/skills/scripts/`: **`validate_uoc.py`**.
- One or more **`<docx> <md>` pairs** (default layout: `.md` under `units_of_competency/`, `.docx`
  under `units_of_competency/original/`, same basename — but pairing is positional, so any paths work).

## Inputs & outputs
- **In:** one or more positional `<docx> <md>` pairs.
- **Out:** one verdict per pair — `EXACT MATCH`, `VERBATIM after cosmetic normalisation` (report the
  cosmetic diffs), or `SUBSTANTIVE DIFFERENCES FOUND` (blocking). **Exit 0** when nothing
  substantive differs across all pairs, else **1**.

## How it works
Compares textual content in document order (paragraphs + table cells from the `.docx` vs the `.md`
with Markdown syntax stripped), then diffs word sequences in two tiers (substantive vs cosmetic).
Never "resolve" a substantive diff by editing away from the source. Internals:
`references/validator-internals.md`.

## Version history
- **v1.0.0 (2026-06-14)** — initial documented version.
