# Library-inclusion bar — what earns a place in CPAS

A skill / hook / asset is centralised into this library **only when it has genuine cross-project
reuse** — a real second consumer, or clearly general utility. A skill that is technically generic but
has **one real consumer** stays in that project until a second genuinely needs it (it's cheap to
extract later — an hour for a ~60-line skill).

**Why:** speculative centralisation turns the library into a junk drawer and exports coupling; the
vendoring model already tolerates a little drift, so premature extraction buys nothing. (Same spirit as
the `no speculative flexibility` coding principle.)

**Applied (2026-07):** imported the image/music/video generation engines + `draw-diagram`,
`review-slides`, `map-process`, `thumbnail`, `make-short`, `make-pins`, `schedule-social` (+ its 3 `ghl-*`
hooks and the `ghl-social-integration` doc) — each with a genuine general use. **Left in kdp-factory:**
`split-narration` (generic one-take audio splitter, but KDP's read-aloud books are its only consumer)
and the Tier-3 shortlist (the `activity-*` puzzle generators, `build-ebook`, `story-video`,
`validate-instrument-reproduction`). Revisit when a second consumer appears (e.g. `activity-*` →
an `activity-book-generators` skill-pack).

See [[vendoring-model]] and [[skills-parameterised-not-forked]].
