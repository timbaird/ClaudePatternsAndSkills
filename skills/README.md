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
| [inspect-file-size](inspect-file-size/) | 1.0.0 | Report any file's (Office/`.pptx`/`.docx`/`.xlsx` or zip) size and exactly what's bloating it, and gate over a guideline — before committing to git. General-purpose. `python3`. |
| [skill-creator](skill-creator/) | 1.0.0¹ | Create, edit, improve, and benchmark skills — the meta-skill for building the others. **Externally created** (Anthropic), centralised here; lightly trimmed of non-applicable environment guidance (see its README). |

¹ Externally-created skill — the version is an *internal tracking* field (records when we re-vendor an upstream update), not our own iteration. See [skill-creator/README.md](skill-creator/README.md).

## Deploying a skill

Copy the skill's folder into `<project>/.claude/skills/`. Each is self-contained — its engine (if
it has one) lives inside its own folder, so there is no shared dependency to bring along.

*(Index reflects each skill's `SKILL.md` frontmatter — `name`, `description`, `version`.)*
