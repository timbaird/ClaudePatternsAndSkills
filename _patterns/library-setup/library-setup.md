# The Library-Setup Pattern — Setup Specification

Stand up a **new reusable library** inside a project's `libraries/` folder, structurally consistent with
its siblings, following the project's **library standards**. This is a **top-level pattern**: you invoke
it deliberately when you decide to create a library — it is **not** part of a project's initial scaffold
(the [single-repo](../single-repo/single-repo-setup.md) / [umbrella-repo](../umbrella-repo/umbrella-repo-setup.md)
patterns set up the project; this adds a library to it later).

> Placeholders: `<PROJECT>` = the project root (the umbrella root in a multi-repo project; the repo root
> in a single-repo one). `<LIBRARY>` = the new library's name (hyphenated). Commands are shown in
> `git` / shell form.

---

## 1. When to use this

Use library-setup when you're creating a **standalone-reusable library** — code that could reasonably be
used outside this project — that will live in `<PROJECT>/libraries/<LIBRARY>/` as its own git repo.
Because such a library is a stand-alone-reusable sub-repo, it **self-documents** (carries its own reduced
doc set) — see the exception in [doco-structure.md](../_sub_patterns/doco-setup/doco-structure.md).

If the code only makes sense *within* this project, it's not a library — keep it in the relevant repo and
document it at the top-level docs surface instead.

## 2. The two assets this pattern provides

| Asset | Role | Destination |
|---|---|---|
| [`library-standards.md`](library-standards.md) | the **stack-agnostic standards template** — the authority a new library is built against | vendored (once per project) → `<PROJECT>/docs/library-standards.md`, then adapted |
| [`library-standards.evennia-example.md`](library-standards.evennia-example.md) | a **worked example** (Python/Evennia) of the filled-in template | reference only — not vendored |

> **Why the standard lives in `<PROJECT>/docs/`, not just here.** The `library-standards-auditor` agent
> (and the `library-standards-linter` skill) read the standard **from the project's `docs/`** to check a
> library against it. So the adapted standard must be a real doc in the project — vendor it there once,
> and every library in the project is held to the same, locally-authoritative standard.

## 3. Setup playbook

### Step 1 — Ensure the project standard exists (once per project)
If `<PROJECT>/docs/library-standards.md` doesn't exist yet, **vendor the template**:
copy [`library-standards.md`](library-standards.md) → `<PROJECT>/docs/library-standards.md`, then
**adapt it** — fill the `<PLACEHOLDERS>`, resolve the "choose per project" points to your stack
(language, layout, license, test framework, isolated-env tool), and delete guidance that doesn't apply.
Use [`library-standards.evennia-example.md`](library-standards.evennia-example.md) as a worked reference.
**Index it** in `<PROJECT>/docs/INDEX.md`. (Subsequent libraries reuse this same standard — don't
re-vendor.)

### Step 2 — Create the library repo
Create the git repo with its own remote and clone it to `<PROJECT>/libraries/<LIBRARY>/`. In an umbrella
project, add it to the umbrella `.gitignore` (nested-repo entry) like any other sub-repo, and re-run the
[cascade sub-pattern](../_sub_patterns/umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md) so
it gains an up-pointer and is listed in the umbrella `CLAUDE.md`.

### Step 3 — Scaffold to the standard
Follow the **Bootstrap checklist** in `<PROJECT>/docs/library-standards.md`: the source layout, build
manifest, license + SPDX headers, standalone test runner + smoke test, isolated dev environment, and the
**reduced documentation set** (`README.md`, `CLAUDE.md`, `docs/` with `INDEX.md` + `progress.md` +
`archive/`). The library follows the project conventions; it does **not** restate them and has **no
memory surface of its own**.

### Step 4 — Verify against the standard
Run the **[`library-standards-linter`](../../skills/library-standards-linter/)** skill (the mechanical
checks: required files, layout, manifest fields, version, SPDX headers, required `docs/` files, absence of
a per-repo conventions meta-doc or memory surface), then optionally the
**[`library-standards-auditor`](../../agents/library-standards-auditor.md)** agent for the
judgment-level review. Fix findings before the initial commit.

### Step 5 — Commit
Make the library's **initial commit** once the linter is clean. In an umbrella project, also commit the
umbrella's `.gitignore` + cascade changes (separately — they're independent repos).

## 4. Relation to the other patterns

- **Composes with** the project's existing setup — it assumes [single-repo](../single-repo/single-repo-setup.md)
  or [umbrella-repo](../umbrella-repo/umbrella-repo-setup.md) already ran. It reuses the
  [doco-setup](../_sub_patterns/doco-setup/doco-setup.md) conventions (the library's `docs/` follows
  `doco-structure.md`) and, in an umbrella, the
  [cascade](../_sub_patterns/umbrella-claude-md-cascade/umbrella-claude-md-cascade-setup.md).
- **The standard is project-local.** `library-standards.md` is vendored into the project once and is the
  authority; this pattern is how a new library is created against it.

## 5. Gotchas checklist

- [ ] `library-standards.md` is **vendored into `<PROJECT>/docs/`** (so the linter/auditor can read it) —
      not left only in CPAS.
- [ ] **Adapt** the template to your stack — it ships stack-agnostic with placeholders; an un-adapted copy
      is not a usable standard.
- [ ] The library carries the **reduced doc set** — no conventions meta-doc, **no memory surface**.
- [ ] In an umbrella: add the new repo to `.gitignore` and re-run the cascade.
- [ ] Run the **library-standards-linter** before the initial commit.
