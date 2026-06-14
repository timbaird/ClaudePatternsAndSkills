# vet-uoc-development — skill pack · v1.0.0 (updated 2026-06-14)

> ⚠️ **Deploy as a whole unit.** The skills in this pack share the bundled `scripts/` engine, so
> they must be installed **together**. Copy the **entire** `vet-uoc-development/` contents into the
> target project's `.claude/skills/` — the six skill folders become siblings and `scripts/` lands at
> `.claude/skills/scripts/`, which is the path the engines are hardcoded to expect. **Deploying a
> subset will break the validators** (their engine won't be present).

A toolkit for developing and quality-assuring VET/TAFE assessment from official **units of
competency (UoCs)** — transcription, consolidation, and the traceability/coverage validators that
prove compliance.

## Contents

### Skills (all deploy together)

| Skill | Version | Summary |
|---|---|---|
| [transcribe-uoc](transcribe-uoc/) | 1.0.0 | Convert an official UoC `.docx` → **verbatim** `.md` (lifts from Word XML), then validate fidelity. |
| [validate-uoc-transcription](validate-uoc-transcription/) | 1.0.0 | Word-level diff `.docx` vs `.md` to prove a transcription is verbatim (substantive vs cosmetic). |
| [consolidate-uocs](consolidate-uocs/) | 1.0.0 | Build a cluster's `consolidated_uoc.md`: extract every item verbatim (script) → group editorially (DRAFT) → validate completeness (script). |
| [validate-uoc-consolidation](validate-uoc-consolidation/) | 1.0.0 | Prove `consolidated_uoc.md` holds every source item exactly once (MISSING / UNEXPECTED / DUPLICATED). |
| [validate-at-traceability](validate-at-traceability/) | 1.0.0 | Prove one assessment task's marking criteria each carry a valid UoC tag and every tag resolves. |
| [validate-cluster-coverage](validate-cluster-coverage/) | 1.0.0 | Prove a cluster's ATs *together* evidence every consolidated item (gaps + phantoms). |

### Shared engine — `scripts/` (required by the skills above)
`inventory_uoc.py` · `transcribe_uoc.py` · `validate_uoc.py` · `validate_consolidated.py` ·
`validate_at_traceability.py` · `validate_cluster_coverage.py`

## Prerequisites
- A **Python 3 interpreter** on PATH (`python3`, or `python` / `py -3` on Windows) — standard library only (no venv, no `pip install`).
- A VET course repo layout: cluster directories containing `units_of_competency/`, `assessments/`,
  and `consolidated_uoc.md`.

## Version history
- **v1.0.0 (2026-06-14)** — initial pack: 6 UoC-development skills + shared `scripts/` engine.
