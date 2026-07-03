---
name: music-gen
version: 1.0.0
description: |
  Deterministic music-generation engine. A no-LLM mechanical wrapper that calls an
  OpenRouter audio model with a fully-resolved prompt (+ optional reference image(s))
  and a model name, and saves candidate songs to a review folder for human curation.
  The model is a parameter (model-agnostic — swap models with a flag, not a code
  edit; the recommended default lives in the project docs). This is a BASE UNIT the
  use-case music skills compose on top of — it does NO prompt composition and holds
  NO channel/IP knowledge. Use it directly when you already have a resolved prompt +
  a model and just need songs.
allowed-tools:
  - Bash
---

# music-gen

The **deterministic engine** at the bottom of the music pipeline. Give it a finished prompt, a
model, and an output folder; it returns saved candidate songs. Everything *above* it — composing
the prompt from the channel's genre/mood spec, picking the model — belongs to the use-case skills
that call this one.

> **"No LLM in the loop"** describes the *orchestration*: the same arguments build the same API
> request, with no model deciding anything. The music *output* is of course non-deterministic —
> that is the audio model, not this script.

## How to run

From the **repo root**:

```bash
python .claude/skills/music-gen/generate.py \
  --model google/lyria-3-pro-preview \
  --prompt "tropical chill-out, warm Rhodes, soft percussion, gentle waves, 90 BPM, instrumental" \
  --format mp3 \
  --n 2 \
  --out channels/tropical-chill/videos/v001/_candidates
```

`--ref` is optional and repeatable (reference image(s) some models accept for conditioning).

## Parameters

| Flag | Required | Meaning |
|---|---|---|
| `--model` | yes | OpenRouter audio model slug (e.g. `google/lyria-3-pro-preview`). **Always explicit** — the engine hardcodes no model. |
| `--prompt` | yes | the fully-resolved music prompt (style, mood, tempo, instrumental/lyrics); this engine does not compose it |
| `--format` | no (`mp3`) | output audio format: `mp3` or `wav` |
| `--n` | no (1) | number of candidate songs to generate (one API call each) |
| `--out` | yes | folder to save into; created if absent |
| `--ref` | no, repeatable | reference image path passed as `refs[]` (for models that accept image conditioning) |
| `--name` | no | output filename stem (`track` → `track.mp3`; extras → `track_2.mp3`); omit to name by the model slug |

## Output

- Saves `<name>.<format>` (extra songs → `<name>_2.<format>`…) when `--name` is given; otherwise
  `<model-slug>.<format>`. Into `--out`.
- Prints a final machine-readable line for callers to parse:
  `RESULT {"model": ..., "count": N, "saved": [paths], "ok": true|false}`.
- Exit code `0` if any song was saved, else non-zero.

## How it talks to OpenRouter

Audio output on OpenRouter is delivered via `POST /api/v1/chat/completions` with
`modalities: ["text","audio"]`, `audio: {"format": …}`, and **`stream: true` (required for audio)**.
The response is Server-Sent Events; each chunk carries a base64 slice at
`choices[0].delta.audio.data`. This engine concatenates the slices and decodes once to the file.

## Notes

- **Model-agnostic by design.** The factory commits to no single music model; `--model` is always
  passed. OpenRouter currently exposes few audio models, but that will change — swap by flag, and
  keep the chosen default in the project docs, not in this code.
- **Key.** Reads `OPENROUTER_API_KEY` from the environment or the repo-root `.env`. Tolerates the
  legacy `OPEN_ROUTER_API_KEY` name with a nudge to rename. The key is never printed.
- **Costs credit.** Successful generations spend OpenRouter credit; failed calls (auth / bad model
  / bad request) generally do not.
- **Tests ship with the skill.** `python .claude/skills/music-gen/tests.py` runs the stdlib unit
  tests offline (no network, no API cost) — every pure helper (incl. SSE parsing + base64
  assembly) plus an injected-caller run of `generate()`. Run it after any change to `generate.py`.
