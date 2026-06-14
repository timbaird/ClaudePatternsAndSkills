# Sub-pattern — Documentation setup

A reusable recipe that establishes the standard **four-surface documentation structure** in a repo
(`README.md`, `CLAUDE.md`, `MEMORY`, `docs/`) and drops the structure-explainer into `docs/` so the
repo carries its own map.

> **Sub-pattern** = a composable building block referenced by full patterns, not used alone.
> Referenced by: [umbrella-repo](../../umbrella-repo/umbrella-pattern.md), single-repo, etc.
> Sibling of [memory-setup](../memory-setup/memory-setup.md) — together they stand up a repo's
> Claude + docs infrastructure. Placeholder: `<REPO>` = the target repo's root.

## What it sets up (the four surfaces)

Full definitions + the `CLAUDE.md` ⇄ `MEMORY` split live in the **`doco-structure.md`** explainer
(which this recipe copies into the repo). In brief:

| Surface | Role | Provisioned by |
|---|---|---|
| `README.md` | human landing page | **this sub-pattern** (authored) |
| `CLAUDE.md` | always-loaded agent operating rules (small, universal, imperative) | **this sub-pattern** (authored) |
| `MEMORY.md` + `.claude/memory/` | agent's accumulated durable knowledge (situational, declarative) | the **memory-setup** sub-pattern |
| `docs/` (+ `INDEX.md`, `doco-structure.md`) | technical / knowledge wiki | **this sub-pattern** |

## Required assets — provisioning manifest

| Asset | Type | Source | Destination |
|---|---|---|---|
| `doco-structure.md` | doc template (vendored **verbatim**) | [`doco-structure.md`](doco-structure.md) (beside this recipe) | `<REPO>/docs/doco-structure.md` |
| `docs/INDEX.md` | authored | — | `<REPO>/docs/INDEX.md` |
| `README.md` | authored per the README surface | — (repo-specific) | `<REPO>/README.md` |
| `CLAUDE.md` | authored per the CLAUDE.md surface | — (repo-specific) | `<REPO>/CLAUDE.md` |

> Only `doco-structure.md` is copied verbatim — it's the generic explainer. `README.md` and
> `CLAUDE.md` are **authored fresh per repo** (they're repo-specific); use the surface definitions in
> `doco-structure.md` as the spec. `MEMORY` is **not** set up here — that's the memory-setup sibling.

## Provisioning steps (ordered)

1. **Create `docs/`** and copy **`doco-structure.md`** (verbatim, from beside this recipe) to
   `<REPO>/docs/doco-structure.md` — the in-repo explainer of the four surfaces.
2. **Create `docs/INDEX.md`** — the entry point listing every `docs/` document with a one-line
   description. Seed it with the `doco-structure.md` entry.
3. **Author `<REPO>/README.md`** to the README surface (what / why / status / how-to-try) — kept
   skim-friendly and repo-specific.
4. **Author `<REPO>/CLAUDE.md`** to the CLAUDE.md surface — *small*: one-paragraph what, where-to-read,
   load-bearing principles, out-of-scope list, broad conventions, and **pointers** to `docs/` and
   `MEMORY` (don't duplicate their content). Keep it lean; it's loaded every session.
5. **`MEMORY`** — provisioned by the **memory-setup** sub-pattern. If composing both (the usual case),
   run that too; this recipe just leaves `CLAUDE.md` pointing at `MEMORY`.

> **Don't commit here.** This is a *sub-pattern* — one component of a larger setup. The calling
> pattern commits **once, after the full setup is complete**; committing a half-finished setup
> mid-process is the wrong granularity.

## Notes

- **`docs/` is the same role for non-software repos** — the project's substantive knowledge base, not
  necessarily code architecture. (The name `docs/` is deliberately neutral for that reason.)
- Keep `CLAUDE.md` small and `README.md` skim-friendly; let **`docs/`** absorb length and **`MEMORY`**
  absorb accumulating decisions. That division is the whole point of the structure.

## Why a vendored explainer + authored surfaces

`doco-structure.md` is generic, so it's **vendored verbatim** — every repo carries the same map, and
improving the master re-propagates by re-copying. `README` / `CLAUDE.md` are inherently repo-specific,
so they're **authored** against that map rather than templated.
