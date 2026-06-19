#!/usr/bin/env python3
"""doc-convention-linter — deterministic checks on a project's documentation corpus.

No model is in the loop: same input -> same output. This is the mechanical half of
the documentation audit. It is meant to be composed into agentic workflows (the
doc-convention-auditor ingests `--json` and applies judgment on top), called
directly from a Claude session, or wired into a git pre-commit / GitHub CI check.

It reports only what is *decidable by a machine*:
  - filename / H1 / summary-block conventions  (docs/ roots only)
  - INDEX completeness                          (per docs/ root)
  - broken relative links                       (corpus-wide)
  - orphaned docs (no inbound link)             (docs/ roots only)
  - "document what IS, not WAS" trigger phrases (corpus-wide, advisory)

Judgment calls — surface-fit, graduation/demotion, cross-ref *quality*, whether a
flagged "WAS" phrase is a legitimate "use X not Y" exception — are deliberately
left to the doc-convention-auditor agent that consumes this output.

Run from the project root:  python .claude/skills/doc-convention-linter/lint.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- corpus definition (globs relative to repo root) -------------------------
# Directories whose .md files get the FULL convention checks. doco-structure.md
# scopes the kebab/H1/summary/INDEX rules to "docs/ documents", so only these.
DOC_ROOT_GLOBS = ["docs", "libraries/*/docs"]

# Loose doc surfaces: link + WAS checks only (NOT held to kebab/H1/summary —
# memory files carry frontmatter and no H1; CLAUDE.md/README are free-form).
LOOSE_GLOBS = [
    "README.md", "CLAUDE.md", ".claude/README.md", ".claude/memory/*.md",
    "libraries/README.md", "libraries/*/README.md", "libraries/*/CLAUDE.md",
    "src/game/CLAUDE.md", "ops/CLAUDE.md", "ops/*/CLAUDE.md",
]

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
# Names allowed to break kebab-case inside a docs/ root.
EXEMPT_NAMES = {"INDEX.md", "README.md", "CLAUDE.md", "MEMORY.md"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")  # links inside `inline code` are examples, not refs
# Trigger phrases for the "document what IS, not WAS" rule (CLAUDE.md). Advisory:
# some are legitimate ("use X, not Y") — the agent adjudicates, the linter flags.
WAS_PATTERNS = [
    "used to be", "migrated from", "formerly", "renamed from",
    "superseded", "previously", "what was",
]
WAS_RE = re.compile(r"\b(?:" + "|".join(re.escape(p) for p in WAS_PATTERNS) + r")\b", re.I)


# --- finding model -----------------------------------------------------------
class Finding:
    __slots__ = ("check", "severity", "path", "line", "message")

    def __init__(self, check, severity, path, line, message):
        self.check = check
        self.severity = severity      # "error" | "warn" | "advisory"
        self.path = path              # repo-relative str
        self.line = line              # int | None
        self.message = message

    def as_dict(self):
        return {
            "check": self.check, "severity": self.severity,
            "path": self.path, "line": self.line, "message": self.message,
        }


# --- helpers -----------------------------------------------------------------
def read_lines(path: Path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def fenced_line_indices(lines):
    """Indices of lines inside (or marking) ``` fenced code blocks — skipped by
    link and WAS checks so example snippets don't produce false positives."""
    inside, fence = set(), False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            inside.add(i)
            fence = not fence
        elif fence:
            inside.add(i)
    return inside


def body_after_frontmatter(lines):
    """Return the index where content begins, skipping a leading --- YAML block."""
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i < len(lines) and lines[i].strip() == "---":
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "---":
                return j + 1
    return 0


def find_h1(lines, start):
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if s == "":
            continue
        if s.startswith("# "):
            return i, s[2:].strip()
        return None  # first content line is not an H1
    return None


def resolve_link(src: Path, target: str, root: Path):
    """Resolve a markdown link target to a local Path, or None if external/anchor."""
    t = target.strip()
    if not t or t.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return None
    t = t.split()[0]                 # drop optional ("title")
    t = t.split("#", 1)[0]           # drop #anchor
    if not t:
        return None
    if t.startswith("/"):
        return (root / t.lstrip("/")).resolve()
    return (src.parent / t).resolve()


def links_in(lines, fenced):
    out = []
    for i, ln in enumerate(lines):
        if i in fenced:
            continue
        for m in LINK_RE.finditer(INLINE_CODE_RE.sub("", ln)):
            out.append((i + 1, m.group(1)))
    return out


def rel(path: Path, root: Path):
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# --- corpus discovery --------------------------------------------------------
def discover(root: Path):
    """Return (doc_roots, loose_files) for the whole doc corpus.

    doc_roots: {Path: [md files]} per docs/ root (full convention checks).
    loose_files: list of Path (link + WAS checks only).

    The full corpus is ALWAYS discovered. Scoping is applied to *findings*, not to
    discovery, so corpus-wide checks (orphaned, not_indexed, inbound links) keep the
    global context they need even when the report is narrowed to a few files.
    """
    doc_roots = {}
    for g in DOC_ROOT_GLOBS:
        for d in sorted(root.glob(g)):
            if d.is_dir() and (d / "INDEX.md").exists():
                doc_roots[d] = sorted(d.glob("*.md"))

    loose, seen = [], set()
    for g in LOOSE_GLOBS:
        for p in sorted(root.glob(g)):
            if p.is_file() and p not in seen:
                loose.append(p)
                seen.add(p)
    return doc_roots, loose


def path_in_scope(rp, scopes):
    """A repo-relative file path is in scope if it equals, or sits under, any
    scope prefix. `scopes` is a list of rstrip('/')-normalised prefixes."""
    return any(rp == s or rp.startswith(s + "/") for s in scopes)


# --- analysis context -------------------------------------------------------
class Context:
    """The corpus read once and pre-computed, shared by every check. Built over
    the WHOLE corpus so corpus-wide checks have global context even when the
    final report is scoped to a few files."""

    def __init__(self, root: Path, doc_roots, loose):
        self.root = root
        self.doc_roots = doc_roots
        self.loose = loose
        self.structured = [p for files in doc_roots.values() for p in files]
        self.corpus = self.structured + loose
        self.cache = {p: read_lines(p) for p in self.corpus}
        self.fences = {p: fenced_line_indices(self.cache[p]) for p in self.corpus}
        # inbound link count per structured doc (for orphan detection)
        self.inbound = {p.resolve(): 0 for p in self.structured}
        for src in self.corpus:
            for _, target in links_in(self.cache[src], self.fences[src]):
                dest = resolve_link(src, target, root)
                if dest is not None and dest in self.inbound:
                    self.inbound[dest] += 1

    def rel(self, p: Path):
        return rel(p, self.root)


def build_context(root: Path):
    return Context(root, *discover(root))


# --- checks (each: Context -> list[Finding], independently unit-testable) ----
def check_filename_kebab(ctx):
    return [Finding("filename_not_kebab", "error", ctx.rel(p), None,
                    f"filename '{p.name}' is not kebab-case .md")
            for p in ctx.structured
            if p.name not in EXEMPT_NAMES and not KEBAB_RE.match(p.name)]


def check_h1(ctx):
    out = []
    for p in ctx.structured:
        if p.name == "INDEX.md":
            continue  # INDEX has its own shape; skip H1/summary
        lines = ctx.cache[p]
        if find_h1(lines, body_after_frontmatter(lines)) is None:
            out.append(Finding("h1_missing", "error", ctx.rel(p), None,
                               "no H1 title as the first content line"))
    return out


def check_summary(ctx):
    out = []
    for p in ctx.structured:
        if p.name == "INDEX.md":
            continue
        lines = ctx.cache[p]
        h1 = find_h1(lines, body_after_frontmatter(lines))
        if h1 is None:
            continue  # absence reported by check_h1
        h1_line, _ = h1
        nxt = next((j for j in range(h1_line + 1, len(lines))
                    if lines[j].strip() != ""), None)
        if nxt is None or lines[nxt].lstrip().startswith("#"):
            out.append(Finding("summary_missing", "warn", ctx.rel(p), h1_line + 1,
                               "no one-paragraph summary block after the H1"))
    return out


def check_broken_links(ctx):
    out = []
    for src in ctx.corpus:
        for lineno, target in links_in(ctx.cache[src], ctx.fences[src]):
            dest = resolve_link(src, target, ctx.root)
            if dest is not None and not dest.exists():
                out.append(Finding("broken_link", "error", ctx.rel(src), lineno,
                                   f"link target does not exist: {target}"))
    return out


def check_not_indexed(ctx):
    out = []
    for d, files in ctx.doc_roots.items():
        index = d / "INDEX.md"
        indexed = {dest for _, t in links_in(ctx.cache[index], ctx.fences[index])
                   if (dest := resolve_link(index, t, ctx.root)) is not None}
        for p in files:
            if p.name != "INDEX.md" and p.resolve() not in indexed:
                out.append(Finding("not_indexed", "warn", ctx.rel(p), None,
                                   f"not linked from {ctx.rel(index)}"))
    return out


def check_orphaned(ctx):
    return [Finding("orphaned", "warn", ctx.rel(p), None,
                    "no inbound links from any doc in the corpus")
            for p in ctx.structured
            if p.name != "INDEX.md" and ctx.inbound.get(p.resolve(), 0) == 0]


def check_was_phrasing(ctx):
    out = []
    for p in ctx.corpus:
        for i, ln in enumerate(ctx.cache[p]):
            if i in ctx.fences[p]:
                continue
            m = WAS_RE.search(ln)
            if m:
                out.append(Finding("was_phrasing", "advisory", ctx.rel(p), i + 1,
                                   f'"{m.group(0)}" — verify it states current '
                                   "state, not history (agent adjudicates)"))
    return out


CHECKS = [
    check_filename_kebab, check_h1, check_summary, check_broken_links,
    check_not_indexed, check_orphaned, check_was_phrasing,
]


def lint(root: Path, scope=None):
    """Run every check over the full corpus, then narrow the *report* to `scope`
    (a list of repo-relative path prefixes). Analysis stays global so corpus-wide
    checks remain correct; only the emitted findings are filtered."""
    ctx = build_context(root)
    findings = [f for check in CHECKS for f in check(ctx)]

    if scope:
        scopes = [s.rstrip("/") for s in scope]
        findings = [f for f in findings if path_in_scope(f.path, scopes)]
        in_files = [p for p in ctx.corpus if path_in_scope(ctx.rel(p), scopes)]
        n_files = len(in_files)
        n_roots = len({d for d, fs in ctx.doc_roots.items()
                       for p in fs if path_in_scope(ctx.rel(p), scopes)})
    else:
        n_files = len(ctx.corpus)
        n_roots = len(ctx.doc_roots)

    return findings, n_files, n_roots


# --- output ------------------------------------------------------------------
SEV_ORDER = {"error": 0, "warn": 1, "advisory": 2}


def render_human(findings, n_files, n_roots):
    out = []
    by_sev = {"error": [], "warn": [], "advisory": []}
    for f in findings:
        by_sev[f.severity].append(f)
    label = {"error": "ERRORS", "warn": "WARNINGS", "advisory": "ADVISORY"}
    for sev in ("error", "warn", "advisory"):
        group = sorted(by_sev[sev], key=lambda f: (f.path, f.line or 0))
        if not group:
            continue
        out.append(f"\n{label[sev]} ({len(group)})")
        out.append("-" * len(label[sev]))
        for f in group:
            loc = f"{f.path}:{f.line}" if f.line else f.path
            out.append(f"  [{f.check}] {loc}\n      {f.message}")
    out.append(
        f"\nScanned {n_files} files across {n_roots} docs/ root(s): "
        f"{len(by_sev['error'])} error, {len(by_sev['warn'])} warn, "
        f"{len(by_sev['advisory'])} advisory."
    )
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic doc-convention linter.")
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("scope", nargs="*",
                    help="optional repo-relative path prefixes to restrict the scan")
    ap.add_argument("--json", action="store_true", help="emit JSON findings")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero on warnings too (default: errors only)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    findings, n_files, n_roots = lint(root, args.scope)

    if args.json:
        print(json.dumps({
            "findings": [f.as_dict() for f in
                         sorted(findings, key=lambda f: (SEV_ORDER[f.severity],
                                                         f.path, f.line or 0))],
            "summary": {
                "files_scanned": n_files, "docs_roots": n_roots,
                "errors": sum(f.severity == "error" for f in findings),
                "warnings": sum(f.severity == "warn" for f in findings),
                "advisory": sum(f.severity == "advisory" for f in findings),
            },
        }, indent=2))
    else:
        print(render_human(findings, n_files, n_roots))

    fail = any(f.severity == "error" for f in findings)
    if args.strict:
        fail = fail or any(f.severity == "warn" for f in findings)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
