---
name: ecc-mining-and-agentshield
description: ECC is mined (vendor individual scanned assets), not adopted wholesale. AgentShield is shelved — if revisited, pin the npm package, don't fork it.
metadata:
  type: project
---

Everything Claude Code (ECC, `affaan-m/ECC`, MIT) is treated as a **quarry**, not a dependency: vendor
individual, scanned-on-intake assets (so far: `code-reviewer`, `silent-failure-hunter`,
`code-simplifier`, `skill-scout`, `search-first`), never adopt the whole system.

**Why:** ECC's memory is home-scoped (`~/.claude`) — it *conflicts* with our portable in-repo memory —
and it's the plugin/marketplace (manifest) model we deliberately deferred. Full adoption inverts CPAS's
minimal/owned ethos. **AgentShield** (its `.claude/` config security scanner, npm `ecc-agentshield`,
separate repo) is **shelved**: it's a ~30k-LOC TypeScript *platform* (the static scan is one of ~15
commands), so reviewing-to-trust the whole thing is disproportionate.

**How to apply:** to revisit AgentShield, **pin an exact npm version, review `src/rules/`, and run its
test suite** (~1–2 hrs) — do NOT fork/prune the source. ECC's language/domain skills are documented in
`resources.md` for on-demand pull, not vendored up front. See [[external-asset-vendoring]],
[[vendoring-model]].
