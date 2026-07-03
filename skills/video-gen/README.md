# video-gen

Deterministic, **model-agnostic** video-generation engine — a no-LLM wrapper over OpenRouter's
async video API (`POST /api/v1/videos` → poll → download). Give it a resolved prompt (+ optional
start/end frame) and a model slug; it submits the job, waits, and saves the MP4. Includes the
seamless-loop trick (same image as first + last frame). The base unit the use-case video skills
compose on.

**Internally created** (factory engine). `python3`, stdlib only. Sibling of `image-gen` and
`music-gen`; same conventions (`--model` required, `.env` key loading, `RESULT` line, shipped
offline tests).

See [SKILL.md](SKILL.md) for usage. Run `python tests.py` for the offline unit tests.
