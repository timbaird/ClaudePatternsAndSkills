# output-styles — reusable output styles

Drop-in **output styles** (markdown + YAML frontmatter: `name`, `description`, and optional
`keep-coding-instructions`) that get vendored into a repo's `.claude/output-styles/`. An output style
changes **how Claude writes back to you** across a whole session — tone, length, structure — without
touching what it does. Unlike a skill (loads on demand) or a rule (auto-fires by glob), an output
style is **selected** and stays active until you switch it with `/output-style`.

> **Activation.** Copying the file into `.claude/output-styles/` only makes a style *available*. To
> make it the **active** style, set `"outputStyle": "<name>"` in the repo's `.claude/settings.json`, or
> switch at runtime with `/output-style`. The [baseline-includes](../_patterns/_sub_patterns/baseline-includes/baseline-includes.md)
> sub-pattern vendors **ELI5** and sets it active in every new project.

## Catalogue

| Output style | Origin | Summary |
|---|---|---|
| [ELI5](ELI5.md) | Internal | "Explain like I'm 5" — replies in **ASD-STE100 Simplified Technical English** (approved plain words, active voice, one idea per sentence). Short sentences, small words, big words explained on the spot. Reports only what's necessary (what you did, did it work, what next); decisions capped at 2 options with a recommendation. Keeps paths/commands exact. Sets `keep-coding-instructions: true`, so coding behaviour is preserved. **Internally created.** |

## Deploying an output style

1. Copy the style's `.md` into `<repo>/.claude/output-styles/`.
2. *(Optional)* Make it the session default: add `"outputStyle": "<name>"` to
   `<repo>/.claude/settings.json` (merge in — don't overwrite the memory hook or `permissions`), or
   just switch to it at runtime with `/output-style`.

*(Catalogue reflects each style's frontmatter — `name`, `description`.)*
