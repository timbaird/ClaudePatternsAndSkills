---
name: settings-template-driven
description: settings.json permissions are applied by selecting + merging a pre-made settings/ template (settings-setup), not authored freehand.
metadata:
  type: project
---

The `settings-setup` sub-pattern doesn't author `settings.json` permissions from scratch — it asks two
questions (git autonomy, permission model) and **merges a reviewed `settings/` permission template**
(`strict` / `readonly` / `open`) into the file.

**Why:** permissions are security-relevant, so pre-made reviewed templates are more deterministic and
auditable than freehand authoring. Permission syntax is the **colon form** — `Bash(cmd:*)` = command +
any args, `Bash(cmd)` = exact, `Read(./**)` globs, `deny` overrides `allow` (confirmed against real
working configs; the docs/WebFetch can mislead toward a space form).

**How to apply:** add new profiles as `settings/` assets; `settings-setup` merges only the
`permissions` block, **preserving** memory-setup's `hooks.SessionStart` (different keys → merge, never
overwrite), and the deny-list must not block the hook's `node`/`git` ops. See [[memory-hook-is-node]].
