# validate_cluster_coverage.py — internals & notes

Read this when a coverage result is surprising. For normal use, the SKILL.md is enough.

## What it does

1. **Expected set** — every `[UNIT SECTION numbering]` item tag in the cluster's
   `consolidated_uoc.md` (code spans stripped, so backtick-wrapped examples don't count). Reuses
   `valid_tag_set` from the traceability validator.
2. **Required vs informational** — the expected set is split: PC/FS/PE/KE are *required* (must be
   evidenced by a criterion); AC (Assessment Conditions) are *informational* by default, because
   they describe the assessment environment and are met by the setup, not by marking criteria. Pass
   `--include-ac` to require them too.
3. **Covered set** — the union of UoC references across every AT's benchmark section. Each AT is read
   with `docx_to_text` (or as `.md`), restricted to its benchmark/traceability section, and parsed
   with the shared `resolve_tags` — so abbreviated tags are resolved, range/list tags expanded, and
   compound `·` tags split, identically to the per-AT traceability validator.
4. **Report** — MISSING (required − covered), PHANTOM (covered − expected), overlap (covered by >1
   AT, informational), and per-AT contribution.

## Why these choices

- **Overlap is not an error.** Unlike the single-document consolidation check (where each item must
  appear exactly once), a competency may legitimately be evidenced across several ATs. Coverage only
  asks "≥ 1 AT", so overlap is reported as information, never a failure.
- **AC excluded by default.** Requiring AC items in criteria produces large false "missing" lists —
  Assessment Conditions are satisfied by the lab/tool/access setup described in the AT's conditions
  section, not by a marking criterion.
- **Benchmark-only scan.** References are taken from the benchmark/traceability section, not the
  whole document, so incidental mentions in task prose don't inflate coverage. If an AT has no
  benchmark section, the whole document is scanned as a fallback.

## Relationship to the other validators

- `validate-at-traceability` checks one AT inward (every criterion tagged, every reference valid).
- `validate-cluster-coverage` checks the cluster outward (the ATs together cover every required
  item). PHANTOMs it reports are the same per-AT issues the traceability validator pins down — run
  that on the offending AT to locate them.
- Both share the tag grammar and resolution in `validate_at_traceability.py`; a new unit-code prefix
  or tag form should be handled there so both stay consistent.

## Auto-discovery

With no `--at`, it globs `assessments/**/*Assessor*.docx`. If a cluster names its assessor files
differently, pass them explicitly with repeated `--at`. Exemplars and student copies are excluded by
the `*Assessor*` match (they carry no benchmark, so including them would not change coverage anyway).
