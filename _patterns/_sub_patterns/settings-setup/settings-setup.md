# Sub-pattern — Settings setup (git autonomy + permission model)

A reusable recipe that elicits a project's **operational config** — how Claude handles git, and how
permissive `settings.json` is — and applies it by **selecting a pre-made permission template and
merging it in**. Config-by-template: the human answers two questions, a reviewed profile gets merged;
nothing security-relevant is authored freehand.

> **Sub-pattern** = a composable building block referenced by full patterns, not used alone.
> Referenced by: [umbrella-repo](../../umbrella-repo/umbrella-repo-setup.md),
> [single-repo](../../single-repo/single-repo-setup.md). Sibling of
> [dot-claude-setup](../dot-claude-setup/dot-claude-setup.md),
> [memory-setup](../memory-setup/memory-setup.md), [doco-setup](../doco-setup/doco-setup.md),
> [umbrella-claude-md-cascade](../umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md),
> [skill-vendoring](../skill-vendoring/skill-vendoring.md), and
> [project-discovery](../project-discovery/project-discovery.md). Placeholder: `<REPO>` = the repo whose
> `settings.json` is configured (the umbrella/launch-dir root in a multi-repo project — settings load
> only from there).

## The two questions (ask Q1 before Q2)

**Q1 — Git interaction (non-destructive operations).** How should Claude handle commits, pushes,
branches, tags, pulls — operations that add to repo state without discarding work?
- **A — Auto-execute.** Claude runs them when it judges appropriate. (Solo / trusted automation.)
- **B — Ask before each.** Claude proposes the exact command + rationale, waits for approval.
- **C — User self-manages.** Claude never runs state-changing git; read-only git only.

> *Destructive* git (force push, hard reset, history rewrite, …) **always** requires explicit approval
> regardless of this answer — that's the universal rule stamped into `CLAUDE.md` by
> [project-discovery](../project-discovery/project-discovery.md), not something a setting can relax.

**Q2 — Permission model for `settings.json`.** How permissive should the auto-approve list be?
- **A — Strict** (ask for everything) → [`settings/permissions-strict.json`](../../../settings/permissions-strict.json)
- **B — Read-only auto-approved** *(recommended)* → [`settings/permissions-readonly.json`](../../../settings/permissions-readonly.json)
- **C — Open** (auto-approve everything) → [`settings/permissions-open.json`](../../../settings/permissions-open.json)

> Present the three neutrally but **recommend B**. Do **not** offer C as the default — it removes the
> human from consequential actions.

Q1 is asked first because its answer tunes the allowlist (see step 2).

## Apply

1. **Select** the `settings/` profile matching Q2's answer.
2. **Tune for Q1:** if git = **Auto-execute**, add the git-write commands to the profile's `allow`
   (`Bash(git add:*)`, `Bash(git commit:*)`, `Bash(git push:*)`, `Bash(git branch:*)`,
   `Bash(git tag:*)`); if **Ask** or **Self-manage**, leave them out so they prompt (or are never
   auto-run). The read-only git commands are already in the read-only/allowlist profiles.
3. **Merge** the profile's `permissions` block into `<REPO>/.claude/settings.json` — **preserve
   `$schema` and any existing `hooks.SessionStart`** (see the dependency below). If a `permissions`
   block already exists, confirm with the user before replacing it.

> **Don't commit here.** This is a *sub-pattern* — the calling pattern commits once, after the full
> setup is complete.

## Composes with memory-setup — load-bearing dependency

`settings.json` is a **shared file with multiple contributors**, so this sub-pattern must merge, not
overwrite:

- `dot-claude-setup` lays the base `$schema`; **`memory-setup` merges `hooks.SessionStart`** (the
  Node memory hook); this sub-pattern merges `permissions`. **Different keys → merge in, never
  overwrite** — preserve the memory hook or the per-session self-heal stops firing.
- The chosen profile's **deny list must not block what the memory hook runs each session** — `node`,
  `git rev-parse`, and writing `settings.local.json`. The provided profiles are written to keep these
  clear; if you customise the deny list, don't break them.
- **Order-independent:** because both merge, it doesn't matter whether `settings-setup` or
  `memory-setup` runs first.

## The behavioural side of Q1 (not a setting)

Q1 also carries a *behavioural* expectation — does Claude propose-then-commit, or commit on its own.
That belongs in `CLAUDE.md` (a working convention), **not** in JSON. This sub-pattern writes only the
**allowlist**; the behavioural note (and the universal "destructive git needs approval" rule) is
carried by [project-discovery](../project-discovery/project-discovery.md). Settings here, behaviour
there.

## Idempotent / re-runnable

Re-running means **re-confirm**, not silent swap: if `settings.json` already has a `permissions`
block, surface it and confirm before changing the profile. Safe to run before or after the other
sub-patterns.
