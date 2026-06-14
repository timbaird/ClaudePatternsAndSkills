---
name: inspect-file-size
version: 1.0.0
updated: 2026-06-14
model: claude-haiku-4-5-20251001
description: >-
  This skill should be used to check whether a file is too big to commit to git and to find exactly
  what is inflating it — e.g. "is this pptx/docx/xlsx too big to commit", "check the file size before
  I commit", "what's bloating this deck", "why is this Office file so large", "size / bloat hygiene
  check", or before committing any large Office file or binary. It runs a deterministic check (the
  bundled inspect_file_size.py) that reports the on-disk size, the largest internal entries, and
  embedded media grouped by type, and fails if the file exceeds a size guideline. Works on any
  zip-based Office file (.pptx, .docx, .xlsx) or any zip archive — git-tracked Office files such as
  teaching decks are the usual culprit. Use it whenever a file's size needs checking before commit,
  even if the user does not name the script.
---

# Inspect a file's size before committing

Office files and other binaries can quietly bloat a git repo — uncompressed images, an embedded
video, dragged-in slide masters. This skill shows a file's on-disk size and exactly which internal
objects are driving it, and gates on a size guideline, so a heavy file is caught and trimmed before
it lands. It is format-agnostic: it flags whatever the big objects are.

## When to use

- Before committing any large Office file (`.pptx` / `.docx` / `.xlsx`) or zip — teaching decks are
  the classic offender.
- When a file seems unexpectedly large and you need to find the culprit object.
- As a pre-commit hygiene gate for any tracked binary.

## How to run it

> **Python interpreter:** run the command below with whatever Python 3 launcher your system has —
> `python3`, `python`, or `py -3` (on Windows, `python3` may be the Microsoft Store alias).

```bash
python3 .claude/skills/inspect-file-size/inspect_file_size.py <file> [--warn-mb 25] [--top 15]
```

- `<file>` — the `.pptx` / `.docx` / `.xlsx` (or any zip) to inspect.
- `--warn-mb` — the size guideline; the check fails (exit 1) if the file on disk exceeds it. Default
  25 MB.
- `--top` — how many largest internal entries to list. Default 15.

Exit `0` if within the guideline, `1` if over — so it can act as a pre-commit gate.

## Interpreting the result

- **On disk / uncompressed total** — the headline size and how much it expands to.
- **Largest internal entries** — the specific objects (often `ppt/media/imageNN.*` in a deck) eating
  the space; this is where to look first.
- **Embedded media by type** — the culprit category at a glance (e.g. large `.tiff` / uncompressed
  `.png`, or an embedded video/audio). Shown for Office files; a plain zip with no `/media/` simply
  omits this section.
- **OK / WARNING** — within or over the guideline.

If it WARNs, trim before committing — e.g. for slides, PowerPoint → Compress Pictures (whole file,
150 ppi, delete cropped areas), or drop the offending object identified above — then re-run until OK.
Don't assume the cause; the report names it, and it won't be the same object every time.

## Portability

**Self-contained:** the engine `inspect_file_size.py` is bundled inside this skill's own folder (no
shared `scripts/`) and uses only the Python standard library — so the skill is a drop-in: copy the
`inspect-file-size/` folder into any repo's `.claude/skills/` and it works. It inspects any Office/zip
file, so it is a **general-purpose** "keep large files out of git" size gate, not tied to any project.
