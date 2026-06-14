# validate_at_traceability.py — internals & how to extend

Read this when a result is surprising, or when adapting to an AT whose marking guide is structured
unusually. For normal use, the SKILL.md is enough.

## What it parses

1. **The benchmark section.** The AT text (from `docx_to_text`, or a `.md`) is split at the last
   short heading line mentioning "benchmark" or "traceability". The text after it is the
   criterion → tags mapping; the text before it is the marking guide + instructions. If no such
   heading exists, the whole document is scanned and a hard failure is raised (an AT with no
   traceability section has nothing to validate).

2. **Criterion ids.** Lines beginning `^[A-Z]{1,2}\d+` followed by a dash (e.g. `T1 —`, `A2 —`,
   `B3 —`) are criterion lines. The benchmark's own id prefix(es) are learned and used to restrict
   the (best-effort) marking-guide cross-check, so task labels (`AT1`) and condition lists (`C1`)
   are not mistaken for criteria.

3. **Tags.** Every `[...]` on a criterion line is examined:
   - `[UNIT SEC num]` — a full reference (`UNIT` ∈ ICT…/BSB…/VU…, `SEC` ∈ PC/FS/PE/KE/AC).
   - `[SEC num]` — abbreviated; the unit is inherited from the nearest preceding full tag on the
     same line. With no preceding full tag, it is *unresolved* (a hard failure).
   - Brackets that are neither (prose, placeholders like `[ Write here ]`) are ignored.

## Resolution and expansion

- **Abbreviated** tags inherit the line's current unit.
- **Compressed** numbering is expanded into members before validation:
  - integer list `3, 4, 6` → 3, 4, 6
  - integer range `1–6` (en/em dash or hyphen) → 1..6
  - PC range within one major `1.1–1.4` → 1.1, 1.2, 1.3, 1.4
  - a cross-major PC range or anything unrecognised is left as its endpoints (and will fail
    validation if those aren't real items — surfacing it for a human)
- Foundation-skill references carry a skill **name**, not a number, so they are never expanded.

Each resolved member is checked against the valid set — every `[UNIT SEC num]` tag in the cluster's
`consolidated_uoc.md` (code spans stripped first, so backtick-wrapped example tags don't count).

## Hard failures vs advisories

**Hard (exit 1):** phantom/mistyped references (resolved member not in the valid set); free-floating
criteria (a benchmark criterion with no tag); unresolved abbreviated tags; and — only with
`--expect` — expected items not covered.

**Advisory (does not fail):** references not in individual full-ref form (abbreviated or
range/list), and the best-effort "guide criterion not in benchmark" cross-check. These reflect house
convention and judgement, not correctness, so they are surfaced but not enforced — decide per the
course's standard whether to expand compressed tags to individual full refs.

## Adapting

- **A new criterion-id scheme** (not `[A-Z]{1,2}\d+`) — widen `CRIT_ID`.
- **A different benchmark heading** — adjust `BENCH_HEADING`.
- **A new unit-code prefix** from another training package — extend the `FULL` / valid-set regexes
  (also do so in `validate_consolidated.py`, which shares the tag grammar).

Keep the checks strict: the value is in catching the criterion that lost its reference and the tag
that points nowhere. After any change, re-run against a known-clean AT (e.g. CL3 AT1, which should
PASS with only the abbreviated-form advisory) to confirm no regression.
