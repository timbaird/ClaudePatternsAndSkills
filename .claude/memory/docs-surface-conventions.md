---
name: docs-surface-conventions
description: docs/ is a single top-level surface (umbrella-only in a multi-repo project); docs/INDEX.md is required-reading surfaced by a CLAUDE.md pointer because, unlike MEMORY.md, it isn't auto-loaded.
metadata:
  type: project
---

Two conventions govern the four-surface `docs/` (the **both-audience** knowledge surface — humans *and*
agents), enforced by [doco-setup](../../_patterns/_sub_patterns/doco-setup/doco-setup.md) and stamped
into `CLAUDE.md`:

1. **One `docs/`, at the top level only.** In a multi-repo (umbrella) project, `docs/` lives **only at
   the umbrella** — a single shared docs surface for the umbrella *and* every sub-repo; **sub-repos hold
   no `docs/`** (you always launch from the umbrella, so one surface serves all). Single-repo → `docs/`
   at the repo root. Run `doco-setup` once, at the top.
2. **`docs/INDEX.md` is required reading via a `CLAUDE.md` pointer.** Unlike `MEMORY.md` (whose index is
   auto-injected every session), `docs/INDEX.md` is **not** auto-loaded — so the always-loaded
   `CLAUDE.md` must carry a line telling the agent to read it each session and load the relevant doc on
   demand. Same index-then-load-on-demand pattern as MEMORY; the pointer is the enforcement.

**Why:** the four-surface model puts both-audience knowledge in `docs/` (not the LLM-only `MEMORY`), but
`docs/` isn't auto-loaded, so without the `CLAUDE.md` pointer the agent silently misses it. And in a
multi-repo project, scattering `docs/` into each sub-repo fragments the surface and breaks the
launch-from-the-umbrella model — one top-level surface keeps it coherent.

**How to apply:** `doco-setup` scaffolds `docs/` + `docs/INDEX.md` once at the top and adds the
`docs/INDEX.md` required-reading line to the `CLAUDE.md` shape; `project-discovery` augments around that
line, never dropping it; sub-repo `CLAUDE.md` files need no separate pointer (the umbrella `CLAUDE.md`
is always loaded first). See [[doc-discipline-universal]] (the LLM-only-vs-both-audience split) and
[[vendoring-model]].
