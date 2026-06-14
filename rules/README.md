# rules — reusable `.claude/rules/` assets

Drop-in **rule** files that get vendored into a repo's `.claude/rules/`. A rule is a markdown file
with `paths:` frontmatter; Claude Code **auto-fires** it on any file matching the glob — no wiring in
`settings.json`, unlike [hooks](../hooks/README.md).

> **Placement matters.** A rule is discovered from the **launch directory's** `.claude/rules/`. In an
> umbrella-repo project, put rules at the **umbrella** root and scope them with a `paths:` glob so they
> reach files in the nested sub-repos too — nested sub-repo rules aren't reliably discovered. (See the
> umbrella pattern's discovery-rules table.)

## Catalogue

| Rule | Fires on | Summary |
|---|---|---|
| [coding-principles.md](coding-principles.md) | code files (`.py`, `.js`/`.ts`, `.go`, `.rs`, `.java`, `.sh`, `.sql`, … via `paths:` glob) | Caution-over-speed coding guidelines to reduce common LLM coding mistakes: think before coding, simplicity first, surgical changes, goal-driven execution. Adapted from the *andrej-karpathy-skills* guidelines. |

## Deploying a rule

1. Copy the rule's `.md` into `<repo>/.claude/rules/` (the umbrella/launch-dir root in a multi-repo
   project).
2. That's it — it fires automatically on files matching its `paths:` glob. Adjust the glob if a project
   uses languages/extensions the default list doesn't cover.

> **Don't leave an *example* rule in a live `.claude/rules/`** — rules auto-fire, so a placeholder
> becomes live noise. Vendor only rules you actually want active.
