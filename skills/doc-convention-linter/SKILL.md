---
name: doc-convention-linter
version: 1.0.0
description: |
  Deterministic linter for a project's documentation corpus. Run it to surface the
  *mechanically decidable* documentation problems — broken relative links,
  docs missing from their INDEX, orphaned docs, non-kebab-case filenames, missing
  H1 / summary blocks, and "document what WAS" trigger phrases. Use before
  committing documentation changes, when auditing the docs, or as the first step
  of the doc-convention-auditor (which applies judgment on top of this output).
  Pure Python, no model in the loop: same input always gives the same findings.
allowed-tools:
  - Bash
---

# doc-convention-linter

The **mechanical half** of a project's documentation audit. It reports only what a
script can decide with certainty, leaving every judgment call to the
`doc-convention-auditor` agent that consumes its output.

## What it checks

| Check | Severity | Scope |
|---|---|---|
| `broken_link` — relative link target does not exist on disk | error | whole corpus |
| `filename_not_kebab` — docs/ file is not kebab-case `.md` | error | docs/ roots |
| `h1_missing` — no `# H1` as the first content line | error | docs/ roots |
| `not_indexed` — docs/ file not linked from its `INDEX.md` | warn | per docs/ root |
| `orphaned` — docs/ file with no inbound link anywhere | warn | docs/ roots |
| `summary_missing` — no one-paragraph summary after the H1 | warn | docs/ roots |
| `was_phrasing` — "formerly / migrated from / superseded / …" | advisory | whole corpus |

It deliberately does **not** judge: surface-fit (right content in the right
surface), CLAUDE.md⇄MEMORY graduation, cross-ref *quality*, or whether a flagged
`was_phrasing` is a legitimate "use X, not Y" exception. Those need a model — they
belong to the `doc-convention-auditor`.

## How to run

From the **project root** (the umbrella root in a multi-repo project, else the repo root):

```bash
# Human-readable report (grouped by severity), exit 1 if any error:
python .claude/skills/doc-convention-linter/lint.py

# Structured findings for an agent to ingest:
python .claude/skills/doc-convention-linter/lint.py --json

# Scope the REPORT to an area — a directory or a single file (repo-relative).
# The whole corpus is still analysed for context; only findings are narrowed.
python .claude/skills/doc-convention-linter/lint.py docs libraries/<your-library>
python .claude/skills/doc-convention-linter/lint.py docs/some-doc.md

# Also fail on warnings (for a stricter gate):
python .claude/skills/doc-convention-linter/lint.py --strict
```

## Reading the output

- **`error`** — a hard, machine-certain breach. Exit code is non-zero if any exist.
  Note: a `broken_link` into an ignored/external path (a virtualenv, `node_modules`,
  a private or not-yet-cloned sub-repo) is *really* unresolved on disk, but may be an
  expected environmental absence rather than a doc bug — that distinction is the
  agent's call, not the linter's.
- **`warn`** — a convention gap worth fixing; does not fail the default run.
- **`advisory`** — a phrase to eyeball; almost always needs human/agent judgment.

`--json` emits `{ "findings": [...], "summary": {...} }`; each finding carries
`check`, `severity`, `path`, `line`, `message`.

## Notes

- **Corpus.** Full convention checks apply to `docs/` roots (the top-level `docs/`
  and each library's self-documenting `docs/`). Loose surfaces (`README.md`,
  `CLAUDE.md`, `.claude/memory/`) get link + `was_phrasing` checks only — they are
  intentionally exempt from the kebab/H1/summary rules.
- **Pre-commit norm (advisory, not a gate).** Running this before committing
  doc changes is good hygiene, but a SKILL.md instruction cannot *enforce* it.
  Real enforcement is a git pre-commit hook or GitHub CI that calls `lint.py`
  directly — the same script, a different entry point.
- The check set is defined at the top of `lint.py` (corpus globs, exempt names,
  trigger phrases) — adjust there. Each check is a `Context -> list[Finding]`
  function in the `CHECKS` list; add or remove a check by editing that list.
- **Tests ship with the skill.** `python .claude/skills/doc-convention-linter/tests.py`
  runs the stdlib unit tests (every helper, every check, the scope filter, and an
  inject/restore round-trip). No dependencies — run it after any change to `lint.py`.
