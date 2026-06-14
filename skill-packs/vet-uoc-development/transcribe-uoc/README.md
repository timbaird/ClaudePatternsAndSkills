# transcribe-uoc · v1.0.0 (updated 2026-06-14)

## Purpose
Convert an official unit-of-competency (UoC) Word document (`.docx`) into a **verbatim** Markdown
transcription (`.md`), by lifting content straight from the Word XML (never retyping), then
**proving** fidelity with a validator. VET compliance depends on the `.md` reproducing the source
exactly — no paraphrasing, omission, or "tidying".

## Prerequisites
- A **Python 3 interpreter** on PATH (`python3`, or `python` / `py -3` on Windows) — standard library only (no venv, no `pip install`).
- Shared scripts in `.claude/skills/scripts/`: **`transcribe_uoc.py`** and **`validate_uoc.py`**.
- A source `.docx`, by convention under `<cluster>/units_of_competency/original/`.

## Inputs & outputs
- **In:** `<UNIT>_Complete_R<N>.docx`.
- **Out:** `<UNIT>_Complete_R<N>.md` under `units_of_competency/` (same basename), proven verbatim.

## How it works
Two deterministic steps; the second is mandatory:
1. **Transcribe** — `transcribe_uoc.py <docx> <md>`: reads only the document body (headers/footers/
   page numbers excluded), maps paragraph styles to structure (headings, bullets, tables), copies
   text runs in order. Detail: `references/transcriber-internals.md`.
2. **Validate** — `validate_uoc.py <docx> <md>` → expect `EXACT MATCH`. `VERBATIM after cosmetic
   normalisation` is acceptable (report the cosmetic diffs); `SUBSTANTIVE DIFFERENCES FOUND` means
   the converter doesn't yet handle a structural style — **extend the script**, never hand-edit the
   `.md` away from the source.

To only re-check an existing `.md`, use `validate-uoc-transcription` instead.

## Version history
- **v1.0.0 (2026-06-14)** — initial documented version.
