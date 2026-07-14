---
name: map-process
version: 1.0.0
description: |
  Turn a factory's step→gate run-sheet into a Mermaid process map plus a
  structured audit model — a visual summary of the process a factory currently
  implements, and the input to a process audit. Reads a run-sheet doc written in
  the factory step→gate convention (`**N · `skill` — Title** *(scope)*` step headers;
  `> **⟱ Gate N→M:** *kind* `validator` = …` gate blockquotes), cross-checks
  every named skill/validator/agent/engine against what actually exists under
  the skills + engines roots, and emits per run-sheet a flowchart (steps → gates
  → done, gates coloured by build status), a tooling-&-locus table (🏠 factory
  tools each stage runs · 📦/🌐 project data it draws on · 👤 human-led), an
  audit table (named-but-missing validators, stale doc status markers), and a
  machine-readable JSON model. Domain-agnostic: point it at any factory's
  run-sheet(s). Stdlib only — no venv.
allowed-tools:
  - Bash
  - Read
---

# map-process

Map the process a **factory** (a repo authored to the step→gate run-sheet convention) currently
implements — as a **Mermaid flowchart** you can read at a glance, backed by a **structured model** a
downstream audit consumes. It answers three questions in one pass:

1. **What is the flow?** — the ordered steps and the gates between them.
2. **What runs at each stage, and where?** — the skills / agents / engines / MCP each step uses
   (🏠 factory tooling) and the project / website data it draws on (📦 / 🌐), plus which stages are
   👤 human-led.
3. **Is the process self-consistent?** — the **cross-check / audit**: a gate that names a validator
   which resolves to no skill/script/agent, or a doc status marker that contradicts what exists
   (e.g. prose says *"to build"* but the skill is already there).

It is **read-only** over the factory: it authors nothing but its own output maps.

## Run it

Stdlib only — run with any Python 3 (no venv). From the repo root:

```bash
python3 .claude/skills/map-process/map_process.py \
    docs/run-sheet.md \
    --skills-root .claude --engines-root scripts --out docs/process-maps
```

- **positional args** — one or more run-sheet `.md` files, **in pipeline order**. Give ≥2 and it also
  writes `factory-overview.md`, chaining them (last step of one → first step of the next).
- `--skills-root` (default `.claude`) — the root holding `skills/` (skill dirs + `skills/scripts/`
  engines) and `agents/`. What a named validator/agent is resolved against.
- `--engines-root` (default `scripts`) — a root of standalone engine scripts (scanned one level deep),
  so bare script names in the run-sheet resolve.
- `--out` (default `docs/process-maps`) — output directory.

Re-runnable: it regenerates the maps from the current docs + inventory every time. **The maps are
generated — regenerate, don't hand-edit them.**

## What it writes (per run-sheet `<slug>`)

- **`<slug>.md`** — the human view: a summary line, the **Mermaid flowchart**, the **Tooling & locus by
  stage** table, a legend, and the **Cross-check / audit table**.
- **`<slug>.json`** — the structured model (steps with `skill`/`scope`/`status`/`tools`/`data`; gates
  with `kind`/`names`/`resolved`/`implemented`/`flags`/`cls`). This is the seam a process-audit
  capability reads — it never has to re-parse prose.
- **`factory-overview.md`** (when ≥2 run-sheets) — the pipelines as subgraphs with the hand-off edge.

## The grammar it parses

A run-sheet written the factory way:

- **Step header** — `**N · `skill` — Title** *(scope)*`. The backticked skill and the `*(scope)*` are
  optional; a step with no skill is treated as **human-led**.
- **Gate** — a blockquote `> **⟱ Gate N→M (label):** *kind* … ` where *kind* is `*validator*`,
  `*human review*`, `*human / institutional*`, etc.; backticked names in the gate body are candidate
  validators; `+ human` marks a retained human check; a trailing **built** / **to build** is the doc's
  status marker.
- **Step detail** — a `## §N — …` section is associated with step *N*; its prose is scanned (alongside
  the pipeline block) to harvest the stage's tools + data artefacts, however they're spelled (backticked,
  **bold**, or bare).

## How the cross-check colours a gate

- **🟩 built** — a named validator resolves to a real skill / `skills/scripts/` engine / agent.
- **🟨 human-only** — no validator yet (a candidate for tooling).
- **🟥 flag** — an inconsistency worth a human's eye: a named validator that resolves nowhere, or a
  status marker that contradicts reality. These are the audit's starting points.

A validator name resolves across forms — kebab `validate-slide-plan` (a skill dir), snake
`validate_slide_plan` (a `skills/scripts/` engine), an `… agent` suffix (an `agents/*.md`), and a bare
`build_topic_deck` (an `--engines-root` script). `mcp__*` tokens are recognised as MCP tools. Only a
name that resolves, *or* looks validator-ish (`validate`/`verify`/`generate`/… or ends `.py`), counts as
a named validator — an incidental backticked word in a gate is ignored.

## Locus (where each stage runs / draws data)

The map tags each stage's loci inline:
- **🏠 factory** — the tooling (skills/engines/agents) resolved under the skills + engines roots.
- **📦 project / 🌐 website** — data artefacts (`.md`/`.docx`/`.pptx`/`.yaml`/`.ts`/…) the stage draws
  on; a token that looks website-side (`.astro`, `/src/`, `website`) is tagged 🌐, else 📦.
- **👤 human-led** — a step with no primary automated skill.

This surfaces the crossing worth seeing — a factory tool operating on a project data file.

## Viewing the maps

The `.md` files render their Mermaid on **GitHub** and in **VS Code** (with a Markdown-Mermaid preview
extension) with no build step — the text *is* the artefact, so it diffs cleanly as the process evolves.

## Where it fits

Downstream of the maps sits a **process audit** (a separate skill/agent, not this one): it reads the
`<slug>.json` model + the flag set and reasons about deeper problems — orphan tools (a skill referenced
by no step), ordering/dependency issues, gates with no definition-of-done. `map-process` is the input
that makes that audit deterministic. Related: [draw-diagram](../draw-diagram/SKILL.md) (the technical-
diagram renderer), [review-slides](../review-slides/SKILL.md).
