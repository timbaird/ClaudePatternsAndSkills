---
name: doc-discipline-universal
description: Documentation/assertion + destructive-git discipline is universal → always-on in CLAUDE.md, not a paths-scoped rule. Path-rules are only for disciplines with a real "doesn't apply here" state.
metadata:
  type: project
---

Documentation & assertion discipline (don't assume, flag `[TBD]`, current-state-only) and
destructive-git safety are **universal** — they apply to *all* output (prose, code comments, memory,
chat), every session. So they live **always-on in `CLAUDE.md`** (the always-loaded top one in an
umbrella project), not in a `paths:`-scoped rule, and are not duplicated into sub-repo `CLAUDE.md`
files. `project-discovery` stamps them; CPAS's own `CLAUDE.md` carries them too (dogfood).

**Why:** a `paths: **/*.md` rule both *over-fires* (any markdown edit) and *under-fires* (misses
fabrication in code/chat); and `.md` is too pervasive (memory + CLAUDE.md + docs) to be a useful
filter. The `paths:` mechanism earns its keep only when there's genuinely work where the rule should
*not* apply.

**How to apply:** keep universal discipline in `CLAUDE.md`; reserve the path-scoped `rules/` collection
for disciplines with a real "off" state — code discipline qualifies (irrelevant when writing prose), so
`coding-principles` is a rule. See [[vendoring-model]].
