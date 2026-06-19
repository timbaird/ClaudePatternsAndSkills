# doc-convention-linter · v1.0.0 (created 2026-06-19)

## Purpose
**The mechanical half of a project's documentation audit.** A deterministic linter that surfaces the
*machine-decidable* documentation problems — broken relative links, docs missing from their `INDEX`,
orphaned docs, non-kebab-case filenames, missing H1 / summary blocks, and "document what WAS" trigger
phrases. No model in the loop: same input always gives the same findings. It deliberately stops where
judgment begins (surface-fit, graduation, cross-ref *quality*, legitimate "use X not Y" exceptions) —
that half belongs to the `doc-convention-auditor` agent, which consumes this linter's `--json` output.

## Provenance — internally created
Internally created (originated in the FCM project; generalized for reuse) — not vendored from a third
party. The version tracks *our* iteration. Pure Python standard library — no third-party dependencies, so
it runs anywhere Python 3 does and ships complete with its own tests.

## What's in the folder
- `SKILL.md` — the model/user-facing contract: what it checks, how to run it, how to read the output.
- `lint.py` — the linter. The corpus globs, exempt filenames, and trigger phrases are constants at the
  top; each check is a `Context -> list[Finding]` function in the `CHECKS` list.
- `tests.py` — stdlib `unittest`: every helper, every check, the scope filter, and an inject/restore
  round-trip. Zero dependencies.

## How it works
`lint.py` discovers the whole doc corpus, reads it once into a shared `Context`, then runs each check.
Findings carry `check`, `severity` (`error` / `warn` / `advisory`), `path`, `line`, `message`.
Scoping (a directory or a single file) narrows the *report* while analysis stays global, so corpus-wide
checks (orphaned, not-indexed, inbound links) remain correct. Exit code is non-zero when any `error`
exists (or any `warn` under `--strict`), so it doubles as a git pre-commit / CI gate over the same script.

## Running the tests
```bash
python .claude/skills/doc-convention-linter/tests.py
```
Run it after any change to `lint.py`. The check set is data (`CHECKS`), so adding a check means adding a
function and a test.

## Deploying
Copy the `doc-convention-linter/` folder into a project's `.claude/skills/`. Adjust the corpus globs at
the top of `lint.py` to match that project's doc layout. No dependencies beyond Python 3.
