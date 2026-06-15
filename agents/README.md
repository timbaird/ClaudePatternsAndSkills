# agents — reusable subagent definitions

Drop-in **subagent** definitions (markdown + YAML frontmatter: `name`, `description`, `tools`,
`model`) that get vendored into a repo's `.claude/agents/`. Unlike skills (which load on demand) and
rules (which auto-fire), an agent is invoked explicitly via the Agent tool / a subagent call.

> **Placement.** Agents are discovered only from the **launch directory's** `.claude/agents/` — in an
> umbrella-repo project they must live at the **umbrella** root (they do *not* cascade into sub-repos).
> See the umbrella pattern's discovery-rules table.

## Catalogue

| Agent | Tools | Origin | Summary |
|---|---|---|---|
| [code-reviewer](code-reviewer.md) | Read/Grep/Glob/Bash | ECC (vendored) | Senior code-review specialist — confidence-gated findings (>80%), explicit false-positive list, security/quality/perf/React/Node checklists, "zero findings is a valid review." |
| [silent-failure-hunter](silent-failure-hunter.md) | Read/Grep/Glob/Bash | ECC (vendored) | Hunts silent failures — empty catches, swallowed errors, dangerous fallbacks, lost stack traces, missing error propagation. Language-agnostic. |

## Provenance & the "Prompt Defense Baseline" block

The vendored agents are copied **verbatim** from [Everything Claude Code](../resources.md) (ECC, MIT),
**scanned in full on intake** (they're single-file instruction documents — no bundled code, no network
calls, no ECC-runtime coupling). Each carries a provenance comment in its frontmatter.

They retain ECC's prepended **"Prompt Defense Baseline"** block — a short generic prompt-injection
guardrail. It's kept deliberately (verbatim + a reasonable defense); strip it if you'd rather a leaner
agent. The `version`/tracking convention for externally-sourced *skills* (re-vendor markers) applies
here too if these are updated upstream.

## Deploying an agent

Copy the agent's `.md` into `<repo>/.claude/agents/` (the umbrella/launch-dir root in a multi-repo
project). It's then available to invoke as a subagent.
