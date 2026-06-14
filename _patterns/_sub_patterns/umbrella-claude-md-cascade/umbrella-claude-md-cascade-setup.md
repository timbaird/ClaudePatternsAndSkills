# Sub-pattern — Umbrella ⇄ sub-repo `CLAUDE.md` cascade

A reusable recipe that wires the **two-way `CLAUDE.md` cascade** of an umbrella-repo project: the
umbrella `CLAUDE.md` points **down** to every nested sub-repo's `CLAUDE.md`, and each sub-repo's
`CLAUDE.md` points **up** to the umbrella for project-wide rules. The result is that, launching from
the umbrella, project-wide context loads always and each sub-repo's context loads *lazily* when Claude
touches a file in it — with nothing duplicated.

> **Sub-pattern** = a composable building block referenced by full patterns, not used alone.
> Referenced by: [umbrella-repo](../../umbrella-repo/umbrella-pattern.md). Sibling of
> [memory-setup](../memory-setup/memory-setup.md) and [doco-setup](../doco-setup/doco-setup.md).
> Placeholders: `<UMBRELLA>` = the umbrella repo root; `<REPO>` / `<REPO_A>`, `<REPO_B>`, … = nested
> working repos.

## Order-independent and idempotent — by design

This recipe is safe to run **in any order** relative to the other sub-patterns, and safe to **re-run**
any number of times. It works by **detecting what's already there and only adding what's missing**:

- If a `CLAUDE.md` **doesn't exist**, it's created with the cascade block.
- If it **exists but lacks** the cascade block, the block is inserted at the most appropriate spot,
  leaving everything else untouched.
- If it **already has** the block, it's left as-is (the umbrella's down-list is reconciled so every
  current sub-repo has a link — see below).

Because sub-repos are **discovered dynamically** each run, the common "I added a new sub-repo to an
already-set-up umbrella" case is handled with no special mode: the new repo is found, gains an
up-pointer (and its file if absent), and its link is added to the umbrella's down-list — while every
already-correct file is left alone.

## The cascade in two halves

| Half | Lives in | Content |
|---|---|---|
| **Down-signpost** | `<UMBRELLA>/CLAUDE.md` | a "Sub-repo context" section linking to **each** sub-repo's `CLAUDE.md` |
| **Up-pointer** | each `<REPO>/CLAUDE.md` | a top-of-file note that project-wide rules + cross-repo context live in the umbrella |

**Load-bearing rule — plain links, never `@import`.** The down-signpost uses **plain markdown links**.
An `@import` would load every sub-repo's `CLAUDE.md` *eagerly* on every session; a plain link lets the
sub-repo file load **lazily**, only when Claude reads a file in that repo. This laziness is the whole
point of the cascade — never convert these links to `@imports`. (Why the *up*-pointer is needed at all:
of the umbrella's assets, only skills and `CLAUDE.md` cascade down into sub-repos; agents, settings,
rules, and memory load **only** from the launch dir. So each sub-repo points up to say "the rest lives
at the umbrella, launch from there." See the umbrella pattern's discovery-rules table.)

## Templates

### Umbrella down-signpost — a section in `<UMBRELLA>/CLAUDE.md`
```markdown
## Sub-repo context

Each nested repo has its own `CLAUDE.md`, **auto-loaded (lazily) when Claude reads a file in that
repo** — so repo-specific context arrives only when it's relevant:

- [<REPO_A>](<REPO_A>/CLAUDE.md)
- [<REPO_B>](<REPO_B>/CLAUDE.md)

> These are **plain markdown links, not `@imports`** — an `@import` would load every sub-repo's
> `CLAUDE.md` eagerly on every session; plain links keep them lazy.
```

### Sub-repo up-pointer — a blockquote at the top of `<REPO>/CLAUDE.md`
```markdown
> **Project-wide working rules and cross-repo context live in the umbrella repo's `CLAUDE.md`**
> (loaded automatically when you work from the umbrella root). This file holds only
> **<REPO>-specific** instructions.
```

### A sub-repo `CLAUDE.md` created from scratch
```markdown
# <REPO>

> **Project-wide working rules and cross-repo context live in the umbrella repo's `CLAUDE.md`**
> (loaded automatically when you work from the umbrella root). This file holds only
> **<REPO>-specific** instructions.

<!-- <REPO>-specific instructions go here. -->
```

### An umbrella `CLAUDE.md` created from scratch (minimal)
```markdown
# <UMBRELLA> — umbrella / coordination

> Parent (umbrella) repo holding cross-repo coordination context and Claude Code tooling. The actual
> deliverables live in nested repos this repo **gitignores**. Open Claude here, at the umbrella root,
> for work that spans repos.

## Sub-repo context

<!-- down-signpost block (above) — one link per discovered sub-repo -->
```

## Provisioning steps (order-independent, idempotent)

### 1. Identify the umbrella and discover its sub-repos
- The **umbrella** is the repo at the working root (`<UMBRELLA>`).
- **Sub-repos** are the immediate child directories that are their **own git repositories** (each
  contains a `.git` entry) — these are the repos the umbrella `.gitignore` excludes by name. Enumerate
  them fresh on every run; cross-check against the umbrella's `.gitignore` nested-repo entries.
- Record the discovered list. If **none** are present yet, do only the umbrella half (step 2) with an
  empty/placeholder section — later runs populate it as repos are added.

### 2. Umbrella `CLAUDE.md` — the down half
- **Missing file** → create it from the minimal umbrella template, with a "Sub-repo context" section
  listing **every** discovered sub-repo.
- **Existing file** → locate a section that links to the sub-repos (the down-signpost, by any heading):
  - **Absent** → insert the down-signpost section near the **top** — after any orientation/intro
    blockquote, *before* the standing-rules / detailed body.
  - **Present** → **reconcile the link list**: ensure each discovered sub-repo has exactly one plain
    link; add any that are missing; never duplicate; don't touch unrelated content. If any link is an
    `@import`, convert it back to a plain link.

### 3. Each sub-repo `CLAUDE.md` — the up half
For **every** discovered sub-repo:
- **Missing file** → create it from the from-scratch sub-repo template (H1 = repo name + up-pointer +
  placeholder).
- **Existing file** → check for an up-pointer to the umbrella's `CLAUDE.md` (a top note that
  project-wide rules live at the umbrella):
  - **Absent** → insert the up-pointer blockquote **directly under the H1**, before any repo-specific
    content.
  - **Present** → leave it as-is.

### 4. Verify
- Every discovered sub-repo appears **once** in the umbrella down-list, and every link resolves to an
  existing `<REPO>/CLAUDE.md`.
- Every sub-repo `CLAUDE.md` carries the up-pointer.
- **No `@imports`** anywhere in the cascade; no duplicated cascade blocks.

> **Don't commit here.** This is a *sub-pattern* — one component of a larger setup. Committing is
> **not** part of it: the calling pattern commits **once, after the full setup is complete**.

## Detection cues (so re-runs are reliable)
- **Down-signpost present** = the umbrella `CLAUDE.md` contains markdown links of the form
  `](<repo>/CLAUDE.md)` for one or more sub-repos (typically under a "Sub-repo context" heading).
- **Up-pointer present** = the sub-repo `CLAUDE.md` near the top references the umbrella's `CLAUDE.md`
  / "project-wide" rules living at the umbrella.
- Match these **semantically**, not by exact wording — an umbrella set up by hand (different headings,
  different phrasing) should be recognised as already-cascaded and left intact, not duplicated.

## Notes
- **Launch from the umbrella.** The cascade only delivers its benefit when Claude is launched with
  `<UMBRELLA>` as the workspace root; that's why each sub-repo points up. (The umbrella pattern's
  "golden rule".)
- **Keep `CLAUDE.md` files lean.** This sub-pattern only adds the *cascade wiring*. Project-wide rules
  belong in the umbrella body; repo-specific instructions in each sub-repo. Deeper explanation of *how*
  the cascade works (the discovery asymmetry) belongs in `docs/`, not repeated in every `CLAUDE.md` —
  compose with [doco-setup](../doco-setup/doco-setup.md) if you want that explainer in-repo.
- **Composes with siblings.** Run alongside [memory-setup](../memory-setup/memory-setup.md) and
  [doco-setup](../doco-setup/doco-setup.md) in any order; the umbrella pattern sequences and commits.
