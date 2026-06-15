# search-first · v1.0.0 (vendored 2026-06-15)

## Purpose
**Research before you code.** Before writing a custom utility or adding a dependency, search the
repo + package registries (npm/PyPI) + MCP servers + GitHub/web for existing solutions, score them
(functionality, maintenance, community, docs, **license**, deps), and decide **adopt / extend / build**.
It's the coding-side cousin of [skill-scout](../skill-scout/) ("search before you build" — one for
libraries/tools, the other for skills).

## Provenance — externally created
Vendored from [Everything Claude Code](../../resources.md) (ECC, MIT), **copied verbatim and scanned
in full on intake** (single-file `SKILL.md`; it uses `rg`/`gh`/registry + web search and can spawn a
general-purpose researcher subagent — no bundled code). The `version`/`updated` fields are **internal
re-vendor tracking**, not upstream's own versioning.

## How it works
A preflight checks which search channels are actually available (and reports honestly when one is
skipped), then runs need-analysis → parallel search → score → decide → implement. Includes a
quick "inline" mode (mentally run the checklist before writing a helper) and a "full" mode that
launches the researcher subagent for a structured comparison.

## Note on references
Upstream lists optional integrations with ECC's `planner`/`architect` agents and an
`iterative-retrieval` skill — those aren't part of CPAS, so treat them as nice-to-have hooks, not
requirements. The core search→score→decide workflow stands alone.

## Deploying
Copy the `search-first/` folder into a project's `.claude/skills/`. No dependencies beyond standard
shell + search tools (`rg`/`gh`/registry CLIs where available).
