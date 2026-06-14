# The Multi-Repo "Umbrella" Pattern — Setup Specification

A reusable pattern for coordinating **multiple git repositories** under a single,
version-controlled **umbrella repo** that carries the shared Claude Code tooling
(`CLAUDE.md`, rules, skills, settings) and a **portable, self-healing memory**.

> This document is **generic and self-contained**. Another Claude session (or a person)
> can follow it to set up a brand-new project in this pattern. Placeholders:
> `<UMBRELLA>` = the umbrella repo name, `<REPO_A>`, `<REPO_B>`, … = the nested working
> repos. Commands assume **Windows + PowerShell + Git Bash** (the reference implementation);
> a "Porting" section covers other OSes.

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
umbrella repo and kept machine-correct by a tiny self-healing skill — so it's both
version-controlled *and* portable.

```
<UMBRELLA>/                 ← umbrella git repo (the coordination layer)
├── .claude/                ← shared tooling: rules, skills, memory, settings, hooks
├── CLAUDE.md               ← project-wide context + working rules
├── README.md
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
the umbrella's agents, settings, rules, and shared memory.

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
| Memory | umbrella `.claude/memory/` (redirected — see the [memory-setup sub-pattern](../_sub_patterns/memory-setup/)) | version-controlled + portable |

---

## 5. The standard `.claude/` skeleton (every repo)

Give **every** repo (umbrella *and* each sub-repo) the same skeleton, so structure is
uniform and ready to use even where a slot is currently empty. Empty folders are held by a
`.gitkeep`.

```
<repo>/
├── CLAUDE.md
└── .claude/
    ├── README.md                 # points to the umbrella .claude/README.md as the reference
    ├── .gitignore                # ignores: settings.local.json, agent-memory-local/
    ├── settings.json             # minimal real config (sub-repos: just {"$schema": …})
    ├── rules/.gitkeep
    ├── skills/.gitkeep           # (real skills replace the .gitkeep where used)
    ├── agents/.gitkeep
    ├── agent-memory/.gitkeep
    ├── agent-memory-local/.gitkeep   # gitignored — machine-local
    ├── output-styles/.gitkeep
    └── hooks/.gitkeep
```

The **umbrella** additionally holds the *live* assets: real `settings.json` (with the
memory hook), `settings.example.json` (inert reference), real `rules/`, the
`ensure-repo-memory` skill, `memory/`, `.mcp.json`, the root `.gitignore`, the project-wide
`CLAUDE.md`, and `README.md`.

> **Note on examples:** keep illustrative example files only where they're *inert* (skills,
> agents, output-styles, hooks, status-line — they do nothing until invoked/wired). Do NOT
> leave an example **rule** in `rules/` — rules auto-fire by `paths:` and a placeholder rule
> becomes live noise. And the **one** config that's always live is `settings.json`, so keep
> it real; put the "what's possible" catalogue in `settings.example.json` (which Claude
> Code never loads).

---

## 6. Setup playbook (do these in order)

### Step 1 — Create the umbrella repo
Create an empty git repo `<UMBRELLA>` with a remote, clone it, `cd` in.

### Step 2 — Clone the working repos *inside* the umbrella
```bash
cd <UMBRELLA>
git clone <REPO_A_URL>
git clone <REPO_B_URL>
```
> Folder names matter — the `.gitignore` excludes them by exact name.

### Step 3 — Gitignore the working repos (umbrella root `.gitignore`)
```gitignore
# Nested working repos — version-controlled independently by their own remotes.
/<REPO_A>/
/<REPO_B>/

# Personal, machine-local instructions — not synced.
/CLAUDE.local.md
```
Verify: `git status` should NOT list the sub-repos, and `git check-ignore -v <REPO_A>`
should match.

### Step 4 — Scaffold the umbrella `.claude/`
Create the standard skeleton (§5) plus the live assets. Key files in the appendix (§11):
`.claude/.gitignore`, `.claude/settings.json` (with the SessionStart memory hook),
`.claude/settings.example.json`, `.claude/README.md`. Recreate the `ensure-repo-memory`
skill from §11, and **request any other reusable skills from the user** to vendor here (§8a).

### Step 5 — Standard skeleton in each sub-repo
Add the §5 skeleton to `<REPO_A>/.claude/` and `<REPO_B>/.claude/`, **without disturbing
any existing real skills**. Create a `CLAUDE.md` stub in each sub-repo if absent.

### Step 6 — Cascading `CLAUDE.md`
- **Umbrella `CLAUDE.md`** holds project-wide context + standing working rules, and a lean
  signpost: *"Each sub-repo has its own `CLAUDE.md`, auto-loaded when Claude reads a file in
  that repo."* (Plain links, NOT `@imports` — imports load eagerly every session; plain
  links let the sub-repo file load lazily, on demand.)
- **Each sub-repo `CLAUDE.md`** holds only that repo's specifics. Lift anything project-wide
  *up* into the umbrella so nothing is duplicated.

### Step 7 — Project-wide rules
Put cross-cutting rules in `umbrella/.claude/rules/<name>.md`. Scope code-style rules with a
`paths:` glob so they fire across all repos, e.g.:
```yaml
---
description: Coding principles — applied when editing code (any language, any repo)
paths:
  - "**/*.{py,js,mjs,ts,tsx,astro,go,rs,java,c,cpp,rb,php,cs,sh,sql}"
---
```

### Step 8 — Portable, self-healing memory  ← the keystone
Set it up per the **[memory-setup sub-pattern](../_sub_patterns/memory-setup/)** — relocate memory
into `.claude/memory/`, redirect via `settings.local.json`, and self-heal with the
`ensure-repo-memory` skill + `SessionStart` hook. (Summary in §8.)

### Step 9 — (Optional) migrate existing memory
If this project had memory under the old default location
(`~/.claude/projects/<old-project-key>/memory/`), copy it into `umbrella/.claude/memory/`
and **verify byte-for-byte** (SHA-256 per file) before trusting it. Only delete the old
source after the copy is confirmed faithful *and committed*.

### Step 10 — Verify end-to-end, then commit
- **Memory test:** put a unique marker line at the top of `.claude/memory/MEMORY.md`, open a
  **fresh session from the umbrella**, and ask Claude to recall it. If it knows it and
  reports its memory path as the repo's `.claude/memory/`, the redirect is live. Remove the
  marker.
- **Commit** the umbrella and each sub-repo separately (they're independent repos). Confirm
  gitignored/machine-local files (`settings.local.json`, `CLAUDE.local.md`,
  `agent-memory-local/`) are NOT staged.

---

## 7. The golden rule

**Always launch Claude with `<UMBRELLA>` as the workspace root — even when editing inside a
sub-repo.** Skills and `CLAUDE.md` still cascade down to wherever you're working, so you get
everything: the umbrella's shared layer *plus* each sub-repo's own context on demand.

---

## 8. Portable, self-healing memory (the keystone mechanism)

Set this up per the **[memory-setup sub-pattern](../_sub_patterns/memory-setup/)** — the
canonical, reusable recipe. In brief, it relocates Claude's auto-memory *into*
`<UMBRELLA>/.claude/memory/` (version-controlled), redirects each machine to it via
`autoMemoryDirectory` in the gitignored `settings.local.json`, and keeps that pointer correct
automatically with the vendored `ensure-repo-memory` skill run by a `SessionStart` hook. It's the
keystone that makes the umbrella's memory both version-controlled and portable. See the sub-pattern
for the full mechanism, the new-machine flow, and the vendoring-vs-manifest trade-off.

---

## 8a. Bringing existing reusable skills into a new project

Because skills are **vendored** (committed per-repo), a session setting up a *new* project
starts with an **empty `.claude/skills/`**. It cannot magically have the reusable skills that
live in your *other* projects or your personal toolkit — so the setup session must
**request them from you**. Make this an explicit setup step.

**The setup session should:**

1. **Recreate `ensure-repo-memory` directly** — its full contents are in §11 of this spec, so
   no need to ask for it; the memory mechanism (§8) depends on it.
2. **Ask the user which other reusable skills to vendor**, e.g.:
   > *"Which of your existing reusable skills should I vendor into this project? For each, point
   > me at where it lives — a path in another local repo, a toolkit repo, or paste the
   > `SKILL.md` plus any scripts/`references/` — and I'll copy it in."*
3. **Place each correctly** (per §4): cross-project / utility skills → `<UMBRELLA>/.claude/skills/`;
   skills specific to one working repo → that sub-repo's `.claude/skills/`.
4. **Copy verbatim** — include every supporting file (scripts, `references/`), not just the
   `SKILL.md` — then sanity-check the skill is discovered.

> **Tip:** if you keep a **toolkit repo** of reusable skills, this collapses to one step —
> *"point me at `<toolkit>` and I'll vendor the skills you list."* That toolkit repo is the
> lightweight stand-in for a skill package manager until a native one exists, and it's the
> obvious home for this spec too.

---

## 9. Porting to macOS / Linux

The reference script is **PowerShell** and the hook command invokes `powershell`, so the
memory mechanism is Windows-bound as written. To support other OSes, provide a sibling
script (bash or Node) implementing the same three steps — **(1)** find the repo root
(`git rev-parse --show-toplevel`), **(2)** compute `<root>/.claude/memory`, **(3)** reconcile
`autoMemoryDirectory` in `.claude/settings.local.json` (preserving other keys; absolute path;
UTF-8 no-BOM) — and make the `SessionStart` hook command select the right interpreter per OS.
Node is the most portable interpreter (Claude Code runs on it), but may not be on `PATH`.

---

## 10. Gotchas checklist

- [ ] Launch from the **umbrella**, not a sub-repo, and not the parent of the umbrella.
- [ ] Sub-repo folder names must match the `.gitignore` entries exactly.
- [ ] `autoMemoryDirectory` lives in **`settings.local.json`** (gitignored), never committed.
- [ ] Accept the **workspace-trust** prompt on a new machine; **relaunch once** after the
      first heal.
- [ ] No **example rule** in `rules/` (rules auto-fire). Examples only for inert asset types.
- [ ] `settings.json` is **live** — keep it real; put the catalogue in `settings.example.json`.
- [ ] Memory migration: **verify SHA-256** and **commit** before deleting any source.
- [ ] Vendored skills don't auto-arrive in a *new* project — **request the user's existing
      reusable skills** and copy them in, placed per §4 (§8a).
- [ ] Commit each repo **separately** — they're independent git repositories.

---

## 11. Appendix — file templates

### `<UMBRELLA>/.gitignore`
```gitignore
/<REPO_A>/
/<REPO_B>/
/CLAUDE.local.md
```

### `<repo>/.claude/.gitignore` (every repo)
```gitignore
# Personal / machine-local Claude assets — never synced across machines.
settings.local.json
agent-memory-local/
```

### `<UMBRELLA>/.claude/settings.json` (live config + memory hook)
```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"${CLAUDE_PROJECT_DIR}/.claude/skills/ensure-repo-memory/ensure_repo_memory.ps1\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

### `<UMBRELLA>/.claude/skills/ensure-repo-memory/SKILL.md`
```markdown
---
name: ensure-repo-memory
description: >-
  Ensure this repository's Claude auto-memory is redirected into the version-controlled
  <repo-root>/.claude/memory folder (via autoMemoryDirectory in the machine-local
  settings.local.json). Idempotent, deterministic, machine-local — safe to run at the start
  of every session; re-running once configured is a cheap no-op.
model: haiku
shell: powershell
---

# Ensure repo memory

The script below does ALL the work (find repo root → compute the path → reconcile
settings.local.json). Relay its one-line result.

## Run the check

` ``!
powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/ensure_repo_memory.ps1"
`` `

## Act on the result
- `OK:`    → already configured. Continue silently.
- `FIXED:` → path just set for this machine. **Tell the user to relaunch before continuing.**
- `SKIP:`  → not applicable here (no .claude folder). Mention briefly and continue.
```
> (In a real file the fenced shell block is a single ```` ```! ```` … ```` ``` ```` block;
> it's spaced out above only to display inside this document.)

### `<UMBRELLA>/.claude/skills/ensure-repo-memory/ensure_repo_memory.ps1`
```powershell
# Idempotently point this repo's Claude auto-memory at <repo-root>/.claude/memory by setting
# `autoMemoryDirectory` in .claude/settings.local.json (machine-local, gitignored).
# Prints one STATUS line: OK | FIXED (relaunch) | SKIP.
$ErrorActionPreference = 'Stop'

# 1. Repo root (git if available, else current directory)
$root = $null
try { $root = (git rev-parse --show-toplevel 2>$null) } catch { $root = $null }
if (-not $root) { $root = (Get-Location).Path }
$root = [System.IO.Path]::GetFullPath($root)

$claudeDir    = Join-Path $root '.claude'
$memDir       = [System.IO.Path]::GetFullPath((Join-Path $claudeDir 'memory'))
$settingsPath = Join-Path $claudeDir 'settings.local.json'

if (-not (Test-Path $claudeDir)) { Write-Output "SKIP: no .claude folder at $root"; exit 0 }

# 2. Load (or init) settings.local.json, preserving existing keys (UTF-8 on read)
if (Test-Path $settingsPath) {
  try { $cfg = Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $cfg = [PSCustomObject]@{} }
} else {
  $cfg = [PSCustomObject]@{ '$schema' = 'https://json.schemastore.org/claude-code-settings.json' }
}

# 3. Compare to expected (case-insensitive, slash-normalised)
function Norm($p) { if (-not $p) { return '' } return ($p.TrimEnd('\','/').ToLower()) }
$current = $null
if ($cfg.PSObject.Properties.Name -contains 'autoMemoryDirectory') { $current = $cfg.autoMemoryDirectory }
if ((Norm $current) -eq (Norm $memDir)) { Write-Output "OK: repo memory already configured -> $memDir"; exit 0 }

# 4. Fix: ensure folder, set property, write UTF-8 WITHOUT BOM
if (-not (Test-Path $memDir)) { New-Item -ItemType Directory -Force -Path $memDir | Out-Null }
if ($cfg.PSObject.Properties.Name -contains 'autoMemoryDirectory') { $cfg.autoMemoryDirectory = $memDir }
else { $cfg | Add-Member -NotePropertyName 'autoMemoryDirectory' -NotePropertyValue $memDir }
$json = $cfg | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText($settingsPath, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output "FIXED: set autoMemoryDirectory -> $memDir in settings.local.json. RELAUNCH REQUIRED so memory loads from the repo."
exit 0
```

### Memory migration + verification (PowerShell)
```powershell
$src = '<OLD_DEFAULT_MEMORY_DIR>'                 # e.g. ~/.claude/projects/<old-key>/memory
$dst = '<UMBRELLA>/.claude/memory'
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item "$src\*" $dst -Force
# verify every file identical by SHA-256 before trusting / deleting the source
$bad = 0
Get-ChildItem $src -File | ForEach-Object {
  $a = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
  $b = (Get-FileHash (Join-Path $dst $_.Name) -Algorithm SHA256).Hash
  if ($a -ne $b) { $bad++; "DIFF $($_.Name)" }
}
if ($bad -eq 0) { "FAITHFUL COPY" } else { "PROBLEM: $bad differ" }
```

---

## 12. TL;DR

1. Umbrella git repo on top; clone the working repos **inside** it; **gitignore** them.
2. Every repo gets the standard `.claude/` skeleton; the umbrella holds the live assets.
3. Split `CLAUDE.md`: project-wide up top, repo-specific in each sub-repo (lazy-loaded).
4. Rules/agents/settings/memory live at the umbrella; skills + `CLAUDE.md` cascade down.
5. Relocate memory into `.claude/memory/` per the
   [memory-setup sub-pattern](../_sub_patterns/memory-setup/) — vendored `ensure-repo-memory` skill
   + `SessionStart` hook keep each machine pointed at it.
6. Vendor reusable skills — recreate `ensure-repo-memory` from §11, and **ask the user** for
   any others (skills don't auto-arrive in a new project).
7. **Always launch from the umbrella.** New machine = clone, trust, relaunch once.
