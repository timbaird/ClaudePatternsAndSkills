#!/usr/bin/env python3
"""library-standards-linter — deterministic checks against library-standards.md.

No model is in the loop: same input -> same output. This is the mechanical half of
the library-standards audit. It checks the *machine-decidable* subset of
`docs/library-standards.md` for each reusable library under `libraries/` and is
meant to be composed into agentic workflows (a future library-standards-auditor
ingests `--json` and adjudicates declared divergences), called directly from a
Claude session, or wired into CI.

Structure: each library is read once into a `LibContext`, then every check is a
single-purpose `LibContext -> list[Finding]` validator in the `CHECKS` list — each
independently unit-tested. Add or remove a check by editing that list.

Calibration: structural folders the standard expects (`tests/`, `docs/archive/`)
are checked at *folder-presence* level — a placeholder (`.gitkeep` or a short
README explaining why) satisfies them; the linter does not demand their internal
contents. `examples/` is optional. Whether a gap is a sanctioned divergence (e.g.
a pure-Python library with no Evennia test infra) is left to the judgment layer:
the linter surfaces the deviation; the accepted resolutions are "add the structure
(placeholder OK)" or "document the divergence in the library's CLAUDE.md".

Run from the project root:  python .claude/skills/library-standards-linter/lint_library.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

# A library under libraries/ is any directory carrying a pyproject.toml. This
# excludes auxiliary repos (test-content / fixture repos) which are not bound by
# the standards (per library-standards.md).
LIBRARIES_DIR = "libraries"

SPDX = "SPDX-License-Identifier: BSD-3-Clause"
SPDX_SKIP_DIRS = {"migrations", "__pycache__"}


class Finding:
    __slots__ = ("check", "severity", "library", "path", "message")

    def __init__(self, check, severity, library, path, message):
        self.check = check
        self.severity = severity      # "error" | "warn"
        self.library = library
        self.path = path              # repo-relative str
        self.message = message

    def as_dict(self):
        return {"check": self.check, "severity": self.severity, "library": self.library,
                "path": self.path, "message": self.message}


# --- helpers -----------------------------------------------------------------
def rel(p: Path, root: Path):
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def head(path: Path, n=5):
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            return "".join(next(f, "") for _ in range(n))
    except OSError:
        return ""


def _resolve_pkg(src: Path):
    """The single package directory under src/ (a dir with __init__.py), or None."""
    if not src.is_dir():
        return None
    pkgs = [d for d in sorted(src.iterdir())
            if d.is_dir() and (d / "__init__.py").exists()]
    return pkgs[0] if pkgs else None


def _load_pyproject(pp: Path):
    """Return (parsed_dict_or_None, error_str_or_None)."""
    if not pp.exists():
        return None, None
    try:
        return tomllib.loads(pp.read_text(encoding="utf-8")), None
    except (tomllib.TOMLDecodeError, OSError) as e:
        return None, str(e)


class LibContext:
    """One library read once, shared by every check."""

    def __init__(self, libdir: Path, root: Path):
        self.libdir = libdir
        self.root = root
        self.name = libdir.name
        self.expected_pkg = self.name.replace("-", "_")
        self.src = libdir / "src"
        self.pkg = _resolve_pkg(self.src)
        self.pyproject_path = libdir / "pyproject.toml"
        self.pyproject, self.pyproject_error = _load_pyproject(self.pyproject_path)

    def F(self, check, severity, path: Path, message):
        return Finding(check, severity, self.name, rel(path, self.root), message)


# --- checks (each: LibContext -> list[Finding], independently unit-testable) --
def check_root_files(ctx):
    out = []
    for fn, sev in [("pyproject.toml", "error"), ("README.md", "error"),
                    ("CLAUDE.md", "error"), ("LICENSE", "error"),
                    (".gitignore", "warn"), ("runtests.py", "warn")]:
        if not (ctx.libdir / fn).exists():
            out.append(ctx.F("missing_file", sev, ctx.libdir / fn, f"missing {fn}"))
    return out


def check_docs(ctx):
    docs = ctx.libdir / "docs"
    if not docs.is_dir():
        return [ctx.F("missing_docs", "error", docs, "missing docs/ directory")]
    out = []
    if not (docs / "INDEX.md").exists():
        out.append(ctx.F("missing_file", "error", docs / "INDEX.md", "missing docs/INDEX.md"))
    if not (docs / "progress.md").exists():
        out.append(ctx.F("missing_file", "warn", docs / "progress.md", "missing docs/progress.md"))
    if not (docs / "archive").is_dir():
        out.append(ctx.F("missing_dir", "warn", docs / "archive",
                          "missing docs/archive/ (a placeholder dir is fine)"))
    if (docs / "documentation-structure.md").exists():
        out.append(ctx.F("forbidden_meta_doc", "error", docs / "documentation-structure.md",
                          "docs/documentation-structure.md must not exist — libraries follow the "
                          "the project's conventions (the reduced-set standard), not a per-repo copy"))
    return out


def check_src_layout(ctx):
    if not ctx.src.is_dir():
        return [ctx.F("missing_src", "error", ctx.src, "missing src/ directory")]
    if ctx.pkg is None:
        return [ctx.F("missing_package", "error", ctx.src,
                      "no package (a dir with __init__.py) under src/")]
    init = ctx.pkg / "__init__.py"
    if "__version__" not in init.read_text(encoding="utf-8", errors="replace"):
        return [ctx.F("missing_version", "warn", init,
                      "no __version__ in the package __init__.py")]
    return []


def check_naming(ctx):
    if ctx.pkg is None or ctx.pkg.name == ctx.expected_pkg:
        return []
    return [ctx.F("naming_mismatch", "error", ctx.pkg,
                  f"src package '{ctx.pkg.name}' should be '{ctx.expected_pkg}' "
                  "(underscored form of the repo name)")]


def check_spdx(ctx):
    if ctx.pkg is None:
        return []
    missing = [f for f in sorted(ctx.pkg.rglob("*.py"))
               if not (SPDX_SKIP_DIRS & set(f.parts)) and SPDX not in head(f)]
    if not missing:
        return []
    shown = ", ".join(rel(f, ctx.root) for f in missing[:6])
    more = f" (+{len(missing) - 6} more)" if len(missing) > 6 else ""
    return [ctx.F("missing_spdx", "warn", ctx.pkg,
                  f"{len(missing)} source file(s) missing the SPDX header "
                  f"`# {SPDX}`: {shown}{more}")]


def check_tests_dir(ctx):
    if (ctx.libdir / "tests").is_dir():
        return []
    return [ctx.F("missing_dir", "warn", ctx.libdir / "tests",
                  "no tests/ directory — add it (a placeholder is fine) or document a "
                  "divergence in CLAUDE.md (e.g. a pure-Python library)")]


def check_memory_surface(ctx):
    mem = ctx.libdir / ".claude" / "memory"
    if not mem.exists():
        return []
    return [ctx.F("forbidden_memory", "warn", mem,
                  "library carries its own memory surface — memory is a project-level "
                  "concern held once, at the top level")]


def check_pyproject(ctx):
    if ctx.pyproject_error:
        return [ctx.F("pyproject_unparseable", "error", ctx.pyproject_path,
                      f"could not parse pyproject.toml: {ctx.pyproject_error}")]
    if ctx.pyproject is None:
        return []  # absence already reported by check_root_files
    out = []
    proj = ctx.pyproject.get("project", {})
    if proj.get("name") != ctx.name:
        out.append(ctx.F("pyproject_name", "error", ctx.pyproject_path,
                         f"[project] name '{proj.get('name')}' should match the repo dir '{ctx.name}'"))
    lic = proj.get("license")
    lic_text = lic.get("text") if isinstance(lic, dict) else lic
    if lic_text != "BSD-3-Clause":
        out.append(ctx.F("license", "error", ctx.pyproject_path,
                         f"license should be BSD-3-Clause, found {lic_text!r}"))
    rpy = proj.get("requires-python")
    if not rpy:
        out.append(ctx.F("requires_python", "warn", ctx.pyproject_path,
                         "missing requires-python (should be >=3.10)"))
    else:
        m = re.search(r">=\s*3\.(\d+)", rpy)
        if not m or int(m.group(1)) < 10:
            out.append(ctx.F("requires_python", "warn", ctx.pyproject_path,
                             f"requires-python should allow >=3.10, found {rpy!r}"))
    if "build-system" not in ctx.pyproject:
        out.append(ctx.F("build_system", "warn", ctx.pyproject_path, "missing [build-system] table"))
    where = (ctx.pyproject.get("tool", {}).get("setuptools", {})
             .get("packages", {}).get("find", {}).get("where"))
    if where != ["src"]:
        out.append(ctx.F("packages_where", "warn", ctx.pyproject_path,
                         f'[tool.setuptools.packages.find] where should be ["src"], found {where!r}'))
    return out


CHECKS = [
    check_root_files, check_docs, check_src_layout, check_naming,
    check_spdx, check_tests_dir, check_memory_surface, check_pyproject,
]


def check_library(libdir: Path, root: Path):
    ctx = LibContext(libdir, root)
    return [f for chk in CHECKS for f in chk(ctx)]


# --- discovery + driver ------------------------------------------------------
def discover(root: Path, scope):
    libdir = root / LIBRARIES_DIR
    if not libdir.is_dir():
        return []
    libs = [d for d in sorted(libdir.iterdir())
            if d.is_dir() and (d / "pyproject.toml").exists()]
    if scope:
        wanted = {s.rstrip("/").split("/")[-1] for s in scope}
        libs = [d for d in libs if d.name in wanted]
    return libs


def lint(root: Path, scope):
    libs = discover(root, scope)
    findings = [f for lib in libs for f in check_library(lib, root)]
    return findings, [l.name for l in libs]


# --- output ------------------------------------------------------------------
SEV_ORDER = {"error": 0, "warn": 1}


def render_human(findings, libs):
    out = []
    by_lib = {name: [] for name in libs}
    for f in findings:
        by_lib.setdefault(f.library, []).append(f)
    for name in libs:
        group = sorted(by_lib.get(name, []), key=lambda f: (SEV_ORDER[f.severity], f.check))
        e = sum(f.severity == "error" for f in group)
        w = sum(f.severity == "warn" for f in group)
        status = "OK" if not group else f"{e} error, {w} warn"
        out.append(f"\n{name} — {status}")
        out.append("-" * (len(name) + len(status) + 3))
        for f in group:
            out.append(f"  [{f.severity}] {f.check}: {f.message}")
            out.append(f"      {f.path}")
    total_e = sum(f.severity == "error" for f in findings)
    total_w = sum(f.severity == "warn" for f in findings)
    out.append(f"\nChecked {len(libs)} librar{'y' if len(libs) == 1 else 'ies'}: "
               f"{total_e} error, {total_w} warn.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic library-standards linter (Python instance).")
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("scope", nargs="*", help="optional library names to restrict the check")
    ap.add_argument("--json", action="store_true", help="emit JSON findings")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero on warnings too (default: errors only)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    findings, libs = lint(root, args.scope)

    if args.json:
        print(json.dumps({
            "findings": [f.as_dict() for f in
                         sorted(findings, key=lambda f: (f.library, SEV_ORDER[f.severity], f.check))],
            "summary": {
                "libraries": libs,
                "errors": sum(f.severity == "error" for f in findings),
                "warnings": sum(f.severity == "warn" for f in findings),
            },
        }, indent=2))
    else:
        print(render_human(findings, libs))

    fail = any(f.severity == "error" for f in findings)
    if args.strict:
        fail = fail or any(f.severity == "warn" for f in findings)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
