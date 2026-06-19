# skills — standalone reusable skills

General-purpose skills, each **self-contained and independently deployable**. Copy any single
skill's folder into a project's `.claude/skills/` and it brings everything it needs (including its
own script, if any).

> For skills that must be deployed *together* as a group with shared dependencies, see
> [`../skill-packs/`](../skill-packs/). For reusable **hook scripts** (e.g. the memory-setup
> preflight), see [`../hooks/`](../hooks/) — those are wired into `settings.json`, not invoked as skills.

## Catalogue

| Skill | Version | Summary |
|---|---|---|
| [doc-convention-linter](doc-convention-linter/) | 1.0.0 | Deterministic linter for a project's documentation corpus — broken relative links, docs missing from their `INDEX`, orphaned/non-kebab/missing-H1/missing-summary docs, and "document what WAS" trigger phrases. Pairs with the `doc-convention-auditor` agent. **Internally created.** `python3`, stdlib only. |
| [library-standards-linter](library-standards-linter/) | 1.0.0 | Deterministic linter checking reusable libraries under `libraries/` against `library-standards.md` — required files, src layout, naming, `pyproject` fields, `__version__`, SPDX headers, required `docs/`, no per-repo conventions meta-doc/memory. **Python/Evennia instance** (edit constants for other stacks). Pairs with the `library-standards-auditor` agent. **Internally created.** `python3` (3.11+). |
| [humaniser](humaniser/) | 2.8.0¹ | Remove the tells of AI-generated writing (inflated significance, em-dash overuse, rule-of-three, AI vocabulary, filler, etc.) while preserving meaning and voice. **Externally created** (adapted from Siqi Chen's MIT `humanizer`), centralised here, vendored verbatim. |
| [inspect-file-size](inspect-file-size/) | 1.0.0 | Report any file's (Office/`.pptx`/`.docx`/`.xlsx` or zip) size and exactly what's bloating it, and gate over a guideline — before committing to git. General-purpose. `python3`. |
| [skill-creator](skill-creator/) | 1.0.0¹ | Create, edit, improve, and benchmark skills — the meta-skill for building the others. **Externally created** (Anthropic), centralised here; lightly trimmed of non-applicable environment guidance (see its README). |
| [skill-scout](skill-scout/) | 1.0.0¹ | Search existing local/marketplace/GitHub/web skill sources (and vet them) *before* building a new skill — pairs with `skill-creator`. **Externally created** (ECC, MIT), vendored verbatim. |
| [search-first](search-first/) | 1.0.0¹ | Research-before-coding: search repo + npm/PyPI + MCP + GitHub for existing solutions, score them (maintenance/license/deps), and decide adopt/extend/build. The coding-side cousin of `skill-scout`. **Externally created** (ECC, MIT), vendored verbatim. |

¹ Externally-created skill — the version tracks *which upstream we vendored*, not our own iteration (for `skill-creator` the field was internally added; for `humaniser` it's upstream's own version). See each skill's README.

## Deploying a skill

Copy the skill's folder into `<project>/.claude/skills/`. Each is self-contained — its engine (if
it has one) lives inside its own folder, so there is no shared dependency to bring along.

*(Index reflects each skill's `SKILL.md` frontmatter — `name`, `description`, `version`.)*
