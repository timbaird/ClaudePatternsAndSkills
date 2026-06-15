# Sub-pattern — Portable, self-healing repo memory

A reusable recipe that relocates a repo's Claude Code **auto-memory into the repo itself**
(`<REPO>/.claude/memory/`) so memory is version-controlled and travels between machines — and keeps
each machine pointed at it automatically, every session.

> **Sub-pattern** = a composable building block referenced by full patterns rather than used alone.
> Referenced by: [umbrella-repo](../../umbrella-repo/umbrella-repo-setup.md) (and any single-repo
> setup that wants portable memory). Sibling of
> [dot-claude-setup](../dot-claude-setup/dot-claude-setup.md),
> [doco-setup](../doco-setup/doco-setup.md),
> [umbrella-claude-md-cascade](../umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md),
> [skill-vendoring](../skill-vendoring/skill-vendoring.md),
> [project-discovery](../project-discovery/project-discovery.md), and
> [settings-setup](../settings-setup/settings-setup.md). Placeholder: `<REPO>` = the target repo's
> root.

## Why

Claude's auto-memory normally lives **outside** any repo (in `~/.claude/projects/…`), so it never
syncs — move to another machine and it's gone. This relocates it *into* the repo (git-tracked) and
re-points each machine at it automatically.

## The mechanism (three parts)

1. **Memory files** live in `<REPO>/.claude/memory/` — committed, synced via git.
2. **Redirect:** `autoMemoryDirectory` in `<REPO>/.claude/settings.local.json` points Claude's
   auto-memory at that folder. **Machine-local + gitignored** — the value is an absolute path that
   differs per machine.
3. **Per-session preflight:** a **`SessionStart` hook** runs a small **Node** script
   (`ensure-repo-memory.mjs`) at the start of *every* session. It verifies the redirect and
   re-establishes it if missing (fresh machine) or wrong. Idempotent — prints `OK` and changes
   nothing when already correct.

**Why Node:** the hook command must be **identical on every OS** (it's committed in `settings.json`
and travels to Windows/macOS/Linux clones alike). `node <file>` is the *only* invocation that's
byte-identical across all three — shell commands (`powershell`/`bash`) and `python3` are not
(`python3` is even a broken Store-alias on Windows). One `.mjs`, one command, every platform.

## Prerequisite: Node

The hook runs via `node`, and **Node is not guaranteed** — Claude Code's *native installer* doesn't
include it (only the legacy npm install does). So Node is a **prerequisite** this pattern must
verify:

- **Check** `node --version`.
- **If missing, PROMPT the user for permission to install it** (do **not** silently install) — then
  install via the platform's package manager (`winget`/`choco` on Windows, `brew` on macOS, the
  distro's manager on Linux), or have the user do it.
- Only proceed once `node` is confirmed present.

## Required assets — provisioning manifest

| Asset | Type | Source | Destination |
|---|---|---|---|
| `ensure-repo-memory.mjs` | Node hook script (vendored) | [`hooks/ensure-repo-memory.mjs`](../../../hooks/ensure-repo-memory.mjs) | `<REPO>/.claude/hooks/ensure-repo-memory.mjs` |
| SessionStart hook | `settings.json` fragment (**merge**) | inline (below) | `<REPO>/.claude/settings.json` → `hooks.SessionStart` |
| `settings.local.json` ignore | `.gitignore` line | inline (below) | `<REPO>/.claude/.gitignore` |
| memory folder | folder (+ optional migrated files) | new / migration | `<REPO>/.claude/memory/` (committed) |

> **Composes with [dot-claude-setup](../dot-claude-setup/dot-claude-setup.md):** if you ran the
> skeleton sub-pattern first, a base `settings.json` and `.claude/.gitignore` already exist — the
> steps below *merge into* them. Run in either order; the create-if-missing / merge-if-present steps
> handle both.

### SessionStart hook — `<REPO>/.claude/settings.json`
If the file doesn't exist, create it as below. If it exists, merge the `hooks.SessionStart` block in
(append to the array if `SessionStart` already has hooks; leave other keys untouched).
```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "node .claude/hooks/ensure-repo-memory.mjs", "timeout": 15 }
        ]
      }
    ]
  }
}
```
> The command is the **same on every OS** — no per-OS variants, no shell selection.

### `.claude/.gitignore` — one entry this pattern needs
```gitignore
settings.local.json
```
> The only line memory-setup requires: `settings.local.json` holds the machine-specific absolute
> path and must never commit. (`.claude/memory/` is the opposite — it *is* committed.) Other
> skeleton entries like `agent-memory-local/` are unrelated; leave them alone.

## Provisioning steps (ordered)

1. **Confirm Node.** Run `node --version`. If absent, **ask the user for permission to install Node**,
   install it (platform package manager) or have them do it, and re-check. Do not proceed without it.
2. **Copy the hook script** from this library's master — `hooks/ensure-repo-memory.mjs` → 
   `<REPO>/.claude/hooks/ensure-repo-memory.mjs`.
3. **Wire the hook:** merge the SessionStart fragment above into `<REPO>/.claude/settings.json`
   (committed, so it travels and fires on a fresh clone's first session).
4. **Gitignore** `settings.local.json` in `<REPO>/.claude/.gitignore` (add the line if absent).
5. **Create** `<REPO>/.claude/memory/` and add a **`MEMORY.md`** — the memory index Claude loads at
   session start (start it with a one-line header; topic files get added over time). The hook also
   creates the `memory/` folder if absent, but `MEMORY.md` must exist so the folder is git-tracked
   and there's an index to load.
6. *(Optional)* **migrate** existing memory — see below.
7. **Launch Claude from `<REPO>`** → the hook runs the script → it writes `autoMemoryDirectory` and
   prints `FIXED … RELAUNCH REQUIRED` → **relaunch once**. Every session after, it prints `OK`
   silently.

> **Don't commit here.** This is a *sub-pattern* — one component of a larger setup. Committing is
> **not** part of it: the calling pattern commits **once, after the full setup is complete**.
> Committing a half-finished setup mid-process is the wrong granularity.

## Per-session preflight (steady state)

Because it's a `SessionStart` hook, the check runs as a **preflight on every session** — not just at
setup. In steady state it silently confirms `OK`; on a fresh machine (or if the path drifts) the same
preflight self-heals and asks for a one-time relaunch. Nothing to remember to run.

## New-machine flow

Clone → (ensure `node` present) → launch from `<REPO>` → hook sets the path → relaunch once → memory
loads from the repo. The hook script and its `settings.json` wiring are both **committed**, so the
preflight arrives with the clone; only `node` itself may need installing once.

## (Optional) migrate existing memory

If the repo previously had memory under the old default (`~/.claude/projects/<old-key>/memory/`),
copy those `.md` files into `<REPO>/.claude/memory/` and **verify byte-for-byte (e.g. SHA-256 per
file)** before trusting it; only delete the source after the copy is confirmed faithful *and
committed*.

## Verify it's live

Put a unique marker line at the top of `<REPO>/.claude/memory/MEMORY.md`, open a **fresh session from
`<REPO>`**, and ask Claude to recall it (and report its memory path). If it knows the marker *and* its
memory path is `<REPO>/.claude/memory/`, the redirect is working. Remove the marker afterward.

## Why `settings.local.json` (not committed `settings.json`)

`autoMemoryDirectory` accepts only an **absolute** path, which would be wrong on every other machine
if committed. The gitignored `settings.local.json` lets each machine hold its own correct path; the
hook writes it automatically, so there's no manual per-machine editing. (The *hook* that writes it
lives in committed `settings.json` — that's what must travel.)

## Vendoring note

The hook script is **vendored** (committed in the repo's `.claude/hooks/`) so it's self-contained and
offline-capable; the cost is **drift** — when the master at
[`hooks/ensure-repo-memory.mjs`](../../../hooks/ensure-repo-memory.mjs) improves, re-copy it into the
repos that use it.
