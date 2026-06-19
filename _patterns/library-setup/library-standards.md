<!-- TEMPLATE — stack-agnostic library standards. Vendored by the library-setup pattern into a
     project's `docs/library-standards.md`, then **adapted**: fill the `<PLACEHOLDERS>`, resolve the
     "choose per project" points to your stack, and delete guidance that doesn't apply. For a worked,
     filled-in instance see `library-standards.evennia-example.md` beside this template (a Python/Evennia
     project). Keep this file in the project's `docs/` so the library-standards-auditor can read it. -->

# Library Standards

Conventions for the reusable libraries developed under `libraries/` (or wherever this project keeps
them). Every library in that folder follows these standards, so a session creating a new one produces a
result structurally consistent with its siblings. This is a **project-level standard held at the top
level** — libraries *follow* it; they do not carry or reference a copy of it. Where a convention has a
deeper authoritative source, this file points there rather than duplicating (e.g.
[doco-structure.md](doco-structure.md) for the documentation surfaces).

The libraries folder may also contain **auxiliary repos directly required for library development** —
test-content and fixture repos. These standards apply only to the libraries themselves; auxiliary repos
are not bound by them.

## When this applies

These standards apply to libraries developed in `libraries/<library-name>/`. Characterise them for this
project — these are **choices to make once and state here**:

- **Stability posture** — `<internal-first` (refactor freely, no semver promises) **or** `published`
  (external consumers, semver applies)>`. State which, because it changes how aggressively APIs may move.
- **Flavour / ecosystem** — `<the framework or ecosystem these libraries extend, if any (e.g. a specific
  web/game/CLI framework), or "framework-agnostic">`.
- **License** — `<the project's chosen license; see Licensing below>`.

If a future library has materially different framing, some standards may relax. State the deliberate
divergence in that library's `CLAUDE.md`.

## Naming

- **Repo / distribution name**: hyphenated, lowercase, descriptive (`<my-thing>`).
- **Import / module name**: the language's identifier form of the same name (`<my_thing>` where the
  language disallows hyphens; otherwise the same). Keep repo name and import name mechanically derivable
  from each other.
- **Repo location**: `libraries/<library-name>/`. Each library is its own git repo with its own remote.

## Source layout

Use a **clear, conventional layout for the language** that separates published package code from test
infrastructure and examples. Prefer the layout that forces an *installed* import during development (so
packaging bugs surface early). Document the chosen layout as an ASCII tree:

```
<library-name>/
├── <build/manifest file>        # single source of build + dependency truth
├── README.md
├── CLAUDE.md
├── LICENSE
├── .gitignore
├── docs/                        # content wiki — how the library works (see doco-structure.md)
├── <package source dir>/        # the importable package/module
├── <test infrastructure dir>/   # standalone test setup + runner
└── examples/                    # runnable demos for integration testing (optional)
```

## Build & dependency declaration

- **One canonical manifest** for build + dependencies (`<the language's standard: e.g. pyproject.toml /
  package.json / Cargo.toml / go.mod>`). No competing/legacy declarations.
- **Runtime dependencies** declared in the manifest's runtime section only; **dev-only tools** in a
  separate dev/optional group.
- **Declared license must match the LICENSE file.**
- **Pin a minimum language/runtime version** and justify raising it per library.

## Licensing

- **One license for all libraries in this folder** — `<chosen license>`. The full text lives in a
  `LICENSE` file at each repo root.
- **Source files carry an SPDX header** on the first line: `<# SPDX-License-Identifier: <LICENSE-ID>>`
  (use the comment syntax of the language).

## Test framework

Pick **one** test framework and a **standalone runner** that needs no external host application:

- A repo-root entry point that bootstraps the environment and runs the suite (`<e.g. runtests.py /
  npm test / cargo test>`).
- Minimal standalone configuration checked into the test-infrastructure dir.
- Tests live where the language's convention expects them; keep them discoverable by the runner.

## Development environment

Each library is developed against a **dedicated, isolated environment** (`<venv / node_modules /
toolchain sandbox>`) so library development is independent of any consumer's environment. The isolated
environment directory is gitignored. Document the from-clone setup:

```bash
cd libraries/<library-name>
<create isolated env>
<install the library in editable/dev mode>
<run the tests>
```

### `examples/` — runnable demos for integration testing (optional)

Where unit tests cover logic in isolation, `examples/` holds **runnable demos** that exercise the
library end-to-end against the real framework/runtime. One subdirectory per demo; each serves the
library, not a real consumer (no project-specific concepts — just enough to exercise the surface).

## Documentation surfaces

A library's documentation follows the project's four-surface model — see
[doco-structure.md](doco-structure.md) — and carries only the **reduced set** appropriate to a
stand-alone-reusable sub-repo:

- **`README.md`** — humans landing on the repo (and standalone consumers).
- **`CLAUDE.md`** — repo-specific agent context.
- **`docs/`** — the content wiki: how the library works (`INDEX.md` + kebab-case topic files).

A library does **not** carry the project's documentation conventions (no per-repo conventions meta-doc)
and has **no memory surface of its own** — those are project-level concerns held once, at the top level.
The library follows the project conventions; it does not restate them. Full rationale: the
"stand-alone-reusable sub-repos may self-document" exception in [doco-structure.md](doco-structure.md).

## CLAUDE.md structure

Standard sections, in order:

1. **What this project is** — one paragraph + tagline.
2. **Project status** — link to `docs/progress.md`; don't duplicate status content here (it ages badly).
3. **Where to read first** — numbered reading order.
4. **Load-bearing architectural principles** — numbered; constraints every implementation decision must respect.
5. **Out of scope** — concrete rulings *or* "decided as questions arise" depending on project maturity.
6. **Working conventions** — editing design docs, license, SPDX headers.
7. **Documentation discipline (load-bearing)** — only-what-was-discussed, flag-open-questions, smaller-is-better.
8. **Repository layout** — current ASCII tree.
9. **Tools and environment** — language/runtime version, runtime deps, test framework.

**Two principles every library's section 4 should include** (the load-bearing reusability guardrails):

- *The library does not own consumer/application concepts.* (Keep domain concepts in the consumer.)
- *No project-specific assumptions.* (Nothing specific to the originating project leaks into the library.)

Other principles are library-specific.

## docs/ structure

Required:

- **`INDEX.md`** — lists every design document with a one-line description, organised by category.
- **`progress.md`** — reverse-chronological milestone log with links to evidence.
- **`archive/`** — historical context, preserved per the "don't delete; supersede" rule.

New design documents follow the project's `docs/` conventions — see [doco-structure.md](doco-structure.md):
kebab-case filename; first line an `# H1 Title` matching the filename; a one-paragraph summary as the
second block; index every document in `INDEX.md` (an un-indexed document is invisible).

## Documentation discipline

Follows the project's working-discipline rules (the top-level `CLAUDE.md` and
[doco-structure.md](doco-structure.md)); each library's `CLAUDE.md` carries a discipline section
reflecting them.

## Bootstrap checklist

When creating a new library in this folder:

- [ ] Create the git repo and clone to `libraries/<library-name>/`.
- [ ] Add `LICENSE` (the project's chosen license).
- [ ] Add `.gitignore` for the language/toolchain.
- [ ] Adapt `CLAUDE.md` from a sibling library; rewrite project-specific sections, keep the standard shape.
- [ ] Create `docs/INDEX.md` and `docs/progress.md` with current state.
- [ ] Write `README.md` answering: what is it, status, is it for me, install, learn more.
- [ ] Populate the build manifest using the standard shape.
- [ ] Set the package version in the conventional place (`<e.g. __version__, package.json "version">`).
- [ ] Adapt the test runner + standalone test config from a sibling.
- [ ] Add one smoke test that proves install + runner work end-to-end.
- [ ] Create the dedicated isolated environment; install the library in dev mode.
- [ ] Verify dev-install and the test runner both succeed.
- [ ] Initial commit.

## Living examples

When in doubt about a convention not covered here, look at how an existing library does it. List the
project's reference libraries here:

- **`<reference-library-a>`** — `<what it's a good reference for>`.
- **`<reference-library-b>`** — `<what it's a good reference for>`.
