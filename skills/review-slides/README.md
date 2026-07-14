# review-slides

Render a `.pptx` (or `.pdf`) slide deck to one PNG per slide (LibreOffice → PyMuPDF) and visually review
it — placeholder boxes, overflow/clipping, image/text overlap, broken layouts, garbled gen images,
off-brand slides. Deterministic + re-runnable. See [SKILL.md](SKILL.md) for the workflow and dependencies
(LibreOffice is a system app; PyMuPDF lives in a gitignored per-skill `.venv/`).

**Internally created.** **Dependency-carrying** — PyMuPDF (per-skill gitignored `.venv/`,
[skill-dependencies convention](../../docs/skill-dependencies.md)) + **LibreOffice** as a system app.
`tests.py` covers the `soffice` resolver + a real PDF→PNG rasterise round-trip (no LibreOffice needed for
the test, since a `.pdf` input skips it).
