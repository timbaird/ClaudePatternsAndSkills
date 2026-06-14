# Consolidation guide — grouping conventions & document shape

Read this when performing the editorial layer (step 2) of `consolidate-uocs`. The mechanical layers
(extract, validate) are covered by the scripts; this is the judgement.

## What a consolidated UoC is for

It is the single source of truth for *what the cluster must assess*. Every downstream artefact (the
assessment plan, the AT marking guides, the per-UoC mapping docs) traces back to its items via the
`[UNIT SECTION numbering]` tags. So two properties are non-negotiable: **completeness** (every item
present exactly once — the validator enforces this) and **verbatim fidelity** (no item re-worded —
guaranteed by arranging the extracted lines rather than retyping them).

## Document shape

1. **Title** — `# <Cluster> — Consolidated UoC`.
2. **Status banner** (blockquote) — mark it **DRAFT** and state plainly that the groupings, comments
   and assessment ideas are a first-pass analysis and **nothing has been approved**. This is a Rule 1
   requirement, not decoration: the consolidation proposes, the course owner disposes.
3. **Reference-tag-format note** — one line showing the `[UNIT SECTION numbering]` form with
   backtick-wrapped examples (backticks matter: the validator strips code spans, so wrapped example
   tags are not counted). Note that PCs keep their source numbering and prefix, FS uses the verbatim
   skill name, and PE/KE/AC are numbered 1..N in source order.
4. **Source units table** — Code | Title | Source file, one row per unit.
5. **The groups** — see below.
6. **Ungrouped items** (if any) — under `## Ungrouped items`, each with a one-line reason it stands
   alone.

## Grouping — the judgement

Group items where the underlying competency or topic is similar enough that **one assessment
artefact could plausibly evidence every member**. The test is assessment-design plausibility, not
mere keyword overlap: ask "could a single task, observation, or question set produce evidence for
all of these at once?"

Each group:

```
## Group N — <short descriptive name>

**Why grouped:** one or two sentences. Brief — name the shared competency that binds them.

**Assessment idea (TBD):** one or two sentences proposing how a single artefact could evidence the
group. Always marked TBD.

- <item line>
- <item line>
  - <nested child, if the item has sub-bullets>
```

Guidance that has held up across clusters:
- Cross-unit groups are good — when two units carry the same competency (e.g. both name the shared
  security responsibility model), grouping their items shows the overlap and avoids double-assessing.
- A Foundation Skill often rides along with a deliverable rather than meriting its own task; it is
  fine for a group's assessment idea to say "evidenced through the documentation in Group X — no
  dedicated item."
- Keep groups coherent and not too large; if a group's *why* needs more than two sentences, it is
  probably two groups.
- Number groups in a sensible delivery-ish order, but remember the order is itself a proposal.

## Item line format (house style — produced by the extractor)

Move these **unchanged** from the inventory into groups:
- **PC** — `- N.N <verbatim text> [<UNIT> PC N.N]` (the source number stays in the text).
- **FS** — `- **<Skill name>** — <verbatim description> [<UNIT> FS <Skill name>]` (multi-part
  descriptions keep every part, joined with `<br>`).
- **PE / KE / AC** — `- <verbatim text> [<UNIT> SEC n]`. A KE item with sub-points keeps them as
  indented children beneath the one tagged parent line — the children are part of that single item,
  not separate items.

The trailing assessor-requirements paragraph ("Assessors of this unit must satisfy…") is an AC item
only when the cluster tags it (`--assessor-ac`); keep the inventory and validator settings aligned.

## Assessor-AC and other tagging notes

- **`--assessor-ac`**: CL1, CL2 and CL3 all tag the trailing assessor paragraph as the unit's last
  AC item, so the inventory and the validator both run with `--assessor-ac`. If a future cluster
  chooses not to tag it, drop the flag in both places — they must agree or the validator will report
  a phantom missing/extra item.
- **Range references in prose** (e.g. `[ICTCLD501 PC 5.1–5.4]`) may be used in a group's *Why* or
  *Assessment idea* as a convenience, but every individual item must still appear once as its own
  tagged line. The validator counts the individual item lines, not the prose ranges.

## After grouping — validate, then hand over

Run `validate_consolidated.py` (step 3 of the skill). On PASS, the document is complete and faithful
but the *groupings remain a proposal*. Present it to the course owner as a draft to react to; do not
describe any group or assessment idea as settled.
