# validate-cluster-coverage · v1.0.0 (updated 2026-06-14)

## Purpose
Prove a cluster's assessment tasks, **taken together**, evidence every assessable item in its
`consolidated_uoc.md` — reporting **gaps** (items no AT evidences) and **phantoms** (references
that match no item). This is the capstone to per-AT traceability: that proves each AT's references
are sound; this proves the ATs collectively leave nothing out.

## Prerequisites
- A **Python 3 interpreter** on PATH (`python3`, or `python` / `py -3` on Windows) — standard library only (no venv, no `pip install`).
- Shared script in `.claude/skills/scripts/`: **`validate_cluster_coverage.py`** (reuses the
  traceability helpers).
- A cluster directory containing **`consolidated_uoc.md`** and an **`assessments/`** tree with
  assessor instruments (`*Assessor*.docx`).

## Inputs & outputs
- **In:** `--cluster <dir>` (auto-discovers `assessments/**/*Assessor*.docx`; or pass explicit
  `--at <file>`), optional `--include-ac`.
- **Out:** `Covered N/M`, `MISSING` (gaps), `PHANTOM` (bad refs), `AC` (informational), `Overlap`
  (informational). **Exit 0** when no missing required items and no phantoms, else **1**.

## How it works
Builds the expected item set from `consolidated_uoc.md`, collects UoC references from each AT's
benchmark (resolving abbreviated tags, expanding ranges, splitting compound `·` tags), and compares.
AC items are **not** required by default (they describe the assessment environment). Internals:
`references/coverage-internals.md`.

## Version history
- **v1.0.0 (2026-06-14)** — initial documented version.
