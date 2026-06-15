# Sub-pattern — Standard `.claude/` skeleton

A reusable recipe that lays the **uniform `.claude/` infrastructure skeleton** into a repo: the
standard sub-folders (each held by a `.gitkeep`), the machine-local `.gitignore`, a minimal
`settings.json`, a `.claude/README.md` signpost, and a bare `CLAUDE.md` placeholder at the repo root.
Every repo in a project gets the **same** skeleton, so structure is uniform and ready to use even
where a slot is currently empty.

> **Sub-pattern** = a composable building block referenced by full patterns, not used alone.
> Referenced by: [umbrella-repo](../../umbrella-repo/umbrella-repo-setup.md) (run once for the umbrella
> and once per sub-repo), single-repo, and any pattern that stands up a repo. Sibling of
> [memory-setup](../memory-setup/memory-setup.md), [doco-setup](../doco-setup/doco-setup.md),
> [umbrella-claude-md-cascade](../umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md),
> [skill-vendoring](../skill-vendoring/skill-vendoring.md),
> [project-discovery](../project-discovery/project-discovery.md), and
> [settings-setup](../settings-setup/settings-setup.md).
> Placeholder: `<REPO>` = the target repo's root.

## Why

A uniform skeleton means any session opening any repo finds the **same predictable layout**, with a
home already waiting for rules, skills, agents, hooks, etc. — so adding one later is "drop it in the
existing folder," not "design the structure first." Empty slots are held open by `.gitkeep` so the
shape is visible and version-controlled before anything fills them.

## Order-independent and idempotent — by design

Safe to run **in any order** relative to the other sub-patterns, and safe to **re-run**. The rule
throughout is **create-what's-missing, never clobber what exists**:

- A folder or file that's **missing** is created.
- A file that **already exists** (e.g. a real `settings.json`, a hand-authored `CLAUDE.md`) is **left
  untouched** — this sub-pattern lays the *base*; the sibling sub-patterns augment it (see
  *Composition*).

## What it lays down

```
<REPO>/
├── CLAUDE.md                          # bare placeholder (content filled by doco-setup / cascade)
└── .claude/
    ├── README.md                      # signpost to the canonical reference
    ├── .gitignore                     # settings.local.json, agent-memory-local/
    ├── settings.json                  # minimal: just {"$schema": …}
    ├── rules/.gitkeep
    ├── skills/.gitkeep
    ├── agents/.gitkeep
    ├── agent-memory/.gitkeep
    ├── agent-memory-local/.gitkeep    # folder is gitignored (machine-local)
    ├── output-styles/.gitkeep
    └── hooks/.gitkeep
```

## The folder + `.gitkeep` rule

For each scaffold folder above: **create it if it doesn't exist; then, if it's empty, put a
`.gitkeep` in it.** A folder that already holds real content is left as-is — it's already
git-tracked, so it needs no `.gitkeep`. (When a folder later gains real content — e.g. a vendored
skill lands in `skills/` — its `.gitkeep` becomes redundant and may be removed.)

> `agent-memory-local/` is matched by `.claude/.gitignore`, so it (and its `.gitkeep`) won't be
> committed — it's a deliberately **machine-local** folder; the `.gitkeep` just makes it present on
> disk.

## File templates

### `<REPO>/.claude/.gitignore`
```gitignore
# Personal / machine-local Claude assets — never synced across machines.
settings.local.json
agent-memory-local/
```

### `<REPO>/.claude/settings.json` (minimal)
```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json"
}
```
> Minimal on purpose. The umbrella's live config (the `SessionStart` memory hook) is added by
> [memory-setup](../memory-setup/memory-setup.md) — this sub-pattern only ensures the file exists, and
> never overwrites one that already has content.

### `<REPO>/.claude/README.md` (signpost)
```markdown
# `.claude/` — infrastructure skeleton

Standard scaffold present in every repo for consistency. Most folders are empty placeholders until
needed. For a full explanation of what each folder/file is for, see the **umbrella repo's
`.claude/README.md`** (the single canonical reference).
```
> In a **sub-repo**, point at the umbrella's `.claude/README.md` as above. In a **standalone or
> umbrella repo** (no parent to point to), make this file the canonical reference itself — a short
> description of what each folder is for.

### `<REPO>/CLAUDE.md` (bare placeholder)
```markdown
# <REPO>

<!-- Project/repo context and working rules go here. The doco-setup sub-pattern authors the body;
     the umbrella-claude-md-cascade sub-pattern adds the cascade wiring. -->
```
> Create this **only if `CLAUDE.md` is absent**, so the skeleton is complete when run standalone. If
> doco-setup or the cascade sub-pattern already created/authored it, leave their file untouched.

## Provisioning steps (idempotent)

1. **Ensure `<REPO>/.claude/` exists.**
2. **Scaffold folders + `.gitkeep`** — for each of `rules/`, `skills/`, `agents/`, `agent-memory/`,
   `agent-memory-local/`, `output-styles/`, `hooks/`: create if missing; add a `.gitkeep` if the
   folder is empty (per the rule above).
3. **`.claude/.gitignore`** — create from the template if missing; if it exists, ensure both lines
   (`settings.local.json`, `agent-memory-local/`) are present, leaving other entries alone.
4. **`.claude/settings.json`** — create the minimal `{"$schema": …}` if missing; **never overwrite**
   an existing one (memory-setup augments the umbrella's).
5. **`.claude/README.md`** — create the signpost if missing.
6. **`<REPO>/CLAUDE.md`** — create the bare placeholder **only if absent** (content is owned by
   doco-setup / cascade).

> **Don't commit here.** This is a *sub-pattern* — one component of a larger setup. Committing is
> **not** part of it: the calling pattern commits **once, after the full setup is complete**.

## Composition with the sibling sub-patterns

This sub-pattern lays the **base**; the others **augment** it, and because everything is
create-or-augment + idempotent, they compose in **any order**:

- [memory-setup](../memory-setup/memory-setup.md) — adds the `SessionStart` hook to `settings.json`
  and relies on the `settings.local.json` line already in `.claude/.gitignore`.
- [doco-setup](../doco-setup/doco-setup.md) — authors the repo-root `README.md` and the `CLAUDE.md`
  body, and adds `docs/`.
- [umbrella-claude-md-cascade](../umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md) —
  adds the down-signpost / up-pointer wiring to `CLAUDE.md`.

## Notes — example-file discipline

If you seed any **example** files into the skeleton, keep them only where they're *inert* (skills,
agents, output-styles, hooks, status-line — they do nothing until invoked/wired). Do **not** leave an
example **rule** in `rules/` — rules auto-fire by their `paths:` glob, so a placeholder rule becomes
live noise. The one config that's always live is `settings.json`, so keep it real; put any
"what's possible" catalogue in `settings.example.json` (which Claude Code never loads).
