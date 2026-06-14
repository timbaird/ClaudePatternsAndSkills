---
name: validate-cluster-coverage
version: 1.0.0
updated: 2026-06-14
model: claude-haiku-4-5-20251001
description: >-
  This skill should be used to check whether a cluster's assessment tasks, taken together, evidence
  every item in its consolidated UoC — e.g. "check the cluster coverage", "do the ATs cover every
  PC/PE/KE", "is anything left unassessed", "what UoC items aren't covered by the assessment tasks",
  "cluster coverage check", or before treating a cluster's assessment as complete. It runs a
  deterministic check (the bundled validate_cluster_coverage.py) that collects the UoC references
  from every AT's marking benchmark and reports which consolidated items no AT evidences (the gaps)
  and which references point nowhere (phantoms). Use it whenever cluster-wide assessment coverage
  must be confirmed, even if the user does not name the script. It is the capstone to the per-AT
  traceability check: that proves each AT's references are sound; this proves the ATs collectively
  leave nothing out.
---

# Validate cluster coverage

The per-AT traceability check proves a single AT's references are valid and every criterion is
tagged. This skill proves the complementary, cluster-wide property: the cluster's assessment tasks
**together** evidence every assessable item in the consolidated UoC — nothing falls through the
cracks. It is the check you run before calling a cluster's assessment complete.

## When to use

- When a cluster's ATs are authored (or partly authored) and you need to know what's covered and
  what's still missing.
- Before treating a cluster's assessment as finished — to confirm no PC / FS / PE / KE is unassessed.
- To see, for an in-progress cluster, exactly which items the remaining ATs still need to evidence.

## The validator

The engine is **`validate_cluster_coverage.py`**, bundled at `.claude/skills/scripts/`. It builds
the expected item set from the cluster's `consolidated_uoc.md`, collects the UoC references from
each AT's benchmark section (resolving abbreviated tags, expanding range/list tags, and splitting
compound `·` tags exactly as the traceability validator does), and compares. Stdlib only. Internals
are in `references/coverage-internals.md`.

## How to run it

> **Python interpreter:** run the command below with whatever Python 3 launcher your system has —
> `python3`, `python`, or `py -3` (on Windows, `python3` may be the Microsoft Store alias).

```bash
python3 .claude/skills/scripts/validate_cluster_coverage.py --cluster <cluster> [--include-ac]
```

- `--cluster` — the cluster directory (it contains `consolidated_uoc.md` and `assessments/`).
- It **auto-discovers** the assessor instruments (`assessments/**/*Assessor*.docx`). Pass `--at
  <file>` (repeatable) to use a specific set instead.
- `--include-ac` — also require Assessment Condition (AC) items to be referenced. **By default AC
  items are not required**, because Assessment Conditions describe the assessment environment
  (lab/tool/access requirements) and are satisfied by the assessment setup, not by marking criteria.
  AC coverage is reported separately as information.

Exit `0` on PASS (every required item evidenced by at least one AT), `1` otherwise.

## Interpreting the result

- **Covered: N / M** — the headline: how many required items (PC/FS/PE/KE) at least one AT
  evidences. For a complete cluster this should be 100%. For an in-progress one, the shortfall is
  the work remaining — the MISSING list names it.
- **MISSING** — consolidated items no AT evidences. For a finished cluster, every one is a real gap
  to close (add a criterion to the AT that should carry it). For an in-progress cluster, they are
  the items the unwritten ATs must pick up.
- **PHANTOM** — references in an AT that match no consolidated item. These are per-AT traceability
  problems (typo, wrong unit, a Foundation Skill the unit lacks); fix them in the AT, and use the
  `validate-at-traceability` skill on that AT to pin them down.
- **AC** — Assessment Conditions referenced vs total, informational (see `--include-ac`).
- **Overlap** — items evidenced by more than one AT. This is expected and fine — a competency may be
  assessed in several tasks — so it is only an informational count, never an error.

A cluster PASSes when there are no missing required items and no phantom references.

## Portability

Self-contained: the validator and the traceability helpers it reuses live in
`.claude/skills/scripts/` and are stdlib-only, so the whole `.claude/skills/` folder works in any
course repo. It needs only the cluster directory.
