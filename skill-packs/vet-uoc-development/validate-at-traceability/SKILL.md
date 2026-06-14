---
name: validate-at-traceability
version: 1.0.0
updated: 2026-06-14
model: claude-haiku-4-5-20251001
description: >-
  This skill should be used whenever an assessment task's UoC traceability needs checking — e.g.
  "validate the AT1 traceability", "check the marking guide UoC references", "does every criterion
  have a UoC tag", "are there any phantom/orphan references in this AT", "check the marking
  benchmark", or after authoring or editing any AT assessor instrument. It runs a deterministic
  check (the bundled validate_at_traceability.py) over an AT's Marking Benchmark / UoC-traceability
  section, confirming every marking criterion carries a unit-of-competency reference (no
  free-floating criteria) and every reference resolves to a real item in the cluster's
  consolidated_uoc.md (no phantom or mistyped tags) — optionally also that every item the AT is
  expected to evidence is covered. Use it whenever AT traceability must be confirmed, even if the
  user does not name the script. It checks references, not the quality of the criteria themselves.
---

# Validate an AT's UoC traceability

Every marking criterion in an assessment task must trace to the units of competency, both ways:
each criterion carries a UoC reference (so no criterion assesses something the units don't ask for),
and each referenced item is a real UoC item the AT genuinely evidences. This rule is otherwise
enforced by eye and is easy to slip — a criterion added without a tag, a mistyped reference, a
reference to an item that belongs to a different unit. This skill proves it mechanically against the
AT's Marking Benchmark / UoC-traceability section.

## When to use

- After authoring or editing an AT assessor instrument (its marking guide / benchmark).
- To check an existing AT for orphan criteria or phantom references.
- As a gate before treating an AT as ready — the traceability is the audit trail that the AT covers
  what it claims.

It checks the *references*, not whether the criteria are well-designed, and it validates one AT at a
time. (Whether the cluster's ATs *together* evidence every consolidated item is a separate,
cluster-level question.)

## The validator

The engine is **`validate_at_traceability.py`**, bundled at `.claude/skills/scripts/`. It reads the
AT from its `.docx` (the artefact of record) or a `.md` companion, reuses the bundled `docx_to_text`
extractor, and uses only the Python standard library. It parses the benchmark section's
criterion → tags mapping, resolves abbreviated tags (unit inherited from context) and expands
range/list tags (`[KE 1–6]`, `[KE 3, 4, 6]`) into their members, then checks each against the valid
item set built from the cluster's `consolidated_uoc.md`. Internals are in
`references/validator-internals.md`.

## How to run it

> **Python interpreter:** run the command below with whatever Python 3 launcher your system has —
> `python3`, `python`, or `py -3` (on Windows, `python3` may be the Microsoft Store alias).

```bash
python3 .claude/skills/scripts/validate_at_traceability.py \
  --at <cluster>/assessments/AT<n>/<AT>-Assessor.docx \
  --consolidated <cluster>/consolidated_uoc.md \
  [--expect "<UNIT SEC num>" --expect "<UNIT SEC num>" ...]
```

- `--at` — the AT assessor `.docx` (or `.md`). The benchmark/traceability section is where the
  criterion → UoC mapping lives.
- `--consolidated` — the cluster's `consolidated_uoc.md`, which defines the valid item set.
- `--expect` (optional, repeatable) — a UoC item the AT must evidence. Pass the AT's allocation from
  the assessment plan's coverage map to also check **reverse coverage** (nothing the AT should cover
  is missing). Omit to check only that what's referenced is valid and every criterion is tagged.

Exit `0` on PASS, `1` otherwise.

## Interpreting the result

The goal is `RESULT: PASS — every criterion is tagged and every reference is a real UoC item`.

**Hard failures (must fix):**
- **phantom / mistyped reference** — a tag (after resolving and expanding) that no source item
  matches. Usually a typo, a wrong unit code, or a reference to a Foundation Skill the unit doesn't
  have. Correct it to a real item, or remove it.
- **free-floating criterion** — a benchmark criterion with no UoC tag. Add its reference, or remove
  the criterion if it assesses nothing in the units.
- **unresolved abbreviated tag** — an abbreviated `[SEC num]` with no preceding full tag on the line
  to supply the unit. Make it a full `[UNIT SEC num]`.
- **uncovered expected item** (only with `--expect`) — an item the AT was told to evidence that no
  criterion references. Add a criterion or extend an existing one.

**Advisories (review, not blocking):**
- **not in individual full-ref form** — abbreviated or range/list references. They are expanded and
  validated, but the convention prefers one full `[UNIT SEC num]` per item for an unambiguous audit
  trail. Consider expanding them; decide per the course's house convention.
- **marking-guide criterion not found in the benchmark** — a best-effort cross-check; verify the
  criterion really does have a benchmark entry.

Fix the hard failures and re-run until PASS; weigh the advisories against the house convention.

## Portability

Self-contained: the validator lives in `.claude/skills/scripts/` and is stdlib-only, so the whole
`.claude/skills/` folder works in any course repo. It needs only the AT file and the cluster's
`consolidated_uoc.md`.
