# agents — reusable subagent definitions

Drop-in **subagent** definitions (markdown + YAML frontmatter: `name`, `description`, `tools`,
`model`) that get vendored into a repo's `.claude/agents/`. Unlike skills (which load on demand) and
rules (which auto-fire), an agent is invoked explicitly via the Agent tool / a subagent call.

> **Placement.** Agents are discovered only from the **launch directory's** `.claude/agents/` — in an
> umbrella-repo project they must live at the **umbrella** root (they do *not* cascade into sub-repos).
> See the umbrella pattern's discovery-rules table.

## Catalogue

| Agent | Version | Tools | Origin | Summary |
|---|---|---|---|---|
| [code-reviewer](code-reviewer.md) | 1.0.0¹ | Read/Grep/Glob/Bash | ECC (vendored) | Senior code-review specialist — confidence-gated findings (>80%), explicit false-positive list, security/quality/perf/React/Node checklists, "zero findings is a valid review." |
| [silent-failure-hunter](silent-failure-hunter.md) | 1.0.0¹ | Read/Grep/Glob/Bash | ECC (vendored) | Hunts silent failures — empty catches, swallowed errors, dangerous fallbacks, lost stack traces, missing error propagation. Language-agnostic. |
| [code-simplifier](code-simplifier.md) | 1.0.0¹ | Read/Write/Edit/Bash/Grep/Glob | ECC (vendored, **modified**) | Proposes behaviour-preserving simplifications of recently changed code (clarity, early returns, dead-code removal). **Modified from upstream**: presents before/after diffs, discusses, and applies only what you approve — never auto-edits. |
| [doc-convention-auditor](doc-convention-auditor.md) | 1.0.0 | Read/Grep/Glob/Bash | Internal | Audits a project's documentation corpus against its own conventions — runs the `doc-convention-linter` for mechanical breaches, then applies judgment the linter can't (surface-fit, `CLAUDE.md`⇄`MEMORY` graduation, cross-ref quality, `doco-structure.md` adherence). Read-only; reports for a human. Pairs with the linter skill. |
| [doc-consistency-auditor](doc-consistency-auditor.md) | 1.0.0 | Read/Grep/Glob/Bash | Internal | Audits **code-vs-doc truth** — where a design doc states something as current fact that the code contradicts (a cited path/symbol/command gone, renamed, or mismatched). Flags only concrete, high-confidence drift; treats design-ahead and `[TBD]` as the doc doing its job, and surfaces stale code docstrings as a separate category. Read-only. The code-side complement to `doc-convention-auditor` (which never reads code). |
| [library-standards-auditor](library-standards-auditor.md) | 1.0.0 | Read/Grep/Glob/Bash | Internal | Audits a reusable library under `libraries/` against `library-standards.md` — runs the `library-standards-linter`, then adjudicates divergences (documented-and-justified vs undocumented gap), checks `CLAUDE.md` sections + the two required principles, README completeness, and reduced-set doc spirit. Structure/docs only (not the code). Read-only. Pairs with the linter skill. |

¹ Externally-created agent — the version is an *internal tracking* field recording when we re-vendor the
upstream, not our own iteration (intake noted in each agent's frontmatter comment). Internally-created
agents use the version to track *our* iteration.

## Provenance & the "Prompt Defense Baseline" block

The vendored agents come from [Everything Claude Code](../resources.md) (ECC, MIT) and were
**scanned in full on intake** (single-file instruction documents — no bundled code, no network calls,
no ECC-runtime coupling). Most are **verbatim**; `code-simplifier` is **modified** (an approval gate
added — it proposes and applies only what you approve, never auto-edits). Each carries a provenance
comment in its frontmatter.

They retain ECC's prepended **"Prompt Defense Baseline"** block — a short generic prompt-injection
guardrail. It's kept deliberately (verbatim + a reasonable defense); strip it if you'd rather a leaner
agent. The `version`/tracking convention for externally-sourced *skills* (re-vendor markers) applies
here too if these are updated upstream.

## Deploying an agent

Copy the agent's `.md` into `<repo>/.claude/agents/` (the umbrella/launch-dir root in a multi-repo
project). It's then available to invoke as a subagent.
