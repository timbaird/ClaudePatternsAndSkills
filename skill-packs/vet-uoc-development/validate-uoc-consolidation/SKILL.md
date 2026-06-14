---
name: validate-uoc-consolidation
version: 1.0.0
updated: 2026-06-14
model: claude-haiku-4-5-20251001
description: >-
  This skill should be used whenever a cluster's consolidated_uoc.md needs to be checked for
  completeness against its source units — e.g. "validate the CL3 consolidated UoC", "does the
  consolidated doc cover every item", "re-validate consolidated_uoc.md after my edits", "check no
  PC/PE/KE was dropped or duplicated", or after any hand-edit to a consolidated UoC (re-grouping,
  re-pointing topic→AT mappings, fixing wording). It runs a deterministic check (the bundled
  validate_consolidated.py) that every PC/FS/PE/KE/AC from each source unit appears in the
  consolidated document exactly once — flagging anything MISSING, UNEXPECTED, or DUPLICATED. Use it
  whenever consolidation completeness must be confirmed, even if the user does not name the script.
  It checks tag coverage, not wording, and does NOT build or group a consolidation.
---

# Validate a consolidated UoC for completeness

A consolidated UoC must reference **every** assessable item — Performance Criteria (PC), Foundation
Skills (FS), Performance Evidence (PE), Knowledge Evidence (KE), Assessment Conditions (AC) — from
each unit in the cluster, **exactly once**. A dropped item means a competency goes unassessed; a
duplicated one muddies the audit trail. This skill proves coverage mechanically: it rebuilds the
expected item inventory from the source units and checks it against the tags in the consolidated
document. It is the same gate the `consolidate-uocs` skill runs at the end of building one — exposed
here as a standalone so an existing consolidation can be re-checked anytime.

## When to use

- After hand-editing a `consolidated_uoc.md` — re-grouping items, re-pointing topic→AT mappings,
  fixing wording — to confirm nothing was lost or doubled.
- To check a consolidation built elsewhere, or just to reconfirm coverage before relying on it.
- As the completeness gate after building a consolidation (the `consolidate-uocs` skill calls this
  same script).

It does **not** build or group a consolidation, and it does not check the *wording* of items — only
that every expected tag is present exactly once.

## The validator

The engine is **`validate_consolidated.py`**, bundled at `.claude/skills/scripts/`. It uses only the
Python standard library, so it runs anywhere with `python3` — no virtualenv. It parses each source
unit `.md` to build the expected set of `[UNIT SECTION numbering]` tags, then parses
`consolidated_uoc.md` and compares. Its internals and the parsing rules are in
`references/validator-internals.md`; read that only when a result is surprising.

## How to run it

> **Python interpreter:** run the command below with whatever Python 3 launcher your system has —
> `python3`, `python`, or `py -3` (on Windows, `python3` may be the Microsoft Store alias).

```bash
python3 .claude/skills/scripts/validate_consolidated.py \
  --cluster <cluster> \
  --unit <CODE>=units_of_competency/<CODE>_Complete_R<N>.md \
  --unit <CODE>=units_of_competency/<CODE>_Complete_R<N>.md \
  [--assessor-ac]
```

- `--cluster` — the cluster directory (it contains `consolidated_uoc.md`).
- `--unit CODE=PATH` — one per source unit: its tag code and its `.md` path (relative to the cluster
  dir, or absolute). Repeat for every unit.
- `--assessor-ac` — count the trailing "Assessors of this unit must satisfy…" paragraph as one extra
  AC item per unit. Use the setting that matches how the consolidation tags it — CL1–CL3 all tag it,
  so `--assessor-ac` on. The flag must match the consolidation, or the check reports a phantom
  missing/extra item.

Exit code is `0` on PASS, `1` otherwise — so it can gate an automated step.

## Interpreting the result

The goal verdict is `RESULT: PASS — every expected item appears exactly once, nothing extra.`
Otherwise the script lists the problems:

- **`MISSING`** — an expected item has no tag in the consolidated doc. It was dropped (often during
  re-grouping). Add it back to the right group.
- **`UNEXPECTED`** — a tag in the consolidated doc that no source item matches. Usually a mistyped
  tag (wrong code, section, or number) or a stray range/example tag left unwrapped. Fix or remove it.
- **`DUPLICATED`** — an item tagged in more than one place. Decide its single home and remove the
  other(s).

Fix the consolidation and re-run until it PASSes. The check is about tag coverage; verbatim wording
is a separate concern (guaranteed upstream by extracting items rather than retyping them).

## Exit criteria

`RESULT: PASS`. Any MISSING / UNEXPECTED / DUPLICATED finding blocks acceptance.

## Portability

Self-contained: the validator lives in `.claude/skills/scripts/` and is stdlib-only, so the whole
`.claude/skills/` folder lifts into any course repo and works on that course's clusters unchanged.
It only needs the cluster dir and its source unit `.md` paths.
