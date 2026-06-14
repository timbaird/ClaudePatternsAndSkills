# skill-creator · v1.0.0 (updated 2026-06-14)

## Purpose
Create new skills from scratch, edit and improve existing ones, and measure skill performance
(evals, benchmarks with variance analysis, and description-triggering optimisation). It's the
meta-skill for building the *other* skills in this library.

## Provenance — externally created
This skill is **externally created** (the Anthropic `skill-creator`). It is **centralised here for
management** rather than authored or maintained internally. It was vendored from upstream and then
**lightly trimmed** to remove guidance for environments we don't run in (see *Edits from upstream*
below) — so it is *not* byte-for-byte verbatim; re-vendoring an upstream update means re-applying
these same trims.

## Edits from upstream
The only changes to upstream's `SKILL.md` are removals of environment-specific guidance that does not
apply to a Claude Code (CLI / VS Code) setup, plus the added tracking frontmatter:

1. **Added frontmatter** — `version` / `updated` with a comment marking them internal tracking fields
   (see *Versioning note* above). Nothing else in the frontmatter changed.
2. **Removed the "Claude.ai-specific instructions" section** — the no-subagents / no-browser workflow
   variant for Claude.ai. We have subagents and a display.
3. **Removed the "Cowork-Specific Instructions" section** — Cowork-only mechanics (`--static` viewer,
   file-download feedback). Not our environment.
4. **Removed the inline "Cowork / headless environments" note** in the eval-viewer launch step (the
   `--static` headless fallback).
5. **Removed the trailing Cowork line** from the closing TodoList reminder.
6. **De-coupled the packaging section** — upstream's "Package and Present (only if `present_files`
   tool is available)" became a plain **"Package"** section; `present_files` isn't available in
   Claude Code, but `scripts.package_skill` is useful, so the command was kept and the tool gate
   dropped.
7. **Lifted "Updating an existing skill" out of the Claude.ai section** into its own top-level
   section (it's environment-agnostic advice), dropping the `/tmp/` Unix-path specifics.

**Not changed:** the core create → test → review → improve → package loop, all `scripts/`,
`eval-viewer/`, `agents/`, `references/`, `assets/`, and `LICENSE.txt` are upstream's, untouched.

**Residual Unix-isms (left as-is):** the main flow still uses `nohup … &`, `open <file>`, `/dev/null`,
and `/tmp/` example paths — these assume a Unix-like shell. On Windows they run under Git Bash; adapt
on the fly if needed. Left untouched to keep the divergence from upstream minimal.

## Versioning note (external skill)
The `version` / `updated` fields in `SKILL.md` are **internally-added tracking fields**, not the
vendor's own versioning. Unlike internally-created skills (which are versioned because *we* iterate
on them), this one is versioned only to track **when we re-vendor an upstream update** — bump the
fields when re-copying a newer upstream, otherwise leave them alone.

## What's in the folder
- `SKILL.md` — the skill itself (the full create → test → review → improve loop).
- `scripts/` — eval / benchmark / packaging / description-optimisation Python tooling.
- `eval-viewer/` — `generate_review.py` + HTML viewer for reviewing eval outputs.
- `agents/` — grader / comparator / analyzer subagent instructions.
- `references/schemas.md` — JSON schemas for evals, grading, benchmarks.
- `assets/` — the eval-review HTML template. `LICENSE.txt` — upstream licence.

## Deploying
Copy the whole `skill-creator/` folder into a project's `.claude/skills/`. The eval/benchmark
scripts need a Python 3 interpreter; the core authoring workflow does not.
