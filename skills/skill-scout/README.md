# skill-scout · v1.0.0 (vendored 2026-06-15)

## Purpose
Search **existing** skill sources — local, marketplace, GitHub, and web — *before* building a new
skill, so you don't duplicate work and you vet anything external before adopting it. Pairs naturally
with [skill-creator](../skill-creator/) (scout first, create only if nothing fits).

## Provenance — externally created
Vendored from [Everything Claude Code](../../resources.md) (ECC, MIT), which itself salvaged it from a
community PR. **Copied verbatim and scanned in full on intake** (single-file `SKILL.md`, no bundled
code; it uses `find`/`grep`/`gh`/web search to look things up). The `version`/`updated` fields are
**internal re-vendor tracking**, not upstream's own versioning.

## What it does
Given an intent, it: captures the task/trigger/keywords → searches local + marketplace skills first →
then GitHub/web → **vets external matches** (reads the `SKILL.md`, looks for unexpected shell/network/
credential behaviour, checks maintenance) → ranks and presents a short table (use existing / fork /
create fresh). It will not jump to "create new" without searching first.

## Deploying
Copy the `skill-scout/` folder into a project's `.claude/skills/`. No dependencies beyond standard
shell tools (and `gh`/web search where available).
