# validate_consolidated.py — internals & deliberate behaviours

Read this when a consolidation-validation result is surprising, or when adapting the check to a
cluster whose source units are structured unusually. For normal use, the SKILL.md is enough.

## What it compares

The validator builds two sets and diffs them:

**Expected** — rebuilt from each source unit `.md`:
- **PC** — the `N.N` numbers in the *Elements and Performance Criteria* table.
- **FS** — the skill-name keys in the *Foundation Skills* table.
- **PE / KE / AC** — top-level bullets under each section heading, numbered `1..N`. Special case: a
  section whose ONLY top-level bullet ends in ':' is a parent — its immediate sub-bullets are the
  items instead (e.g. ICTICT517's PE).
- **assessor AC** — with `--assessor-ac`, one extra AC per unit for the trailing "Assessors of this
  unit must satisfy…" paragraph.

**Found** — every `[UNIT SECTION numbering]` tag in `consolidated_uoc.md`.

It then reports `MISSING` (expected − found), `UNEXPECTED` (found − expected), and `DUPLICATED`
(found more than once).

## Deliberate behaviours (don't "fix" these)

1. **Backtick code spans are stripped before tags are counted.** Example tags in the preamble are
   conventionally backtick-wrapped (`` `[ICTCLD504 PC 1.1]` ``) precisely so they are NOT counted as
   real references. Keep wrapping example tags; keep real item tags unwrapped.
2. **Tag position is irrelevant.** The tag-matching regex finds `[UNIT SEC num]` anywhere on a line,
   so both house styles validate equally — `- [tag] text` (CL1) and `- text [tag]` (CL2/CL3).
3. **It checks coverage, not wording.** Two different consolidations of the same cluster pass
   identically as long as every tag is present once. Verbatim fidelity of the item *text* is a
   separate guarantee, established upstream by extracting items rather than retyping them
   (see the consolidate-uocs skill).
4. **`--assessor-ac` must match the consolidation.** If the doc tags the trailing assessor paragraph
   but the flag is off (or vice-versa), the validator reports a phantom MISSING or UNEXPECTED AC.
   The setting is a property of the cluster's tagging convention, not of the validator.

## Reading the regex

Tags are matched as `\[(ICT\w+|BSB\w+|VU\d+) (PC|FS|PE|KE|AC) ([^\]]+)\]`. A unit whose code does not
start with `ICT`, `BSB`, or `VU` will not be recognised — extend the alternation in `extract_refs`
if a new training package introduces a different prefix.

## Adapting to a new cluster

The check is content-agnostic — it works for any cluster given its dir and source unit `.md` paths.
If a unit's source uses a section heading or table shape the parsers don't recognise (so the expected
inventory comes out wrong), adjust the relevant parser (`parse_pcs`, `parse_fs`,
`parse_section_bullets`) — keep it strict, since the whole point is to catch dropped or doubled
items, and re-run against a known-good consolidation to confirm no regression.
