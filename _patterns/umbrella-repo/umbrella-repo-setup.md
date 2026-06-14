# The Multi-Repo "Umbrella" Pattern — Setup Specification

A reusable pattern for coordinating **multiple git repositories** under a single,
version-controlled **umbrella repo** that carries the shared Claude Code tooling
(`CLAUDE.md`, rules, skills, settings) and a **portable, self-healing memory**.

> This document is **generic and self-contained**, and it is the **orchestrator**: the
> conceptual sections (§1–§5) explain the shape, and the setup playbook (§6) sequences the work —
> **delegating memory, documentation, and the `CLAUDE.md` cascade to their dedicated sub-patterns**
> rather than repeating them here.
>
> Placeholders: `<UMBRELLA>` = the umbrella repo name; `<REPO_A>`, `<REPO_B>`, … = the nested
> working repos. Commands are shown in `git` / shell form. Nothing here is OS-bound — the memory
> mechanism uses a **Node** hook, so the same setup works on Windows, macOS, and Linux.

---

## 1. The problem this solves

When you work across several repos from a **plain parent folder**, that folder is not a
git repo — so any coordination assets you put there (`CLAUDE.md`, skills, notes, memory)
**don't sync** to other machines. Only the work *inside the repos* travels. Push the
assets *into* a repo and they sync, but then Claude doesn't discover them when you launch
from the parent. You're stuck choosing between **discoverability** and **portability**.

## 2. The solution in one paragraph

Make the parent folder an **umbrella git repo**. It **gitignores** the nested working
repos (so it never tracks their files) and instead version-controls a `.claude/`
coordination layer plus a `CLAUDE.md`. You **always launch Claude from the umbrella root**,
which makes the umbrella's tooling authoritative while still letting per-repo context and
skills load on demand as you work inside each sub-repo. Memory is relocated *into* the
umbrella repo and kept machine-correct by a tiny self-healing hook — so it's both
version-controlled *and* portable.

```
<UMBRELLA>/                 ← umbrella git repo (the coordination layer)
├── .claude/                ← shared tooling: rules, skills, memory, settings, hooks
├── CLAUDE.md               ← project-wide context + working rules
├── README.md
├── docs/                   ← technical wiki (see doco-setup)
├── .gitignore              ← ignores <REPO_A>/, <REPO_B>/, CLAUDE.local.md
├── <REPO_A>/               ← nested working repo (own remote; gitignored here)
└── <REPO_B>/               ← nested working repo (own remote; gitignored here)
```

---

## 3. WHY it's shaped this way — Claude Code discovery rules

The placement decisions are not arbitrary; they follow directly from how Claude Code
discovers assets relative to the **launch directory**. Verify against current docs, but as
of writing:

| Asset | Discovered in a **nested** sub-repo's `.claude/` when launched from the umbrella? | Mechanism |
|---|---|---|
| **Skills** | ✅ yes — *on demand* | loaded when Claude touches a file in that sub-repo (monorepo support); git status irrelevant |
| **`CLAUDE.md`** | ✅ yes — *lazy* | loaded when Claude reads a file in that sub-repo |
| **Rules** (`.claude/rules/`) | ⚠️ don't rely on nested discovery | BUT a rule at the umbrella root with a `paths:` glob *does* fire on sub-repo files |
| **Agents** (`.claude/agents/`) | ❌ no | only the launch-dir's agents are discovered |
| **Settings** (`.claude/settings.json`) | ❌ no | settings load only from the launch dir (not inherited/nested) |
| **Memory** | ❌ no | tied to the launch-dir's project |

**The rule of thumb:** *skills and `CLAUDE.md` follow you down into sub-repos; agents,
settings, rules, and memory stay at the umbrella top.* This asymmetry is the entire reason
for **"always launch from the umbrella."** Launch inside a sub-repo and you silently lose
the umbrella's agents, settings, rules, and shared memory. (It's also why each sub-repo's
`CLAUDE.md` carries an **up-pointer** to the umbrella — see the cascade sub-pattern, §6 Step 7.)

---

## 4. Division of labour — where each asset lives

| Asset | Lives in | Notes |
|---|---|---|
| Project-wide `CLAUDE.md` | umbrella root | always loaded |
| Repo-specific `CLAUDE.md` | each sub-repo root | lazy-loaded when you work in that repo |
| Repo-specific skills | the sub-repo's `.claude/skills/` | on-demand; travels with that repo |
| Cross-project skills | umbrella `.claude/skills/` | always available from the umbrella |
| Rules | umbrella `.claude/rules/` (scope with `paths:`) | target sub-repo files via globs |
| Agents | umbrella `.claude/agents/` | must be at the top to fire |
| Settings | umbrella `.claude/settings.json` (+ machine-local `settings.local.json`) | only the umbrella's load |
| Memory | umbrella `.claude/memory/` (redirected — see [memory-setup](../_sub_patterns/memory-setup/memory-setup.md)) | version-controlled + portable |
| Docs | umbrella `docs/` (+ `README.md`, `MEMORY`) | the four doc surfaces — see [doco-setup](../_sub_patterns/doco-setup/doco-setup.md) |

---

## 5. The standard `.claude/` skeleton (every repo)

Give **every** repo (umbrella *and* each sub-repo) the same uniform `.claude/` skeleton, so structure
is predictable and ready even where a slot is empty. This is the
**[dot-claude-setup](../_sub_patterns/dot-claude-setup/dot-claude-setup.md)** sub-pattern — run it per
repo (Step 4). It lays the `.gitkeep`'d folder tree (`rules/`, `skills/`, `agents/`, `agent-memory/`,
`agent-memory-local/`, `output-styles/`, `hooks/`), the machine-local `.claude/.gitignore`, a minimal
`settings.json`, a `.claude/README.md` signpost, and a bare `CLAUDE.md` placeholder.

The **umbrella** additionally holds the *live* assets the skeleton leaves as placeholders: a real
`settings.json` (with the `SessionStart` memory hook — wired by
[memory-setup](../_sub_patterns/memory-setup/memory-setup.md)), `settings.example.json` (inert
reference), real `rules/`, the vendored memory hook in `.claude/hooks/`, `memory/`, `docs/`,
`.mcp.json`, the root `.gitignore`, the project-wide `CLAUDE.md`, and `README.md`. (The example-file
discipline — inert examples only, no example *rule*, catalogue in `settings.example.json` — lives in
the sub-pattern.)

---

## 6. Setup playbook (do these in order)

> **How to run it.** A **single agent** executes these steps **in order**. The memory,
> documentation, and cascade steps are **delegated to sub-pattern recipes** — but the *same*
> agent carries them out inline (reading and following each sub-pattern doc), **not** spawned as
> parallel sub-agents: the sub-patterns share files (`CLAUDE.md`, `settings.json`) and have
> ordering dependencies, so linear execution avoids write races and keeps the end state coherent.
> **No step commits.** The sub-patterns deliberately defer committing; the agent makes a
> **single commit per repo at the very end** (Step 10).
>
> *(At scale — many sub-repos — the one step worth fanning out is the purely repo-local skeleton
> creation in Step 4, since those trees are disjoint. Keep all umbrella-level edits in the main
> agent.)*

### Step 1 — Create the umbrella repo
Create an empty git repo `<UMBRELLA>` with a remote, clone it, `cd` in.

### Step 2 — Clone the working repos *inside* the umbrella
```bash
cd <UMBRELLA>
git clone <REPO_A_URL>
git clone <REPO_B_URL>
```
> Folder names matter — the `.gitignore` excludes them by exact name.

### Step 3 — Gitignore the working repos
Add the umbrella root `.gitignore` (template in §9) excluding each sub-repo **by exact name**
plus `CLAUDE.local.md`. Verify: `git status` should NOT list the sub-repos, and
`git check-ignore -v <REPO_A>` should match.

### Step 4 — Scaffold the `.claude/` skeleton in every repo  ← run the sub-pattern
Run [dot-claude-setup](../_sub_patterns/dot-claude-setup/dot-claude-setup.md) for the umbrella **and**
each sub-repo. It's idempotent (create-what's-missing, never clobber), so existing real skills are
untouched. It lays the uniform `.claude/` skeleton + a bare `CLAUDE.md` placeholder; the umbrella's
live `settings.json` memory hook is added next by memory-setup (Step 5).

### Step 5 — Portable, self-healing memory  ← run the sub-pattern *(the keystone)*
Follow **[memory-setup](../_sub_patterns/memory-setup/memory-setup.md)**: vendor the Node
`ensure-repo-memory.mjs` hook into `<UMBRELLA>/.claude/hooks/`, wire it as a `SessionStart` hook in
`settings.json`, gitignore `settings.local.json`, and create `.claude/memory/` + an explicit
`MEMORY.md`. This is the keystone that makes memory **version-controlled *and* portable**. The
sub-pattern owns the full mechanism, the **Node prerequisite** check, the new-machine flow, and
(optionally) migrating + SHA-256-verifying existing memory.

### Step 6 — Documentation surfaces  ← run the sub-pattern
Follow **[doco-setup](../_sub_patterns/doco-setup/doco-setup.md)**: establish the four doc surfaces
(`README.md`, `CLAUDE.md`, `MEMORY`, `docs/`), vendor `doco-structure.md` into `<UMBRELLA>/docs/`,
and **author the umbrella's `README.md` and `CLAUDE.md` body** (project-wide context + standing
working rules). MEMORY is the Step 5 sibling; this step just leaves `CLAUDE.md` pointing at it.

### Step 7 — `CLAUDE.md` cascade  ← run the sub-pattern
Follow **[umbrella-claude-md-cascade](../_sub_patterns/umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md)**:
add the **down-signpost** to the umbrella `CLAUDE.md` (plain links to every sub-repo's `CLAUDE.md`,
**never `@imports`**) and an **up-pointer** to each sub-repo `CLAUDE.md`, creating any missing
sub-repo `CLAUDE.md`. It's idempotent and order-independent — **re-run it whenever a sub-repo is
added**. (Runs *after* doco-setup so it augments the authored `CLAUDE.md` rather than colliding with
its creation.)

### Step 8 — Project-wide rules
Put cross-cutting rules in `<UMBRELLA>/.claude/rules/<name>.md`, scoped with a `paths:` glob so they
fire across all repos. Vendor the library's
[`rules/coding-principles.md`](../../rules/coding-principles.md) as the standard one — it's already
`paths:`-scoped to code files (caution-over-speed coding guidelines). Add any project-specific rules
the same way; rules auto-fire by their glob, with no `settings.json` wiring. (See
[rules/README.md](../../rules/README.md) for placement — rules load from the launch-dir root, so keep
them at the umbrella and let the glob reach sub-repo files.)

### Step 9 — Bring in existing reusable skills  ← run the sub-pattern
Skills are **vendored** (committed per-repo), so a new project starts with an empty `.claude/skills/`.
Run [skill-vendoring](../_sub_patterns/skill-vendoring/skill-vendoring.md) to bring in the reusable
skills the user wants — it asks which to vendor and where each source is, copies each **verbatim**
(whole folder, every supporting file), checks any runtime prerequisites, and verifies discovery.
Supply the **placement** per §4: cross-project / utility skills → `<UMBRELLA>/.claude/skills/`;
repo-specific skills → that sub-repo's `.claude/skills/`. *(The Node memory hook is vendored by Step 5
— no need to request it.)*

### Step 10 — Verify end-to-end, then commit (the single commit)
- **Memory test:** put a unique marker line at the top of `.claude/memory/MEMORY.md`, open a
  **fresh session from the umbrella**, and ask Claude to recall it. If it knows it and reports its
  memory path as `<UMBRELLA>/.claude/memory/`, the redirect is live. Remove the marker.
- **Cascade check:** every sub-repo is linked from the umbrella `CLAUDE.md`; each sub-repo
  `CLAUDE.md` points up; no `@imports` anywhere.
- **Commit** the umbrella and each sub-repo **separately** (they're independent repos). This is the
  **one** commit the whole setup makes — every sub-pattern step deliberately left committing to
  here. Confirm machine-local files (`settings.local.json`, `CLAUDE.local.md`, `agent-memory-local/`)
  are NOT staged.

---

## 7. The golden rule

**Always launch Claude with `<UMBRELLA>` as the workspace root — even when editing inside a
sub-repo.** Skills and `CLAUDE.md` still cascade down to wherever you're working, so you get
everything: the umbrella's shared layer *plus* each sub-repo's own context on demand.

---

## 8. Gotchas checklist

- [ ] Launch from the **umbrella**, not a sub-repo, and not the parent of the umbrella.
- [ ] Sub-repo folder names must match the `.gitignore` entries exactly.
- [ ] Run the sub-patterns **linearly (one agent)**; they share files and must not race.
- [ ] **Node is a prerequisite** for the memory hook — `memory-setup` checks `node --version` and
      prompts to install if absent. Confirm it before relying on the hook.
- [ ] `autoMemoryDirectory` lives in **`settings.local.json`** (gitignored), never committed.
- [ ] Accept the **workspace-trust** prompt on a new machine; **relaunch once** after the first heal.
- [ ] No **example rule** in `rules/` (rules auto-fire). Examples only for inert asset types.
- [ ] `settings.json` is **live** — keep it real; put the catalogue in `settings.example.json`.
- [ ] Memory migration: **verify SHA-256** and **commit** before deleting any source (see memory-setup).
- [ ] No `@imports` in the cascade — plain links only (eager vs lazy; see cascade sub-pattern).
- [ ] Vendored skills don't auto-arrive in a *new* project — **request the user's reusable skills**
      and copy them in, placed per §4 (Step 9).
- [ ] Commit each repo **separately** — they're independent git repositories — and only **once**, at
      the end.

---

## 9. Appendix — file templates

The memory hook, its `settings.json` wiring, and the documentation templates live in their
sub-patterns ([memory-setup](../_sub_patterns/memory-setup/memory-setup.md),
[doco-setup](../_sub_patterns/doco-setup/doco-setup.md)). Only the umbrella-specific `.gitignore`
templates are here.

### `<UMBRELLA>/.gitignore`
```gitignore
# Nested working repos — version-controlled independently by their own remotes.
/<REPO_A>/
/<REPO_B>/

# Personal, machine-local instructions — not synced.
/CLAUDE.local.md
```

### `<repo>/.claude/.gitignore` (every repo)
```gitignore
# Personal / machine-local Claude assets — never synced across machines.
settings.local.json
agent-memory-local/
```
> `settings.local.json` is required by [memory-setup](../_sub_patterns/memory-setup/memory-setup.md)
> (it holds the machine-specific `autoMemoryDirectory`); the rest is general machine-local hygiene.

---

## 10. TL;DR

1. Umbrella git repo on top; clone the working repos **inside** it; **gitignore** them.
2. Every repo gets the standard `.claude/` skeleton; the umbrella holds the live assets.
3. **Memory** → run [memory-setup](../_sub_patterns/memory-setup/memory-setup.md) (Node hook +
   `settings.local.json` redirect; version-controlled + portable).
4. **Docs** → run [doco-setup](../_sub_patterns/doco-setup/doco-setup.md) (README / CLAUDE.md /
   MEMORY / docs); **cascade** → run
   [umbrella-claude-md-cascade](../_sub_patterns/umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md)
   (down-signpost + up-pointers, plain links).
5. Rules/agents/settings/memory live at the umbrella; skills + `CLAUDE.md` cascade down.
6. **Skills** → run [skill-vendoring](../_sub_patterns/skill-vendoring/skill-vendoring.md) — ask the
   user for them and copy verbatim (skills don't auto-arrive in a new project).
7. **One agent, linear; one commit per repo at the end. Always launch from the umbrella.** New
   machine = clone, trust, relaunch once.
