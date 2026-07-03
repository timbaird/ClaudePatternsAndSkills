---
name: video-gen
version: 1.0.0
description: |
  Deterministic video-generation engine. A no-LLM mechanical wrapper that calls an
  OpenRouter video model (async submit -> poll -> download) with a fully-resolved
  prompt + an optional start/end frame image + a model name, and saves the finished
  MP4(s) to a review folder for human curation. The model is a parameter
  (model-agnostic — swap models with a flag, not a code edit; the recommended default
  lives in the project docs). This is a BASE UNIT the use-case video skills compose on
  top of — it does NO prompt composition and holds NO channel/IP knowledge. Includes
  the seamless-loop trick (same image as first + last frame). Use it directly when you
  already have a resolved prompt (+ frame) + a model and just need clips.
allowed-tools:
  - Bash
---

# video-gen

The **deterministic engine** at the bottom of the video pipeline. Give it a finished prompt, an
optional frame image, a model, and an output folder; it submits the async job, polls it to
completion, and downloads the MP4. Everything *above* it — composing the motion prompt, choosing
the start frame, picking the model — belongs to the use-case skills that call this one.

> **"No LLM in the loop"** describes the *orchestration*: the same arguments build the same API
> request, with no model deciding anything. The video *output* is of course non-deterministic —
> that is the video model, not this script.

## The async flow

Video generation on OpenRouter is asynchronous and takes 30 s – a few minutes:

1. `POST /api/v1/videos` → `{ id, polling_url, status: "pending" }`
2. `GET <polling_url>` every `--poll-interval` s until `status: "completed"` (terminal failures:
   `failed` / `cancelled` / `expired` → the `error` field is surfaced)
3. `GET unsigned_urls[0]` (with auth) → the MP4 bytes, saved to `--out`

## Seamless loops (the key trick)

Pass the **same image as both the first and last frame** so the clip ends exactly where it began
and repeats without a visible seam — ideal for a music-video background:

```bash
python .claude/skills/video-gen/generate.py \
  --model kwaivgi/kling-v3.0-std \
  --prompt "slow drift over a moonlit tropical beach, gentle waves, subtle parallax" \
  --frame scene.png --loop \
  --duration 5 --aspect-ratio 16:9 \
  --n 2 \
  --out channels/tropical-chill/videos/v001/_clips
```

`--loop` sets `frame_images` to `[first_frame=scene.png, last_frame=scene.png]`. For a non-looping
clip use `--frame` alone (start frame only) or `--frame` + `--last-frame` for a distinct end.

## Parameters

| Flag | Required | Meaning |
|---|---|---|
| `--model` | yes | OpenRouter video model slug (e.g. `kwaivgi/kling-v3.0-std`). **Always explicit** — no baked default. |
| `--prompt` | yes | the fully-resolved motion prompt; this engine does not compose it |
| `--frame` | no | start-frame image path (image-to-video) |
| `--loop` | no | use the start frame as BOTH first and last frame (seamless loop) |
| `--last-frame` | no | explicit end-frame image (instead of `--loop`) |
| `--duration` / `--resolution` / `--aspect-ratio` / `--size` | no | model-specific; must be values from the model's `supported_*` sets (an out-of-set value 400s upstream) |
| `--n` | no (1) | clips to generate (one job each) |
| `--out` | yes | folder to save into; created if absent |
| `--name` | no | output filename stem (`clip` → `clip.mp4`; extras → `clip_2.mp4`); omit to name by the model slug |
| `--poll-interval` | no (30) | seconds between status polls |
| `--max-wait` | no (600) | give up after this many seconds per clip |

## Pick per-model parameters — don't guess

`duration`, `resolution`, `aspect_ratio`, and which `frame_type`s are accepted are **per-model**.
Before using a new model, check its capabilities and only pass values from the returned sets:

```bash
curl -sS https://openrouter.ai/api/v1/videos/models | jq '.data[] | select(.id == "MODEL_ID")'
# fields: supported_resolutions, supported_aspect_ratios, supported_durations,
#         supported_frame_images, generate_audio, seed, ...
```

## Output

- Saves `<name>.mp4` (extra clips → `<name>_2.mp4`…) when `--name` is given; otherwise
  `<model-slug>.mp4`. Into `--out`.
- Prints `RESULT {"model": ..., "count": N, "saved": [paths], "ok": true|false}`.
- Exit code `0` if any clip was saved, else non-zero.

## Notes

- **Model-agnostic by design.** `--model` is always passed; any OpenRouter video model works. Keep
  the chosen default in the project docs, not in this code.
- **Key.** Reads `OPENROUTER_API_KEY` from the environment or the repo-root `.env`. Tolerates the
  legacy `OPEN_ROUTER_API_KEY` name. The key is never printed.
- **Costs credit.** Successful generations spend OpenRouter credit; failed submits generally don't.
  Video is the most expensive generator — prefer short clips (loop a 5 s clip rather than render
  minutes).
- **Tests ship with the skill.** `python .claude/skills/video-gen/tests.py` runs the stdlib unit
  tests offline (no network, no API cost) — every pure helper plus injected submit/poll/download
  runs of `generate()` (completion, terminal failure, timeout). Run it after any change.
