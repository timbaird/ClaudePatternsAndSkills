# Sub-pattern — Baseline includes (default assets every project gets)

A reusable recipe that vendors the library's **baseline default assets** into a project — the ones that
go into **every** new repo automatically, on top of whatever the user picks per-project. Today the
baseline is:

- the **[`bro`](../../../skills/bro/)** skill → `<LAUNCH>/.claude/skills/bro/`
- the **[`ELI5`](../../../output-styles/ELI5.md)** output style → `<LAUNCH>/.claude/output-styles/ELI5.md`,
  **set as the active output style** in `settings.json`.

> **Sub-pattern** = a composable building block referenced by full patterns, not used alone.
> Referenced by: [umbrella-repo](../../umbrella-repo/umbrella-repo-setup.md),
> [single-repo](../../single-repo/single-repo-setup.md). Sibling of
> [dot-claude-setup](../dot-claude-setup/dot-claude-setup.md),
> [memory-setup](../memory-setup/memory-setup.md), [doco-setup](../doco-setup/doco-setup.md),
> [settings-setup](../settings-setup/settings-setup.md),
> [umbrella-claude-md-cascade](../umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md),
> [skill-vendoring](../skill-vendoring/skill-vendoring.md), and
> [project-discovery](../project-discovery/project-discovery.md).
> Placeholder: `<LAUNCH>` = the **launch-dir root** — the single repo in a single-repo project, or the
> **umbrella root** in a multi-repo project (output styles and `settings.json` load only from there).

## Why a baseline

Most reusable assets are opt-in per project (`skill-vendoring` asks *which* skills you want). A small
set is wanted **everywhere** — bring them in automatically so a new project is usable immediately,
rather than re-choosing them each time. This sub-pattern is the single home for that default set: add
to the list here and every future project picks it up.

## Placement — launch-dir root only

Both baseline assets go to the **launch-dir root's** `.claude/`, never a sub-repo:

- The **`bro` skill** *could* live in a sub-repo (skills cascade down), but as a cross-project utility
  it belongs at `<LAUNCH>/.claude/skills/` so it's available from everywhere.
- The **`ELI5` output style** and the **`outputStyle` setting** load **only from the launch dir** — put
  them anywhere else and they're never discovered.

## Provisioning steps (idempotent)

1. **Vendor the `bro` skill.** Copy the whole [`skills/bro/`](../../../skills/bro/) folder
   (`SKILL.md` + `README.md`) into `<LAUNCH>/.claude/skills/bro/`. If it's already there, leave it.
   (Follows [skill-vendoring](../skill-vendoring/skill-vendoring.md) — verbatim, whole folder. It's a
   pure-instruction skill: no runtime or third-party package to set up.)

2. **Vendor the `ELI5` output style.** Copy [`output-styles/ELI5.md`](../../../output-styles/ELI5.md)
   into `<LAUNCH>/.claude/output-styles/ELI5.md`. If a `.gitkeep` is holding that folder, it may be
   removed now the folder has real content.

3. **Set ELI5 as the active output style.** Merge `"outputStyle": "ELI5"` into
   `<LAUNCH>/.claude/settings.json` — **a top-level key, merged in, never a full overwrite**. Preserve
   `$schema`, the `hooks.SessionStart` memory hook (from [memory-setup](../memory-setup/memory-setup.md)),
   and the `permissions` block (from [settings-setup](../settings-setup/settings-setup.md)). If
   `outputStyle` is already set to something else, surface it and confirm before changing it.

4. **Verify.** `bro` appears in the session's available skills and triggers on `/bro`; a fresh session
   from `<LAUNCH>` reports the active output style as **ELI5**.

> **Don't commit here.** This is a *sub-pattern* — one component of a larger setup. Committing is
> **not** part of it: the calling pattern commits **once, after the full setup is complete**.

## Relationship to `skill-vendoring`

`skill-vendoring` handles the **per-project, user-chosen** skills (it asks which). This sub-pattern
handles the **always-on baseline** — the assets that don't need asking. Run **both**: baseline-includes
for the defaults, skill-vendoring for the extras. (Order-independent — both copy into place and don't
clobber existing content.)

## Idempotent / re-runnable

Additive and non-clobbering, like the sibling sub-patterns:
- An asset **already present** at its destination is **left alone**.
- The `settings.json` merge **re-confirms** rather than silently swapping: an existing different
  `outputStyle` is surfaced, not overwritten.
- **Adding to the baseline later** (a new default skill / output style) just means listing it here and
  re-running — existing projects pick it up on the next setup pass.
