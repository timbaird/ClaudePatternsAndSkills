---
name: consolidate-uocs
version: 1.0.0
updated: 2026-06-14
model: claude-opus-4-8
description: >-
  This skill should be used when a cluster's units of competency need to be consolidated into a
  single consolidated_uoc.md — e.g. "consolidate the CL3 UoCs", "build the consolidated UoC for
  this cluster", "create consolidated_uoc.md", "merge these units' PCs/PEs/KEs into one grouped
  document", or after a cluster's unit .md transcriptions are validated and the next step is to
  group every assessable item. It extracts every PC/FS/PE/KE/AC verbatim and pre-tagged (a script),
  groups them into topic clusters where one assessment artefact could plausibly evidence the group
  (editorial judgement — a DRAFT proposal, never a locked decision), and validates that every item
  appears exactly once (a script). Use it for any UoC consolidation, even if the user does not name
  the scripts.
---

# Consolidate a cluster's units of competency

A consolidated UoC is a single document holding every assessable item — Performance Criteria (PC),
Foundation Skills (FS), Performance Evidence (PE), Knowledge Evidence (KE), Assessment Conditions
(AC) — from all units in a cluster, quoted verbatim, source-tagged, and grouped where the items
look like one assessment artefact could evidence them together. It is the bridge from the raw units
to the assessment plan.

This work has three layers, two deterministic and one editorial. Keep them distinct: the fidelity
comes from the scripts, the value from the judgement, and **the grouping is always a proposal for
the course owner to react to — never recorded as decided** (see the project's Rule 1).

## Workflow

> **Python interpreter:** run the commands below with whatever Python 3 launcher your system has —
> `python3`, `python`, or `py -3` (on Windows, `python3` may be the Microsoft Store alias).

### 1. Extract the faithful item inventory (script)

```bash
python3 .claude/skills/scripts/inventory_uoc.py \
  --unit <CODE>=<cluster>/units_of_competency/<CODE>_Complete_R<N>.md \
  --unit <CODE>=<cluster>/units_of_competency/<CODE>_Complete_R<N>.md \
  [--assessor-ac] > /tmp/<cluster>_inventory.md
```

This emits every item as a house-style line — `- <verbatim text> [<UNIT> <SEC> <num>]`, FS as
`- **<Skill>** — <desc> [<tag>]`, nested KE children indented under their tagged parent — taken
straight from the validated transcriptions. **This is the raw material to arrange; never retype an
item.** Moving these pre-tagged lines into groups is what guarantees the consolidated text stays
verbatim and every tag stays correct.

`--assessor-ac` controls whether the trailing "Assessors of this unit must satisfy…" paragraph is
emitted as one extra AC item per unit. Use the setting that matches how the cluster tags it (CL1–CL3
all tag it, so `--assessor-ac` on), and use the **same** setting in step 3.

### 2. Group the items (editorial — a DRAFT proposal)

Arrange the extracted lines into topic groups, then write the surrounding document. This is the
judgement layer; `references/consolidation-guide.md` has the full conventions. In short:

- A group collects items where the underlying competency is similar enough that **one assessment
  artefact could plausibly evidence all of them**. Each group gets `## Group N — <short name>`, a
  one-to-two-sentence **Why grouped:**, an **Assessment idea (TBD):**, then its item lines.
- Items that fit no group go under `## Ungrouped items` with a one-line reason.
- Open the document with the DRAFT status banner, the reference-tag-format note, and a Source units
  table. Mark the whole thing a proposal — **no grouping or assessment idea is approved**.
- Move each extracted line **unchanged** into exactly one group. Do not re-word, re-tag, or
  "tidy" the verbatim text.

Write the result to `<cluster>/consolidated_uoc.md`.

### 3. Validate completeness (script — mandatory gate)

```bash
python3 .claude/skills/scripts/validate_consolidated.py \
  --cluster <cluster> \
  --unit <CODE>=units_of_competency/<CODE>_Complete_R<N>.md \
  --unit <CODE>=units_of_competency/<CODE>_Complete_R<N>.md \
  [--assessor-ac]
```

Expect `RESULT: PASS — every expected item appears exactly once, nothing extra.` A `MISSING` item
means it was dropped during grouping; an `UNEXPECTED`/`DUPLICATED` item means a tag was mistyped or
an item placed in two groups. Fix the grouping and re-run until it passes. The validator checks
*tags*, not wording — the verbatim text is already guaranteed by extracting rather than retyping.

## Why this split

Itemising and checking completeness are mechanical and unforgiving, so they are scripts: the
inventory has been verified to reproduce existing consolidated docs item-for-item, and the validator
proves nothing is lost or doubled. Grouping is genuinely about assessment design — which competencies
naturally collapse into one task — so it stays a human-reviewed judgement, presented as a proposal.

## Portability

Self-contained: `inventory_uoc.py` and `validate_consolidated.py` live in `.claude/skills/scripts/`
and use only the Python standard library, so the whole `.claude/skills/` folder works in any course
repo. The grouping conventions in `references/consolidation-guide.md` are training-package-agnostic.
