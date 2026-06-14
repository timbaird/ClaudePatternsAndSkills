# consolidate-uocs · v1.0.0 (updated 2026-06-14)

## Purpose
Build a cluster's `consolidated_uoc.md` — a single document holding **every** assessable item
(PC / FS / PE / KE / AC) from all units in the cluster, quoted **verbatim**, source-tagged, and
**grouped** where one assessment artefact could plausibly evidence the group. It's the bridge
from raw units to the assessment plan. The grouping is always a **DRAFT proposal**, never a
locked decision (project Rule 1).

## Prerequisites
- A **Python 3 interpreter** on PATH (`python3`, or `python` / `py -3` on Windows) — standard library only (no venv, no `pip install`).
- Shared scripts in `.claude/skills/scripts/`: **`inventory_uoc.py`**, **`validate_consolidated.py`**.
- The cluster's unit transcriptions must already exist and be **validated verbatim**
  (see `transcribe-uoc` / `validate-uoc-transcription`).
- Cluster layout: unit `.md` files under `<cluster>/units_of_competency/`; output is
  `<cluster>/consolidated_uoc.md`.

## Inputs & outputs
- **In:** each unit's validated `.md` transcription.
- **Out:** `<cluster>/consolidated_uoc.md` — grouped, source-tagged, DRAFT-banner, source-units table.

## How it works
Three layers — two deterministic, one editorial:
1. **Extract** a faithful, pre-tagged item inventory with `inventory_uoc.py` (never retype — moving
   the pre-tagged lines is what keeps the text verbatim and tags correct).
2. **Group** the extracted lines editorially into `## Group N` blocks (Why grouped / Assessment
   idea (TBD)) — a proposal for the course owner. Conventions: `references/consolidation-guide.md`.
3. **Validate** completeness with `validate_consolidated.py` — every item exactly once.
`--assessor-ac` must match how the cluster tags the trailing assessor paragraph (use the same
setting in extract and validate).

## Version history
- **v1.0.0 (2026-06-14)** — initial documented version.
