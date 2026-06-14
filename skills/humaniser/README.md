# humaniser · v2.8.0 (vendored 2026-06-14)

## Purpose
Remove the tells of AI-generated writing so text reads as natural and human-written. Detects and
rewrites ~33 patterns — inflated significance, promotional language, superficial `-ing` analyses,
vague attributions, em-dash overuse, rule-of-three, AI-vocabulary words, copula avoidance, negative
parallelisms, filler/hedging, emoji/boldface/curly-quote noise, and more — while preserving meaning,
coverage, and the author's voice. Based on Wikipedia's "Signs of AI writing" guide.

## Provenance — externally created
This skill is **externally created** — adapted from Siqi Chen's MIT-licensed
[`humanizer`](https://github.com/blader/humanizer), itself built on Wikipedia's *Signs of AI writing*.
It is **centralised here for management**, not authored or maintained internally, and is **vendored
verbatim** — the skill body is upstream's, unedited.

## Versioning note (external skill)
The `version: 2.8.0` in `SKILL.md` is **upstream's own version**, not internal iteration. Unlike
internally-created skills (versioned because *we* change them), this one is tracked by upstream's
version so we know which upstream we vendored — bump it only when re-vendoring a newer upstream.

## What's in the folder
- `SKILL.md` — the full skill (pattern catalogue + draft → audit → final process + worked example).
- `LICENSE.txt` — upstream MIT licence.

## Deploying
Copy the `humaniser/` folder into a project's `.claude/skills/`. No scripts or external dependencies —
it's pure instructions, so it works as a drop-in anywhere Claude Code runs.
