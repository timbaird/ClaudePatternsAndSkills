# validate-at-traceability · v1.0.0 (updated 2026-06-14)

## Purpose
Prove **one** assessment task's UoC traceability: every marking criterion carries a unit-of-
competency reference (no free-floating criteria), and every reference resolves to a real item in
the cluster's `consolidated_uoc.md` (no phantom or mistyped tags). Optionally checks **reverse
coverage** — that the AT evidences the items it was allocated. It checks *references*, not the
quality of the criteria.

## Prerequisites
- A **Python 3 interpreter** on PATH (`python3`, or `python` / `py -3` on Windows) — standard library only (no venv, no `pip install`).
- Shared script in `.claude/skills/scripts/`: **`validate_at_traceability.py`** (reuses the bundled
  `docx_to_text` extractor).
- The AT **assessor instrument** (`.docx` or `.md`) containing a Marking Benchmark /
  UoC-traceability section.
- The cluster's **`consolidated_uoc.md`** (defines the valid item set).

## Inputs & outputs
- **In:** `--at <AT-Assessor.docx>`, `--consolidated <consolidated_uoc.md>`, optional repeatable
  `--expect "<UNIT SEC num>"` (the AT's allocation, for reverse-coverage).
- **Out:** `PASS`, or findings — phantom/mistyped reference, free-floating criterion, unresolved
  abbreviated tag, uncovered expected item (with `--expect`); plus advisories. **Exit 0/1.**

## How it works
Parses the benchmark's criterion→tags mapping, resolves abbreviated tags (unit from context),
expands range/list tags (`[KE 1–6]`, `[KE 3,4,6]`), and checks each against the consolidated item
set. One AT at a time — cluster-wide coverage is `validate-cluster-coverage`. Internals:
`references/validator-internals.md`.

## Version history
- **v1.0.0 (2026-06-14)** — initial documented version.
