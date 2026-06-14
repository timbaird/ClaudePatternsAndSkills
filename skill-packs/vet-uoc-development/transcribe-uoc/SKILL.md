---
name: transcribe-uoc
version: 1.0.0
updated: 2026-06-14
model: claude-haiku-4-5-20251001
description: >-
  This skill should be used whenever an official unit-of-competency (UoC) Word document needs to
  be turned into a Markdown transcription — e.g. "transcribe ICTCLD504", "convert this UoC .docx
  to markdown", "create the .md for BSBXTW401", "I've added a new unit's Word doc, transcribe it",
  or when a cluster has a source .docx under units_of_competency/original/ with no matching .md.
  It runs a deterministic converter (transcribe_uoc.py) that lifts the unit content verbatim from
  the Word XML — never retyping it, so nothing can be paraphrased, dropped, or "tidied" — and
  reconstructs the section/table/bullet structure from the document's styles. It then MUST validate
  the result against the source with validate_uoc.py, which proves the transcription is verbatim.
  Use it for any UoC docx-to-markdown transcription, even if the user does not name the script.
  Page furniture (headers, footers, page numbers) is excluded automatically and must not be
  transcribed.
---

# Transcribe a unit of competency (.docx → verbatim .md)

A UoC transcription is a Markdown copy of an official training-package unit document that must
reproduce the unit content **verbatim** — VET compliance depends on it. The trap with hand- or
LLM-typed transcription is silent drift: a dropped clause, a "corrected" word, a normalised
heading. This skill removes that risk by taking the content **straight from the Word XML runs**
(never retyping) and then **proving** fidelity with a mechanical validator. The transcription is
faithful by construction; the validator is the receipt.

## When to use

- A new unit's `.docx` has landed under a cluster's `units_of_competency/original/` and needs its
  `.md`.
- Any request to convert / transcribe a UoC Word document to Markdown.
- Re-generating a `.md` from its source (e.g. the source was reissued at a new release).

It does **not** decide groupings or write assessments — it only produces the faithful `.md`. To
re-check an existing transcription without regenerating it, use the `validate-uoc-transcription`
skill instead.

## Workflow

> **Python interpreter:** run the commands below with whatever Python 3 launcher your system has —
> `python3`, `python`, or `py -3` (on Windows, `python3` may be the Microsoft Store alias).

Two steps, both deterministic. The second is mandatory — a transcription is not done until it
validates.

### 1. Transcribe

```bash
python3 .claude/skills/scripts/transcribe_uoc.py \
  <cluster>/units_of_competency/original/<UNIT>_Complete_R<N>.docx \
  <cluster>/units_of_competency/<UNIT>_Complete_R<N>.md
```

The output path follows the house convention: the `.md` sits in `units_of_competency/` beside the
`original/` folder that holds the `.docx`, with the same basename. (Omit the second argument to
preview on stdout instead of writing.)

The converter, in brief — full detail in `references/transcriber-internals.md`:
- Reads only the document body, so headers/footers/page numbers are excluded automatically.
- Maps source paragraph styles to structure: `Title`/`Heading1` → `#` headings; `ListBullet`
  (and `ListBullet2`, …) → `-` bullets indented by nesting depth; tables → Markdown tables with
  multi-paragraph cells joined by `<br>`; everything else → plain paragraphs.
- Collapses stray double-spaces (never words), so output is clean and house-consistent.

### 2. Validate (mandatory gate)

Immediately prove the transcription is verbatim against its source:

```bash
python3 .claude/skills/scripts/validate_uoc.py \
  <cluster>/units_of_competency/original/<UNIT>_Complete_R<N>.docx \
  <cluster>/units_of_competency/<UNIT>_Complete_R<N>.md
```

Expect **`EXACT MATCH`**. Because the content was lifted from the XML rather than retyped, this is
the normal outcome. Treat anything else as follows:

- **`VERBATIM after cosmetic normalisation`** — acceptable; report the cosmetic diffs (quotes,
  dashes) to the user, who may choose to clean the source.
- **`SUBSTANTIVE DIFFERENCES FOUND`** — do **not** accept. This is rare and means the source uses
  a structural style the converter doesn't yet handle (e.g. an unusual list or table style), so a
  word landed in the wrong place or was missed. Read the diff, identify the structure that caused
  it, and extend `transcribe_uoc.py` to handle that style (see the "Adapting" section of the
  internals reference) — never hand-edit the `.md` away from the source to force a pass. Re-run
  both steps until it clears.

## Why a script, not freehand transcription

The content guarantee comes from *not retyping*. The script copies `w:t` text runs in document
order; the only thing it reasons about is structure (which style is a heading, a bullet, a table).
That means the failure mode is never "a word changed" — it's at most "a heading or bullet was
mis-shaped", which the validator catches and which is fixed once, in the script, for every future
unit. This converter has been verified to reproduce the entire existing UoC corpus
(every unit across all clusters, ICT and BSB training packages) byte-for-byte.

## Portability

Self-contained: the converter and validator live in `.claude/skills/scripts/` and use only the
Python standard library, so the whole `.claude/skills/` folder lifts into any course repo and
works on that course's UoCs unchanged. Nothing here is specific to one cluster.
