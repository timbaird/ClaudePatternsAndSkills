# Sub-pattern — Project discovery (draft the project's `CLAUDE.md` content)

A reusable recipe that **elicits a project's defining knowledge through a structured interview and
drafts it into the project's `CLAUDE.md` + `README.md`** — the *content* step that fills the
documentation *structure* laid down by [doco-setup](../doco-setup/doco-setup.md). It also stamps the
project's **universal, always-on discipline rules** into the top-level `CLAUDE.md`.

> **Sub-pattern** = a composable building block referenced by full patterns, not used alone.
> Referenced by: [umbrella-repo](../../umbrella-repo/umbrella-repo-setup.md),
> [single-repo](../../single-repo/single-repo-setup.md). Sibling of
> [dot-claude-setup](../dot-claude-setup/dot-claude-setup.md),
> [memory-setup](../memory-setup/memory-setup.md), [doco-setup](../doco-setup/doco-setup.md),
> [umbrella-claude-md-cascade](../umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md),
> [skill-vendoring](../skill-vendoring/skill-vendoring.md), and
> [settings-setup](../settings-setup/settings-setup.md). Placeholders: `<REPO>` = target repo;
> `<TOP>` = the **always-loaded** `CLAUDE.md` (the umbrella root in a multi-repo project; the single
> repo's `CLAUDE.md` otherwise).

## Why

`doco-setup` builds the four documentation surfaces but leaves their *content* as "go author it" —
which silently assumes the agent already knows the project. This sub-pattern **is** that authoring
step, done as a disciplined interview so the summary is accurate, durable, and **confirmed by the
human** — not guessed.

## When it runs

**After the structure exists** — `dot-claude-setup` (placeholder) → `doco-setup` (surfaces) →
`umbrella-claude-md-cascade` (wiring). It fills content into files that already exist; it does not
create the surfaces.

## Two ways in: interview, or analyse-then-interview

- **Greenfield / new project** → interview from scratch (the discovery protocol below).
- **Existing / unfamiliar codebase** → run **codebase-onboarding** first to *analyse* the repo (stack,
  entry points, conventions), then use this interview to **confirm and fill the gaps** rather than
  starting blank. Analysis seeds the draft; the interview validates it. (These are the two ways to
  populate `CLAUDE.md` — analysis vs interview — and they compose.)

## The discovery protocol (the project summary)

**Claude-led discovery, not a questionnaire.** The user may not volunteer enough on their own — open
broad, listen for what's missing, drill on thin answers, and keep going until every dimension has a
substantive answer.

**Seven dimensions** to probe until answered:
1. **Capability** — what it does, in one or two plain sentences (enduring purpose, not progress).
2. **Mechanism** — how it works at a high level; the central abstraction (intent, not current impl).
3. **Audience** — who it's for (end users, developers, a specific team, a consumer project).
4. **Problem** — what gap it fills; why it needs to exist.
5. **Scope boundary** — what it is deliberately *not*. (Often the most clarifying — if the user
   struggles, ask: "what would you refuse to add to this, even if asked?")
6. **Relationships / positioning** — does it depend on, sit alongside, or replace existing systems?
   Sibling projects, upstream frameworks, downstream consumers worth naming.
7. **Tagline** — a short memorable phrase for the top of `README.md` (derived last, not asked first).

**Load-bearing constraints:**
- **~200–300 words / 3–5 short paragraphs.** Past ~300 it's documentation, not a summary — push the
  overflow into `docs/`.
- **No state-based content — the summary must not be able to go stale.** No progress/milestones, no
  "currently…", no dated facts, no status words ("MVP", "in development") in prose, no changing
  feature lists. (This *is* the library's "principles, not state" ethos.) Status lives **separately** —
  a one-line "Project status" pointer to `docs/` or `MEMORY`, never inline.
- **Mandatory repeat-back before writing.** Draft the "What this project is" section back to the user,
  structured as it will appear, and ask: "Does this capture it accurately — what's missing, wrong, or
  overstated?" Iterate to confirmation *first*, then write. (This is over and above the always-on
  think-before-acting rule — the summary is foundational; every future session depends on it.)

## What gets written, and where (four-surface aware)

| Output | Goes to | Notes |
|---|---|---|
| "What this project is" summary | `<TOP>/CLAUDE.md` **and** `README.md` | same content, framed per surface |
| Tagline | top of `README.md` | |
| "Project status" pointer | `<TOP>/CLAUDE.md` | one line → `docs/`/`MEMORY`, never inline status |
| Universal discipline rules | `<TOP>/CLAUDE.md` (always-on) | the verbatim blocks below |
| Operational config (git autonomy, permissions) | **not here** | that's [settings-setup](../settings-setup/) |

## Universal discipline — stamp into the top `CLAUDE.md`

These apply to **all output, every session** (not just markdown, not just one file type), so they are
**always-on** and belong in the always-loaded `<TOP>/CLAUDE.md` — **not** a `paths:`-scoped rule, and
**not** duplicated into sub-repo `CLAUDE.md` files (those stay lean; they inherit these because you
always launch from `<TOP>`). Write them in verbatim:

```markdown
## Working discipline — assumptions & documentation

Never record anything as *decided / agreed / canonical* unless it was actively discussed **and**
explicitly approved. Flag anything not yet agreed with `[TBD — needs discussion: <what is open>]`
rather than writing it as settled.

- Capture only what was discussed and agreed; don't extrapolate a principle into unraised specifics.
- Flag open questions explicitly with `[TBD — …]` so a later session picks them up deliberately.
- Distinguish archived/historical material from in-conversation decisions.
- Smaller is better — three faithfully-captured points beat ten padded ones.
- Self-correct — if you catch yourself writing beyond what was discussed, remove it or mark it `[TBD]`.
- Docs describe the **current state only**; what-was lives in git history, not in prose.

## Git safety — destructive operations require explicit approval

Never run a destructive git operation without explicit, in-conversation approval for that specific
action — regardless of any settings allowlist or prior approval. Destructive includes: force push,
hard reset, discarding uncommitted changes, `git clean -f`, force-deleting branches, history rewrites
(`rebase`, `amend` on pushed commits, `filter-branch`/`filter-repo`), dropping stashes, deleting tags,
and any `--no-verify` / `--no-gpg-sign` bypass. Force-pushing a protected branch (`main`/`master`/
`release/*`) must be refused outright. When unsure whether something can lose work or rewrite history,
treat it as destructive and ask.
```

> **Code discipline** (think-before-coding, simplicity, surgical changes, goal-driven) is the
> *path-scoped* counterpart — it has a real "doesn't apply here" state (prose), so it lives as the
> [`coding-principles`](../../../rules/coding-principles.md) rule, vendored via
> [skill-vendoring](../skill-vendoring/skill-vendoring.md)/the rules collection, **not** stamped here.

## Idempotent / re-runnable (human-in-the-loop)

Re-running means **refine**, not silent regenerate:
- If `<TOP>/CLAUDE.md` still holds the bare `dot-claude-setup` placeholder → draft fresh.
- If it already holds a confirmed summary → offer **refine-existing**, and never overwrite a confirmed
  summary without the user's say-so.

> **Don't commit here.** This is a *sub-pattern* — the calling pattern commits once, after the full
> setup is complete.

## Composition

- **[doco-setup](../doco-setup/doco-setup.md)** builds the *structure*; this fills the *content*.
  (doco-setup's "author the `CLAUDE.md` body" step delegates here.) doco-setup's `CLAUDE.md` **shape**
  includes the **required-reading pointer to `docs/INDEX.md`** — augment around it, don't drop it.
- **[settings-setup](../settings-setup/)** owns *operational config* (git autonomy, the permission
  allowlist → `settings.json`) — kept separate from project knowledge.
- **codebase-onboarding** (analysis) optionally seeds this interview for an existing repo.
- Placement is **`<TOP>` only** — the umbrella root in a multi-repo project, the single `CLAUDE.md`
  otherwise. Universal discipline and the summary go there once; sub-repos stay lean.
