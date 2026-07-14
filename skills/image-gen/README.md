# image-gen

Deterministic, **model-agnostic** image-generation engine — a no-LLM wrapper over an OpenRouter image
model. Give it a resolved prompt, reference image(s), and a model; it saves candidate images for human
curation. The base unit that use-case image skills (subject reference, scene, cover, page art, …)
compose on top of: it performs no prompt composition and holds no domain knowledge.

**Internally created** (factory engine). `python3`, stdlib only. Sibling of `music-gen` and
`video-gen`; same conventions (`--model` required, `.env` key loading, `RESULT` line, shipped offline
tests).

- `generate.py` — the engine (CLI + pure, testable functions).
- `tests.py` — stdlib unit tests, offline, no API cost: `python tests.py`.
- `SKILL.md` — parameters and the layering it fits into.
