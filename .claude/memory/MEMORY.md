# Memory index

Durable, version-controlled memory for the **ClaudePatternsAndSkills** library — decisions and
agreements worth recalling across sessions ("principles, not state"). One line per memory; the topic
files hold the detail. Claude loads this index at session start and reads topic files on demand.

- [memory hook is Node](memory-hook-is-node.md) — the portable-memory SessionStart hook is a Node `.mjs` (`node <file>` = identical cross-platform command).
- [vendoring model](vendoring-model.md) — reusable assets are vendored (copied) into repos, not installed from a manifest; revisit at scale.
