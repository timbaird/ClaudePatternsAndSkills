---
name: memory-hook-is-node
description: The portable-memory SessionStart hook is a Node .mjs, run via `node <file>` — chosen for an identical cross-platform command.
metadata:
  type: project
---

The `ensure-repo-memory` preflight runs as a `SessionStart` hook invoked with
`node .claude/hooks/ensure-repo-memory.mjs` — one committed command, byte-identical on
Windows/macOS/Linux.

**Why:** a committed hook command must be identical across OSes, and `node <file>` is the only
invocation that is. `python3` is a Microsoft Store-alias *stub* on Windows (it's on PATH but fails when
run); `powershell`/`bash` aren't cross-platform. Node has to be treated as a prerequisite (it is *not*
bundled with Claude Code's native installer) — the [[vendoring-model]] memory-setup sub-pattern checks
for `node` and prompts to install it if absent.

**How to apply:** keep hook scripts as Node `.mjs` and the hook command as `node <file>`; never
reintroduce per-OS shell commands (`powershell`/`bash`/`python3`) as committed hook commands.
