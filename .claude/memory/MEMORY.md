# Memory index

Durable, version-controlled memory for the **ClaudePatternsAndSkills** library — decisions and
agreements worth recalling across sessions ("principles, not state"). One line per memory; the topic
files hold the detail. Claude loads this index at session start and reads topic files on demand.

- [memory hook is Node](memory-hook-is-node.md) — the portable-memory SessionStart hook is a Node `.mjs` (`node <file>` = identical cross-platform command).
- [vendoring model](vendoring-model.md) — reusable assets are vendored (copied) into repos, not installed from a manifest; revisit at scale.
- [doc-discipline is universal](doc-discipline-universal.md) — universal discipline lives always-on in `CLAUDE.md`, not a `paths:`-scoped rule (those need a real "off" state, e.g. code).
- [docs-surface conventions](docs-surface-conventions.md) — one `docs/` at the top level only (umbrella-only in multi-repo); `docs/INDEX.md` is required-reading via a `CLAUDE.md` pointer (not auto-loaded like MEMORY).
- [skill-dependencies convention](skill-dependencies-convention.md) — third-party-dep skills carry a per-skill gitignored `.venv` (never vendored); the convention doc is vendored everywhere, the `ensure-python` hook ships everywhere but is wired only when a Python skill is present.
- [settings are template-driven](settings-template-driven.md) — permissions applied by merging a pre-made `settings/` template, not authored freehand; colon syntax; preserve the memory hook.
- [external-asset vendoring](external-asset-vendoring.md) — scan small markdown assets in full on intake, then vendor with provenance; keep the "Prompt Defense Baseline" block; flag modified assets.
- [ECC mining + AgentShield](ecc-mining-and-agentshield.md) — ECC is a quarry not a dependency; AgentShield shelved (pin-the-package-don't-fork if revisited).
