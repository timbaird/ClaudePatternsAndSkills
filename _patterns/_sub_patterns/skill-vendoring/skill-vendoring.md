# Sub-pattern — Vendoring reusable skills into a repo

A reusable recipe that brings **existing reusable skills into a repo** by *vendoring* them — copying
each skill's whole folder in and committing it with the repo. Because Claude Code skills are vendored
(committed per-repo) rather than installed from a registry, a freshly created or cloned repo starts
with an **empty `.claude/skills/`**; the reusable skills from your other repos or your central library
don't arrive on their own. This is the "bring your skills" step.

> **Sub-pattern** = a composable building block referenced by full patterns, not used alone.
> Referenced by: [umbrella-repo](../../umbrella-repo/umbrella-repo-setup.md) (Step 9), single-repo, and
> any setup that wants reusable skills present. Sibling of
> [dot-claude-setup](../dot-claude-setup/dot-claude-setup.md),
> [memory-setup](../memory-setup/memory-setup.md), [doco-setup](../doco-setup/doco-setup.md),
> [umbrella-claude-md-cascade](../umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md),
> [project-discovery](../project-discovery/project-discovery.md), and
> [settings-setup](../settings-setup/settings-setup.md).
> Placeholders: `<REPO>` = target repo root; `<DEST>` = the `.claude/skills/` folder the **calling
> pattern designates** for each skill (see *Placement*).

## Why vendoring (and not "install")

Skills are **vendored**: a skill is *copied* into the repo's `.claude/skills/`, so the repo is
self-contained and works the moment it's cloned — no per-machine install, no network. The cost is
**drift** (improving a master means re-copying it into the repos that use it). There is no central
install step, so a new repo can't magically have the skills that live elsewhere — they must be brought
in deliberately, here. (See the library's vendoring-model note for the full trade-off vs a
manifest/marketplace.)

## The source — where a skill comes from

A skill to vendor can come from:
- a **central skills/patterns library repo** kept beside the project — the canonical source, and the
  cleanest case (it collapses the whole step to *"vendor these skills from `<library>`"*);
- a **path in another local repo** you already have;
- **pasted content** — the `SKILL.md` plus any supporting files.

The user (or the calling pattern) supplies *which* skills and *where each one lives*.

## Placement — the one parameter

Where each skill is copied depends on its **scope**, and the **calling pattern supplies the rule** —
this sub-pattern copies to the `<DEST>` it's given:
- **Cross-project / utility skill** → the umbrella's `.claude/skills/` (available from every repo).
- **Repo-specific skill** → that repo's own `.claude/skills/` (travels with that repo).
- **Single-repo project** → just `<REPO>/.claude/skills/`.

## Provisioning steps (idempotent)

1. **Ask which skills to vendor** (unless the caller already specified them). Prompt, e.g.:
   > *"Which of your existing reusable skills should I vendor in? For each, point me at where it lives
   > — a path in another local repo, a central library repo, or paste the `SKILL.md` plus any
   > `scripts/` / `references/` / `assets/` — and tell me whether it's cross-project or specific to one
   > repo so I place it correctly."*

2. **For each skill — copy the *entire* folder, verbatim.** Copy `SKILL.md` **and every supporting
   file** (`scripts/`, `references/`, `assets/`, `LICENSE`, etc.) — *not just `SKILL.md`*. A skill
   copied without its scripts/references is **broken**. Sanity-check the copied file count matches the
   source.

3. **Place it** at the `<DEST>` for its scope (per the calling pattern's placement rule).

4. **Check prerequisites.** If the skill bundles a runtime dependency — e.g. a **Python** script or a
   **Node** helper — confirm the interpreter is available (`python3` / `python` / `py -3`;
   `node --version`). If it's missing, **flag it / prompt to install** — don't silently assume it's
   there. (Pure-instruction skills have no runtime to check.)

5. **Verify discovery.** Confirm the skill is recognised — it appears in the session's available
   skills and triggers on a representative prompt. A skill that's present but not discovered is usually
   a malformed `SKILL.md` frontmatter (`name` / `description`) or wrong folder location.

> **Don't commit here.** This is a *sub-pattern* — one component of a larger setup. Committing is
> **not** part of it: the calling pattern commits **once, after the full setup is complete**.

## Idempotent + re-runnable

Additive and non-clobbering, like the sibling sub-patterns:
- A skill **already present** at its `<DEST>` is **left alone** — it's already vendored.
- **Adding a new skill later** just copies the new one in; re-running touches nothing else.
- **Updating** a vendored skill to a newer master is a deliberate re-copy (overwrite), not something a
  routine re-run does — note the new version when you do.

## Notes

- **Verbatim, whole-folder — the #1 mistake** is copying only `SKILL.md` and losing the `scripts/` or
  `references/` it depends on. Always copy the directory.
- **Drift is the accepted cost.** When a master skill improves, re-vendor it into the repos that use
  it. A central library repo makes this a deliberate, trackable re-copy and is the lightweight
  stand-in for a skill package manager until a native one exists.
- **Curating *into* the library (the inverse direction).** When the destination *is* the central
  library — i.e. you're centralising a skill for reuse rather than provisioning a consuming project —
  follow the library's extra conventions (a `version` + a `README`, and a provenance note for
  externally-created skills). See the library's `CLAUDE.md`. For provisioning a normal consuming repo,
  copy as-is.
