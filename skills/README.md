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
| [bro](bro/) | 1.0.0 | Re-explain the **previous assistant message** in much plainer language — for when a reply came out too dense/jargon-heavy/formal. Triggered by `/bro`; re-expresses (never re-answers), keeps every fact verbatim, matches the original's language. **Internally created.** Pure instruction, no dependencies. |
| [doc-convention-linter](doc-convention-linter/) | 1.0.0 | Deterministic linter for a project's documentation corpus — broken relative links, docs missing from their `INDEX`, orphaned/non-kebab/missing-H1/missing-summary docs, and "document what WAS" trigger phrases. Pairs with the `doc-convention-auditor` agent. **Internally created.** `python3`, stdlib only. |
| [library-standards-linter](library-standards-linter/) | 1.0.0 | Deterministic linter checking reusable libraries under `libraries/` against `library-standards.md` — required files, src layout, naming, `pyproject` fields, `__version__`, SPDX headers, required `docs/`, no per-repo conventions meta-doc/memory. **Python/Evennia instance** (edit constants for other stacks). Pairs with the `library-standards-auditor` agent. **Internally created.** `python3` (3.11+). |
| [humaniser](humaniser/) | 2.8.0¹ | Remove the tells of AI-generated writing (inflated significance, em-dash overuse, rule-of-three, AI vocabulary, filler, etc.) while preserving meaning and voice. **Externally created** (adapted from Siqi Chen's MIT `humanizer`), centralised here, vendored verbatim. |
| [inspect-file-size](inspect-file-size/) | 1.0.0 | Report any file's (Office/`.pptx`/`.docx`/`.xlsx` or zip) size and exactly what's bloating it, and gate over a guideline — before committing to git. General-purpose. `python3`. |
| [skill-creator](skill-creator/) | 1.0.0¹ | Create, edit, improve, and benchmark skills — the meta-skill for building the others. **Externally created** (Anthropic), centralised here; lightly trimmed of non-applicable environment guidance (see its README). |
| [skill-scout](skill-scout/) | 1.0.0¹ | Search existing local/marketplace/GitHub/web skill sources (and vet them) *before* building a new skill — pairs with `skill-creator`. **Externally created** (ECC, MIT), vendored verbatim. |
| [search-first](search-first/) | 1.0.0¹ | Research-before-coding: search repo + npm/PyPI + MCP + GitHub for existing solutions, score them (maintenance/license/deps), and decide adopt/extend/build. The coding-side cousin of `skill-scout`. **Externally created** (ECC, MIT), vendored verbatim. |
| [upscale-image](upscale-image/) | 1.0.0 | Deterministic Pillow image upscaler to an exact print-resolution size (Lanczos + cover-fit centre-crop + DPI stamp). **Dependency-carrying** — needs Pillow, so it's the canonical example of the [skill-dependencies convention](../docs/skill-dependencies.md) (per-skill gitignored `.venv/`). Internally created (KDP-factory), generalised + centralised here. |
| [image-gen](image-gen/) | 1.0.0 | Deterministic, **model-agnostic** image-generation engine — a no-LLM wrapper over an OpenRouter image model (`chat/completions`, image output). Resolved prompt + reference image(s) + model slug → candidate images for human curation. Base unit the use-case image skills compose on. **Internally created** (factory engine). `python3`, stdlib only. |
| [music-gen](music-gen/) | 1.0.0 | Deterministic, **model-agnostic** music-generation engine — a no-LLM wrapper over an OpenRouter audio model (`chat/completions` with streamed audio output; SSE base64 assembly). Resolved prompt + model slug → candidate songs for human curation. Base unit the use-case music skills compose on. **Internally created** (factory engine, from yt-music-factory). `python3`, stdlib only. |
| [video-gen](video-gen/) | 1.0.0 | Deterministic, **model-agnostic** video-generation engine — a no-LLM wrapper over OpenRouter's async video API (`POST /api/v1/videos` → poll → download). Resolved prompt (+ optional start/end frame) + model slug → MP4 clip(s); includes the seamless-loop trick (same image as first + last frame). **Internally created** (factory engine, from yt-music-factory). `python3`, stdlib only. |
| [draw-diagram](draw-diagram/) | 1.0.0 | Author an editable **draw.io `.drawio`** technical diagram from a node/edge spec, then render it to **PNG with Pillow** (no draw.io app, deterministic). One spec expresses a network/cloud-architecture diagram, a flowchart, or a simple ERD; honours fixed ports + waypoints so hand-edits re-render true. **Dependency-carrying** (Pillow → per-skill gitignored `.venv/`). **Internally created** (from diploma-cloud-cyber). `python3` + Pillow. |
| [review-slides](review-slides/) | 1.0.0 | Render a slide deck (`.pptx`/`.pdf`) to one PNG per slide (LibreOffice → PyMuPDF) so the model can **look at every slide** and catch placeholder boxes, overflow/clipping, image↔text overlap, broken layouts, garbled AI images. Deterministic render; the review is model judgement. **Dependency-carrying** (PyMuPDF `.venv/`) + **LibreOffice** system app. **Internally created** (from diploma-cloud-cyber). `python3` + PyMuPDF. |
| [map-process](map-process/) | 1.0.0 | Turn a factory's **step→gate run-sheet** into a **Mermaid process map** + a structured audit model — cross-checks every named validator/agent/engine against what exists, colours gates by build status, flags named-but-missing validators + stale doc markers. The factory-methodology tool (any factory's run-sheet). **Internally created** (from diploma-cloud-cyber). `python3`, stdlib only. |
| [thumbnail](thumbnail/) | 1.0.0 | Deterministic **YouTube-thumbnail compositor** (Pillow) — hero/scene + title → 1280×720 JPEG in two layouts: **band** (translucent bottom band + auto-fit/auto-contrast title + optional wordmark + crop `--variants`) or **caption** (shadowed title/subtitle + optional scrim). Brand is data (colours/font/wordmark = params); `--font` optional. **Dependency-carrying** (Pillow `.venv/`). **Internally created** (consolidates KDP `thumbnail` + music `make-thumbnail`). `python3` + Pillow. |
| [make-short](make-short/) | 1.0.0 | Deterministic **9:16 vertical short** (1080×1920) from a 16:9 loop/clip + one audio track + a text hook — YouTube Shorts / Reels / TikTok. Blurred-fill reframe + top hook + optional CTA/handle + looped visual + one faded track snippet. Brand is data (colour/font/CTA/handle = params). **Dependency-carrying** — Pillow + **ffmpeg** (PATH, bundled `imageio-ffmpeg` fallback). **Internally created** (from yt-music-factory). `python3`. |
| [make-pins](make-pins/) | 1.0.0 | Deterministic **2:3 (1000×1500) Pinterest pin** from a scene still + a headline — blurred-fill layout (scene centre band + blurred top/bottom holding a headline + optional CTA/handle). Link set at post time, not baked in. Brand is data (colour/font/CTA/handle = params). **Dependency-carrying** (Pillow `.venv/`). **Internally created** (from yt-music-factory). `python3` + Pillow. |
| [schedule-social](schedule-social/) | 1.0.0 | Deterministic engine to schedule **one social post** via **GHL Social Planner** (YouTube/TikTok/Pinterest/Instagram/Facebook). Config-driven allowlist with a built-in **composite-key guard** (`platform + native_id` — can't post channel A's content to channel B); per-platform payload builders (the captured GHL field map). **Dependency-carrying** (`requests` + `PyYAML`). Pairs with the three `ghl-*` [hooks](../hooks/) + [integration doc](../docs/ghl-social-integration.md). **Internally created** (from yt-music-factory). `python3`. |

¹ Externally-created skill — the version tracks *which upstream we vendored*, not our own iteration (for `skill-creator` the field was internally added; for `humaniser` it's upstream's own version). See each skill's README.

## Deploying a skill

Copy the skill's folder into `<project>/.claude/skills/`. Each is self-contained — its engine (if
it has one) lives inside its own folder, so there is no shared dependency to bring along. A skill that
needs a **third-party package** (e.g. `upscale-image` → Pillow) follows the
[skill-dependencies convention](../docs/skill-dependencies.md): set up its per-skill `.venv/` on install
and wire the `ensure-python.mjs` preflight (see [skill-vendoring](../_patterns/_sub_patterns/skill-vendoring/skill-vendoring.md)).

*(Index reflects each skill's `SKILL.md` frontmatter — `name`, `description`, `version`.)*
