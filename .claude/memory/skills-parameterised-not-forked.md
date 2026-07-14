# Consolidate variants into one parameterised skill (brand/config is data)

When two projects grow their own copy of the same skill and it drifts, **consolidate into ONE
parameterised skill** rather than keeping per-project / per-platform forks. Brand, style, and config
live in **parameters (data)** — never hardcoded — so the skill holds no project identity.

**Do NOT split by "platform" when the real variation is template + geometry.** The two thumbnail
variants were both YouTube 1280×720 — the difference was the title *template*, so they became one
`thumbnail` skill with `--layout band|caption`, not `make_youtube_thumbnail` / `make_pinterest_thumbnail`.
Distinct output artefacts / geometries can still be their own focused skills (`thumbnail` 16:9,
`make-pins` 2:3, `make-short` 9:16) — the axis is *artefact*, not *platform branch in one god-skill*.

This extends the generation engines' "model is a `--model` parameter" philosophy to the brand
dimension. Corollary observed on intake: several skills shipped a hardcoded macOS font path and a
brand colour — genericise those to an optional `--font` (Pillow built-in fallback) + a colour param.

See [[library-inclusion-bar]].
