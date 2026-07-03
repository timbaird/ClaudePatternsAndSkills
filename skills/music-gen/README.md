# music-gen

Deterministic, **model-agnostic** music-generation engine — a no-LLM wrapper over an OpenRouter
audio model (`chat/completions`, streamed audio output). Give it a resolved prompt + a model slug;
it saves candidate songs for human curation. The base unit the use-case music skills compose on.

**Internally created** (factory engine). `python3`, stdlib only. Sibling of `image-gen` and
`video-gen`; same conventions (`--model` required, `.env` key loading, `RESULT` line, shipped
offline tests).

See [SKILL.md](SKILL.md) for usage. Run `python tests.py` for the offline unit tests.
