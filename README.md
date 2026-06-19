# ClaudePatternsAndSkills

A personal library of reusable **Claude Code patterns, skills, and hooks** for standing up and working
in repositories and projects — so common setup and tooling is *vendored in*, not reinvented each time.

## What's here

- **`_patterns/`** — *recipes*: how to set up a repo/project for a kind of work (e.g. `umbrella-repo`,
  `single-repo`, `library-setup`), composed from reusable **`_sub_patterns/`** (e.g. `memory-setup`,
  `doco-setup`).
- **`skills/`** — standalone, drop-in skills (e.g. `inspect-file-size`).
- **`skill-packs/`** — bundles of skills deployed *together* with shared dependencies (e.g. `vet-uoc-development`).
- **`hooks/`** — cross-platform hook scripts wired into `settings.json` (e.g. `ensure-repo-memory.mjs`).
- **`rules/`, `agents/`, `settings/`** — reusable rules, subagents, and settings fragments.
- **`docs/`** — how the library itself is organised; start with [doco-structure.md](docs/doco-structure.md).

## How it's used

Keep this repo available **alongside** a project you're setting up. Point an agent at the relevant
**pattern** — it provisions the new project by copying in the skills / hooks / rules the pattern lists.
The patterns are the *recipes*; the collections are the *ingredients*.

## Status

In active development — patterns and assets are added and refined as the approach matures.
