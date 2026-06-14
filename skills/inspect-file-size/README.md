# inspect-file-size · v1.0.0 (updated 2026-06-14)

## Purpose
Check whether a file is too big to commit to git and find **exactly what's inflating it**, before it
lands. Office files and binaries (uncompressed images, embedded video, dragged-in slide masters)
quietly bloat a repo; this gates on a size guideline and names the culprit so it can be trimmed
first. **General-purpose** — works on any `.pptx` / `.docx` / `.xlsx` or zip (git-tracked teaching
decks are the usual case).

## Prerequisites
- A **Python 3 interpreter** on PATH (`python3`, or `python` / `py -3` on Windows) — standard library only (no venv, no `pip install`).
- The bundled engine **`inspect_file_size.py`** — inside this skill's own folder (self-contained,
  no shared `scripts/` dependency).
- A target file to inspect (any zip-based Office file, or any zip archive).

## Inputs & outputs
- **In:** the file (and optional `--warn-mb`, `--top`).
- **Out:** a report — on-disk + uncompressed size, largest internal entries, embedded media by type
  (Office files), and `OK` / `WARNING`. **Exit 0** within the guideline, **1** over (pre-commit gate).

## How it works
```bash
python3 .claude/skills/inspect-file-size/inspect_file_size.py <file> [--warn-mb 25] [--top 15]
```
Opens the file as a zip, tallies entry sizes, and gates on `--warn-mb` (default 25 MB). The core
report is **format-agnostic**; the "embedded media by type" breakdown uses the OOXML `/media/` +
`/embeddings/` conventions, so it's richest for Office files and simply omitted for a plain zip. If it
WARNs, trim (e.g. Compress Pictures, or drop the named object) and re-run until OK.

## Version history
- **v1.0.0 (2026-06-14)** — initial documented version.
