# draw-diagram

Author an editable **draw.io (`.drawio`)** technical diagram from a simple node/edge spec, then render
it to **PNG with Pillow** — no draw.io app, no system binary, same input → same pixels. The `.drawio`
is the single source of truth (anyone can open + edit it free); the PNG is rendered from it for dropping
into a document or slide. Expresses a network / cloud-architecture diagram, a flowchart, or a simple ERD.

**Internally created.** **Dependency-carrying** — needs Pillow, so it follows the
[skill-dependencies convention](../../docs/skill-dependencies.md): a per-skill gitignored `.venv/` +
committed `requirements.txt` + an import guard. Set up the venv on install (see [SKILL.md](SKILL.md)).

- `draw_diagram.py` — the engine (build `.drawio` from spec; render to PNG).
- `tests.py` — build/parse/geometry helpers + a real Pillow render round-trip. Run with the venv python.
- `requirements.txt` — Pillow.

See [SKILL.md](SKILL.md) for the spec format, shapes, and the render/fallback flow.
