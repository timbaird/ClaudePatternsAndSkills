# hooks — reusable hook scripts

Cross-platform hook scripts, **wired into a repo's `.claude/settings.json`** (they are *not* invoked
as skills). A pattern vendors the script into the target repo's `.claude/hooks/` and adds the matching
hook entry to `settings.json`.

> **Runtime: Node.** These are `.mjs` files run via `node <file>` — the one invocation that's
> **identical on Windows/macOS/Linux**, so a single committed hook command works everywhere (shell
> commands and `python3` are not portable as committed hook commands). **Node is a prerequisite**: it
> is *not* bundled with Claude Code's native installer, so a pattern using these must check for `node`
> and prompt to install it if absent.

## Catalogue

| Hook | Runtime | Summary |
|---|---|---|
| [ensure-repo-memory.mjs](ensure-repo-memory.mjs) | Node | Per-session preflight: points this repo's Claude auto-memory at `.claude/memory/` by setting `autoMemoryDirectory` in `settings.local.json` (idempotent self-heal). Used by the [memory-setup sub-pattern](../_patterns/_sub_patterns/memory-setup/memory-setup.md). |
| [ensure-python.mjs](ensure-python.mjs) | Node | Per-session preflight: confirms a usable **Python 3** (≥3.9) is on PATH, since a project's Python skills depend on it. Silent on success; on a miss surfaces install guidance into the session (advisory, never blocks). Wired when a project carries a Python skill — see the [skill-dependencies convention](../_patterns/_sub_patterns/doco-setup/skill-dependencies.md) + [skill-vendoring](../_patterns/_sub_patterns/skill-vendoring/skill-vendoring.md). |

### GHL social-integration hooks

The three hooks below support the **GHL (GoHighLevel) Social Planner** integration — pair them with the
[`schedule-social`](../skills/schedule-social/) skill and the [integration guide](../docs/ghl-social-integration.md).
Config-driven (repo-root `distribution.yaml` + `channels/<slug>/distribution.yaml`); secrets from `.env`; no ids baked in.

| Hook | Runtime | Wiring | Summary |
|---|---|---|---|
| [ghl-mcp-headers.mjs](ghl-mcp-headers.mjs) | Node | `headersHelper` in `.mcp.json` | Emits the `Authorization: Bearer <PIT>` header for the GHL MCP server(s), reading the PIT from `.env` directly (Claude Code's `${VAR}` expansion doesn't see the project `.env` → empty Bearer → `Invalid JWT`; this fixes it). Picks read/write PIT by `CLAUDE_CODE_MCP_SERVER_NAME`. Emits `{}` (no auth) on any failure — never leaks. |
| [ghl-write-guard.mjs](ghl-write-guard.mjs) | Node | `PreToolUse` (`mcp__ghl-social-write__.*`) | **Fail-closed** composite-key guard: blocks any GHL write whose target account id isn't on the working channel's `distribution.yaml` allowlist (pinned by `platform + native_id`). Silent when authorised (normal permission flow proceeds); hard-blocks on any uncertainty. |
| [ghl-token-health.mjs](ghl-token-health.mjs) | Node | `SessionStart` | Read-only sweep of the connected GHL social accounts' token expiries → one status line (next expiry, any needing reconnect). Never blocks, never prints the token; SKIPs quietly if unconfigured/offline. |

## Using a hook

1. Confirm `node` is present (install if not).
2. Vendor the `.mjs` into `<repo>/.claude/hooks/`.
3. Wire it in `<repo>/.claude/settings.json`:
   ```json
   { "type": "command", "command": "node .claude/hooks/<hook>.mjs", "timeout": 15 }
   ```
   under the appropriate event (e.g. `hooks.SessionStart`).
