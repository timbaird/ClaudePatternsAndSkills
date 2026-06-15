---
name: external-asset-vendoring
description: External skills/agents are scanned in full on intake (small markdown), then vendored with provenance, keeping ECC's "Prompt Defense Baseline" block.
metadata:
  type: project
---

Because a skill/agent is a small markdown file, the trust problem of large tools doesn't apply — **read
it in full on intake**, then vendor and own it. This is the agreed way to bring external assets in.

**Why:** "scan-on-intake then vendor" makes trust tractable for markdown assets, unlike a large tool
(see [[ecc-mining-and-agentshield]]).

**How to apply:** vendor verbatim where possible; add provenance (a `SKILL.md`/agent frontmatter
comment **and** a README) and, for external skills, an internal `version` tracking field (a re-vendor
marker, not our iteration). Keep an upstream's prepended **"Prompt Defense Baseline"** block
deliberately (generic injection defence). When an asset is **modified** from upstream (e.g.
`code-simplifier`'s added approval gate), flag it *modified* in its frontmatter comment + the
collection catalogue. See [[vendoring-model]].
