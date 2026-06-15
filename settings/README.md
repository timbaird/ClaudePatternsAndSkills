# settings — reusable `settings.json` templates

Pre-made, reviewed **permission-profile** fragments for a repo's `.claude/settings.json`. The
[settings-setup](../_patterns/_sub_patterns/settings-setup/settings-setup.md) sub-pattern asks the user
two questions (git autonomy, permission model) and **merges** the matching profile's `permissions`
block into `settings.json` — config-by-template, not config authored freehand.

> **Merge, don't overwrite.** `settings.json` is shared: `dot-claude-setup` lays `$schema`,
> `memory-setup` merges `hooks.SessionStart`. These templates contribute only the `permissions` key —
> copy that block in and leave the others intact.

## Profiles

| Profile | `defaultMode` | Summary |
|---|---|---|
| [permissions-strict](permissions-strict.json) | `default` | Ask before every action; only a dangerous-paths deny baseline. Maximum control, maximum friction. |
| [permissions-readonly](permissions-readonly.json) | `default` | **Recommended default.** Common read-only commands (`ls`/`cat`/`grep`/`rg`/git-read-only) auto-approved; writes, installs, network, and state-changing git still prompt. |
| [permissions-open](permissions-open.json) | `bypassPermissions` | Auto-approve everything (a defence-in-depth deny baseline is kept). **Not a default** — sandboxes / fully-isolated environments only. |

## Notes

- **Syntax** (confirmed against working configs): `Bash(cmd)` = exact command, `Bash(cmd:*)` = command
  plus any arguments, `Read(./**)` = gitignore-style globs. **`deny` overrides `allow`**, and overrides
  `bypassPermissions`. `defaultMode`: `default` | `acceptEdits` | `plan` | `dontAsk` | `bypassPermissions`.
- The read-only profile deliberately **omits `find` and `env`** — `find -delete`/`-exec` can mutate and
  `env` can dump secrets. Add `Bash(find:*)` / `Bash(env)` yourself if you want them.
- The deny baselines are chosen so they don't block what `memory-setup`'s hook runs each session
  (`node`, `git rev-parse`, writing `settings.local.json`) — the self-heal keeps working.
- `settings-setup` tunes the chosen profile by the git answer (auto-execute adds git-write commands to
  `allow`; ask / self-manage leave them out so they prompt).
