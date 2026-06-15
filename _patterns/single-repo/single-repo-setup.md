# The Single-Repo Setup Pattern — Setup Specification

Stand up a **single git repository** with the standard Claude Code infrastructure — the `.claude/`
skeleton, portable self-healing memory, the four documentation surfaces, and any reusable skills —
assembled almost entirely from the shared **sub-patterns**. It is the **non-nested sibling** of the
[umbrella-repo pattern](../umbrella-repo/umbrella-repo-setup.md): the same building blocks, minus the
multi-repo coordination layer.

> Placeholder: `<REPO>` = the repo's root. Commands are shown in `git` / shell form and are
> cross-platform — the memory mechanism uses a Node hook, so nothing here is OS-bound.

---

## 1. When to use this (vs. the umbrella pattern)

Use **single-repo** when the project is **one git repository** — no nested working repos to
coordinate. If you have two or more repos that need a shared coordination layer (a shared `CLAUDE.md`,
cross-repo memory, rules that span them), use the
[umbrella-repo pattern](../umbrella-repo/umbrella-repo-setup.md) instead — it adds the umbrella repo,
the nesting + `gitignore`, and the `CLAUDE.md` cascade **on top of these same sub-patterns**.

## 2. What you get

```
<REPO>/                      ← the git repo
├── .claude/                 ← skeleton: rules, skills, agents, memory, settings, hooks
│   ├── hooks/ensure-repo-memory.mjs    ← portable-memory hook (memory-setup)
│   ├── memory/MEMORY.md                ← version-controlled, portable memory
│   ├── rules/coding-principles.md      ← (optional) vendored rule
│   ├── settings.json                   ← live config incl. the SessionStart hook
│   └── …                               ← skills/, agents/, output-styles/, …
├── CLAUDE.md                ← always-loaded project context + rules
├── README.md                ← human landing page
└── docs/                    ← technical wiki (INDEX.md + doco-structure.md)
```

Everything loads from this **one** repo's `.claude/` — skills, `CLAUDE.md`, rules, agents, settings,
and memory — so there's no discovery asymmetry to manage and **no cascade**. Just launch Claude from
the repo root.

## 3. The sub-patterns it composes

| Step | Sub-pattern | What it does here |
|---|---|---|
| Skeleton | [dot-claude-setup](../_sub_patterns/dot-claude-setup/dot-claude-setup.md) | the uniform `.claude/` tree + minimal `settings.json` + `.gitignore` + bare `CLAUDE.md` |
| Memory | [memory-setup](../_sub_patterns/memory-setup/memory-setup.md) | relocate auto-memory into `<REPO>/.claude/memory/` (Node hook + `settings.local.json` redirect) |
| Settings | [settings-setup](../_sub_patterns/settings-setup/settings-setup.md) | git autonomy + permission model → merge a `settings/` template into `settings.json` |
| Docs | [doco-setup](../_sub_patterns/doco-setup/doco-setup.md) | the four surfaces — `README.md`, `CLAUDE.md` *shape*, `MEMORY`, `docs/` |
| Content | [project-discovery](../_sub_patterns/project-discovery/project-discovery.md) | interview → draft the `CLAUDE.md`/`README` summary + stamp universal discipline into `CLAUDE.md` |
| Skills | [skill-vendoring](../_sub_patterns/skill-vendoring/skill-vendoring.md) | vendor any reusable skills the user wants → `<REPO>/.claude/skills/` |
| Rules | [`rules/coding-principles.md`](../../rules/coding-principles.md) | (optional) the standard coding-principles rule |

The [umbrella-claude-md-cascade](../_sub_patterns/umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md)
sub-pattern is **not** used — it wires an umbrella's `CLAUDE.md` to nested sub-repos, and a single repo
has just one `CLAUDE.md`.

## 4. Setup playbook (single agent, linear)

> Run by **one agent, in order**. The sub-patterns share files (`settings.json`, `CLAUDE.md`) and have
> ordering dependencies, so don't fan them out. **No step commits** — make a **single commit** at the
> end (Step 8).

### Step 1 — The repo
Create or clone the git repo `<REPO>` and `cd` in. (Skip if it already exists.)

### Step 2 — `.claude/` skeleton  ← run the sub-pattern
Run [dot-claude-setup](../_sub_patterns/dot-claude-setup/dot-claude-setup.md). For a single repo, make
`.claude/README.md` the **canonical reference itself** — there's no umbrella to point up to (the
sub-pattern's README template covers this case).

### Step 3 — Portable, self-healing memory  ← run the sub-pattern
Run [memory-setup](../_sub_patterns/memory-setup/memory-setup.md): vendor the Node hook, wire the
`SessionStart` hook, gitignore `settings.local.json`, and create `.claude/memory/MEMORY.md`. The hook
keys off the repo's own git root, so it targets `<REPO>/.claude/memory/` automatically. (Confirm the
**Node prerequisite** first.)

### Step 4 — Operational config: git autonomy + permissions  ← run the sub-pattern
Run [settings-setup](../_sub_patterns/settings-setup/settings-setup.md): answer the git-interaction and
permission-model questions; it **merges** the matching [`settings/`](../../settings/) permission
template into `.claude/settings.json` (only the `permissions` block — preserving the Step 3 memory hook).

### Step 5 — Documentation surfaces  ← run the sub-pattern
Run [doco-setup](../_sub_patterns/doco-setup/doco-setup.md): establish the four doc surfaces and vendor
`doco-structure.md` into `docs/`. This sets up the `CLAUDE.md`/`README` **shape**; their **content is
drafted in Step 6** (project-discovery). (MEMORY is the Step 3 sibling; this step just leaves
`CLAUDE.md` pointing at it.)

### Step 6 — Draft the project's `CLAUDE.md` content  ← run the sub-pattern
Run [project-discovery](../_sub_patterns/project-discovery/project-discovery.md): the structured
interview (seven dimensions, a "must-not-go-stale" summary, mandatory repeat-back) that drafts the
"What this project is" summary into `CLAUDE.md` + `README.md` and stamps the universal discipline rules
(assumptions / `[TBD]`, destructive-git approval) into the single `CLAUDE.md`. For an *existing*
codebase, `codebase-onboarding` can analyse it first to seed the answers.

### Step 7 — Skills + rules
- Run [skill-vendoring](../_sub_patterns/skill-vendoring/skill-vendoring.md) for any reusable skills
  the user wants. **Placement is trivial here** — there's one repo, so everything goes to
  `<REPO>/.claude/skills/`.
- *(Optional)* vendor [`rules/coding-principles.md`](../../rules/coding-principles.md) into
  `<REPO>/.claude/rules/` — it auto-fires on code files via its `paths:` glob (no `settings.json`
  wiring).

### Step 8 — Verify, then commit (the single commit)
- **Memory test:** put a unique marker at the top of `.claude/memory/MEMORY.md`, open a **fresh session
  from `<REPO>`**, and ask Claude to recall it and report its memory path → should be
  `<REPO>/.claude/memory/`. Remove the marker.
- **Commit** — the **one** commit the setup makes; the sub-pattern steps deliberately deferred to here.
  Confirm machine-local files (`settings.local.json`, `agent-memory-local/`) are **not** staged.

## 5. Relation to the umbrella pattern

Single-repo is the umbrella pattern with the **multi-repo layer removed**:
- **No** umbrella / nesting / `gitignore`-the-sub-repos (umbrella Steps 1–3).
- **No** `CLAUDE.md` cascade (one repo, one `CLAUDE.md`).
- `.claude/README.md` is the canonical reference **itself**, not a pointer up.
- Memory, docs, skills, and rules all live in the **one** repo.

Everything else is identical — the sub-patterns, the single-agent / linear orchestration, the
one-commit discipline, the Node memory hook. If a single-repo project later grows into multiple repos,
adopt the [umbrella-repo pattern](../umbrella-repo/umbrella-repo-setup.md) and run the
[cascade sub-pattern](../_sub_patterns/umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md).

## 6. Gotchas checklist

- [ ] Launch Claude from the **repo root** — everything loads from its `.claude/`.
- [ ] **Node is a prerequisite** for the memory hook — `memory-setup` checks `node --version` and
      prompts to install if absent.
- [ ] `settings.local.json` (holds the machine-specific `autoMemoryDirectory`) is gitignored — never
      commit it.
- [ ] Accept the **workspace-trust** prompt on a new machine; **relaunch once** after the first heal.
- [ ] No example **rule** in `.claude/rules/` — rules auto-fire (see [rules/README.md](../../rules/README.md)).
- [ ] **One commit** at the end; the sub-pattern steps don't commit.
