---
name: vendoring-model
description: Reusable assets are vendored (copied) into consuming repos, not installed from a manifest/marketplace — for now.
metadata:
  type: project
---

Skills, hooks, and pattern assets are **vendored**: a pattern copies the asset into the target repo
(e.g. `.claude/skills/`, `.claude/hooks/`). There is no central install step.

**Why:** vendoring gives zero-setup, offline-capable, self-contained repos that work the moment they're
cloned. The cost is **drift** — improving a master means re-copying it into consumers (tracked via
version stamps). The manifest alternative (Claude Code plugins + marketplaces) adds a per-machine
trust/install step and a network dependency, so it's deferred.

**How to apply:** vendor assets into target repos; when a master improves, re-copy it into the repos
that use it. Revisit a manifest/marketplace only once many repos share an asset and drift becomes a
real burden. See [[memory-hook-is-node]] for an asset that follows this model.
