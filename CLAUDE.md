# CLAUDE.md — ClaudePatternsAndSkills

A reusable library of Claude Code **patterns, skills, and hooks** that get vendored into *other* repos.
Assets here are **sources** — copied into projects — so treat changes as published: they ripple outward.

## Read first
- [README.md](README.md) — what the library is and its layout.
- [docs/doco-structure.md](docs/doco-structure.md) — the four doc surfaces and the `CLAUDE.md`⇄`MEMORY` split.
- Collection indexes: `skills/README.md`, `skill-packs/README.md`, `hooks/README.md`, and `_patterns/`.

## Load-bearing principles (apply to all work here)
- **Patterns are recipes; sub-patterns are composable components.** A sub-pattern does its one job and
  **does not commit** — the calling pattern commits once, after the *full* setup.
- **Vendoring model.** Skills/hooks are *copied* into target repos; there's no central install. Improving
  a master means re-copying into consumers — accept the drift, track it via version stamps.
- **Cross-platform hooks use Node** (`node <file>.mjs`) — identical command on every OS. Don't write hook
  commands in `powershell`/`bash`/`python3` (not portable as committed hook commands).
- **Current-state only — no process archaeology.** Docs and patterns describe how to do the thing *now*;
  no "we used to…" narration. Asset **version stamps** are fine (current-state facts).
- **Every skill carries a `version` + a `README`;** keep each collection's index in step with its contents.
  Versioning means different things by origin: for **internally-created** skills the version tracks *our*
  iteration; for **externally-created** skills (vendored verbatim) it's an *internal tracking* field
  recording when we re-vendor an upstream update — flag the external origin in the skill's `README` and a
  `SKILL.md` frontmatter comment.

## Out of scope
- Not an app/runtime — nothing here "runs" as a product; it's a library of assets + recipes.
- No central package manager / auto-install — vendoring is deliberate (revisit only at scale).

## Where things live
Accumulated decisions/agreements → **MEMORY** (auto-loaded). Deeper rationale → **docs/**. User-facing
framing → **README**. (See `docs/doco-structure.md` for the full delineation.)
