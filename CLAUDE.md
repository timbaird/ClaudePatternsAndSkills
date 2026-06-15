# CLAUDE.md — ClaudePatternsAndSkills

A reusable library of Claude Code **patterns, skills, and hooks** that get vendored into *other* repos.
Assets here are **sources** — copied into projects — so treat changes as published: they ripple outward.

## Read first
- **[docs/INDEX.md](docs/INDEX.md) — read this every session** (the docs catalogue; not auto-loaded
  like `MEMORY`, so reading it is on you), and load the relevant doc before related work.
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

## Working discipline — assumptions & documentation

Never record anything as *decided / agreed / canonical* unless it was actively discussed **and**
explicitly approved. Flag anything not yet agreed with `[TBD — needs discussion: <what is open>]`
rather than writing it as settled.

- Capture only what was discussed and agreed; don't extrapolate a principle into unraised specifics.
- Flag open questions explicitly with `[TBD — …]`.
- Distinguish archived/historical material from in-conversation decisions.
- Smaller is better — three faithfully-captured points beat ten padded ones.
- Self-correct — if you catch yourself writing beyond what was discussed, remove it or mark it `[TBD]`.

(This is the same universal discipline `project-discovery` stamps into every repo it sets up — CPAS
eats its own dogfood. "Current-state only" is the load-bearing principle above.)

## Git safety — destructive operations require explicit approval

Never run a destructive git operation without explicit, in-conversation approval for that specific
action — regardless of any settings allowlist or prior approval. Destructive includes: force push,
hard reset, discarding uncommitted changes, `git clean -f`, force-deleting branches, history rewrites
(`rebase`, `amend` on pushed commits, `filter-branch`/`filter-repo`), dropping stashes, deleting tags,
and any `--no-verify` / `--no-gpg-sign` bypass. Force-pushing a protected branch (`main`/`master`/
`release/*`) must be refused outright. When unsure whether something can lose work or rewrite history,
treat it as destructive and ask.

## Out of scope
- Not an app/runtime — nothing here "runs" as a product; it's a library of assets + recipes.
- No central package manager / auto-install — vendoring is deliberate (revisit only at scale).

## Where things live
Accumulated decisions/agreements → **MEMORY** (auto-loaded). Deeper rationale → **docs/**. User-facing
framing → **README**. (See `docs/doco-structure.md` for the full delineation.)
