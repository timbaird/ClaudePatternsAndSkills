---
name: validate-uoc-transcription
version: 1.0.0
updated: 2026-06-14
model: claude-haiku-4-5-20251001
description: >-
  This skill should be used whenever a unit-of-competency (UoC) transcription needs to be
  confirmed verbatim against its source Word document — e.g. "validate the CL3 transcriptions",
  "check the ICTCLD504 .md matches the source .docx", "is this UoC transcription accurate",
  "re-validate the unit transcriptions", or immediately after any UoC .md is created or
  hand-edited. It runs a deterministic word-level diff (the bundled validate_uoc.py) between
  each source .docx and its .md transcription and reports substantive differences (content
  added/removed/changed — blocking) separately from cosmetic ones (smart quotes, dashes,
  whitespace — acceptable). Use it whenever UoC transcription fidelity must be proven, even if
  the user does not name the script. It does NOT create transcriptions; it only checks existing
  ones.
---

# Validate UoC transcription fidelity

A UoC transcription is a Markdown (`.md`) copy of an official unit-of-competency Word document
(`.docx`). For VET compliance the `.md` must reproduce the source **verbatim** — no paraphrasing,
no omission, no LLM "tidying". This skill proves that mechanically by diffing the two at the word
level, so fidelity is confirmed by a script rather than by eye (which matters most when the same
agent both wrote and is checking the transcription — the script makes self-marking honest).

## When to use

- After creating a UoC transcription (as the closing gate — the `transcribe-uoc` skill calls this
  same script for exactly this reason).
- To re-check an existing transcription that may have drifted (hand-edited, merged, or just to be
  sure) **without** re-transcribing it.
- Whenever someone asks whether a unit `.md` faithfully matches its `.docx`.

## The validator

The deterministic engine is **`validate_uoc.py`**, bundled alongside this skill at
`.claude/skills/scripts/validate_uoc.py` (the shared `scripts/` folder that sits beside this
skill's directory — see "Portability" below). It uses only the Python standard library, so it
runs anywhere with `python3` — no virtualenv, no `pip install`.

It compares the **textual content in document order**: paragraphs and table cells from the
`.docx`, versus the `.md` with its Markdown syntax stripped (headings, table pipes, list bullets,
`<br>`). Word sequences are then diffed in two tiers — substantive vs cosmetic. The internal
mechanics and the deliberate exclusions are documented in
`references/validator-internals.md`; read that only when a result is surprising or when adapting
to a new course's file layout.

## How to run it

> **Python interpreter:** run the command below with whatever Python 3 launcher your system has —
> `python3`, `python`, or `py -3` (on Windows, `python3` may be the Microsoft Store alias).

The validator takes one or more `<docx> <md>` **pairs**. Run from the repo root:

```bash
python3 .claude/skills/scripts/validate_uoc.py \
  <cluster>/units_of_competency/original/<UNIT>_Complete_R1.docx \
  <cluster>/units_of_competency/<UNIT>_Complete_R1.md \
  [<docx2> <md2> ...]
```

The usual layout pairs each `.md` under `units_of_competency/` with its source `.docx` under
`units_of_competency/original/` (same basename). If a course stores them differently, just point
the validator at the actual `<docx> <md>` paths — the pairing is positional, not path-bound. To
validate a whole cluster, pass every unit's pair in one invocation.

Exit code is `0` when nothing substantive differs across all pairs, `1` otherwise — so the result
can gate an automated step.

## Interpreting the result

The script prints one verdict per pair. There are exactly three:

1. **`EXACT MATCH (byte-equivalent at word level)`** — the transcription is verbatim. Pass.

2. **`VERBATIM after cosmetic normalisation`** — verbatim apart from cosmetic differences (smart
   vs straight quotes, en/em dashes, non-breaking spaces, ellipsis, BOM). This is **acceptable**,
   but surface the listed cosmetic diffs to the user — they may prefer to fix the source so the
   two match byte-for-byte.

3. **`SUBSTANTIVE DIFFERENCES FOUND`** — words were added, removed, or changed. The transcription
   is **not** verbatim and must not be accepted. Report the diff blocks (the script prints the
   `.docx` words vs the `.md` words for each), correct the `.md` to match the source exactly, and
   re-run until the verdict clears. Never "resolve" a substantive diff by editing away from the
   source.

## Exit criteria

Every pair returns `EXACT MATCH`, or `VERBATIM after cosmetic normalisation` with the cosmetic
diffs reported to the user. Any `SUBSTANTIVE DIFFERENCES FOUND` blocks acceptance.

## Portability

This skill is self-contained so the whole `.claude/skills/` folder can be lifted into another
course repo and work unchanged. The shared validators live at **`.claude/skills/scripts/`** by
convention; this skill and its siblings (`transcribe-uoc`, `consolidate-uocs`) all call them from
there. Nothing here depends on any one course's documentation or paths — only on being handed
`<docx> <md>` pairs.
