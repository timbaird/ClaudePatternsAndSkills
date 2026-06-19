#!/usr/bin/env python3
"""Unit tests for the doc-convention-linter. Stdlib only (no pytest) so they ship
and run with the skill anywhere: `python .claude/skills/doc-convention-linter/tests.py`.

Covers each helper, each of the seven checks in isolation, the scope filter, and a
round-trip integration test (the manual inject/restore test, now automated)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lint  # noqa: E402


# A minimal, fully-correct corpus: one docs/ root, an INDEX linking one good doc.
CLEAN = {
    "docs/INDEX.md": "# Index\n\nThe docs catalogue.\n\n- [good](good.md)\n",
    "docs/good.md": "# Good Doc\n\nA one-paragraph summary.\n\nBody text.\n",
}


def build_tree(spec):
    """Write {relpath: content} into a temp dir; return (TemporaryDirectory, root)."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for relpath, content in spec.items():
        f = root / relpath
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
    return tmp, root


class HelperTests(unittest.TestCase):
    def test_kebab_regex(self):
        ok = ["good.md", "good-name.md", "a1-b2-c3.md"]
        bad = ["Bad.md", "bad_name.md", "Bad-Name.md", "spaces here.md", "x.txt"]
        for n in ok:
            self.assertRegex(n, lint.KEBAB_RE)
        for n in bad:
            self.assertNotRegex(n, lint.KEBAB_RE)

    def test_find_h1(self):
        self.assertEqual(lint.find_h1(["# Title", "x"], 0), (0, "Title"))
        self.assertIsNone(lint.find_h1(["text first", "# Late"], 0))
        self.assertIsNone(lint.find_h1(["## Sub"], 0))

    def test_body_after_frontmatter(self):
        lines = ["---", "name: x", "---", "# Title"]
        self.assertEqual(lint.body_after_frontmatter(lines), 3)
        self.assertEqual(lint.body_after_frontmatter(["# Title"]), 0)

    def test_fenced_line_indices(self):
        lines = ["before", "```", "in fence", "```", "after"]
        self.assertEqual(lint.fenced_line_indices(lines), {1, 2, 3})

    def test_resolve_link(self):
        src = Path("/repo/docs/a.md")
        root = Path("/repo")
        self.assertIsNone(lint.resolve_link(src, "https://x.com", root))
        self.assertIsNone(lint.resolve_link(src, "#anchor", root))
        self.assertEqual(lint.resolve_link(src, "b.md", root), Path("/repo/docs/b.md"))
        # anchor and title are stripped
        self.assertEqual(lint.resolve_link(src, "b.md#sec", root), Path("/repo/docs/b.md"))
        self.assertEqual(lint.resolve_link(src, "../CLAUDE.md", root), Path("/repo/CLAUDE.md"))

    def test_path_in_scope(self):
        self.assertTrue(lint.path_in_scope("docs/a.md", ["docs/a.md"]))
        self.assertTrue(lint.path_in_scope("docs/a.md", ["docs"]))
        self.assertFalse(lint.path_in_scope("docs/b.md", ["docs/a.md"]))
        self.assertFalse(lint.path_in_scope("README.md", ["docs"]))

    def test_links_in_skips_inline_code(self):
        lines = ["a real [x](real.md) and an example `[y](ex.md)`"]
        found = lint.links_in(lines, set())
        self.assertEqual([t for _, t in found], ["real.md"])


class CheckTests(unittest.TestCase):
    """Each check in isolation against a synthetic corpus."""

    def checks_for(self, spec, scope=None):
        tmp, root = build_tree(spec)
        self.addCleanup(tmp.cleanup)
        findings, _, _ = lint.lint(root, scope)
        return findings

    def kinds(self, findings, path=None):
        return {f.check for f in findings if path is None or f.path == path}

    def test_clean_tree_has_no_findings(self):
        self.assertEqual(self.checks_for(CLEAN), [])

    def test_broken_link(self):
        spec = dict(CLEAN)
        spec["docs/good.md"] = "# Good\n\nSummary.\n\nSee [x](missing-xyz.md).\n"
        f = self.checks_for(spec)
        self.assertIn("broken_link", self.kinds(f, "docs/good.md"))

    def test_filename_not_kebab(self):
        spec = dict(CLEAN)
        spec["docs/Bad_Name.md"] = "# Bad\n\nSummary.\n"
        self.assertIn("filename_not_kebab", self.kinds(self.checks_for(spec)))

    def test_h1_missing(self):
        spec = dict(CLEAN)
        spec["docs/nohead.md"] = "No heading line.\n\nMore.\n"
        self.assertIn("h1_missing", self.kinds(self.checks_for(spec), "docs/nohead.md"))

    def test_summary_missing(self):
        spec = dict(CLEAN)
        spec["docs/nosum.md"] = "# Title\n\n## Section\n\nbody\n"
        self.assertIn("summary_missing", self.kinds(self.checks_for(spec), "docs/nosum.md"))

    def test_not_indexed_and_orphaned(self):
        spec = dict(CLEAN)
        spec["docs/lonely.md"] = "# Lonely\n\nSummary.\n"  # exists, nothing links/indexes it
        kinds = self.kinds(self.checks_for(spec), "docs/lonely.md")
        self.assertIn("not_indexed", kinds)
        self.assertIn("orphaned", kinds)

    def test_was_phrasing(self):
        spec = dict(CLEAN)
        spec["docs/INDEX.md"] = "# Index\n\nCatalogue.\n\n- [good](good.md)\n- [h](hist.md)\n"
        spec["docs/hist.md"] = "# Hist\n\nThis API was formerly the only one.\n"
        self.assertIn("was_phrasing", self.kinds(self.checks_for(spec), "docs/hist.md"))

    def test_indexed_doc_is_not_orphaned(self):
        # good.md is linked from INDEX, so it must not be flagged orphaned/not_indexed
        kinds = self.kinds(self.checks_for(CLEAN), "docs/good.md")
        self.assertNotIn("orphaned", kinds)
        self.assertNotIn("not_indexed", kinds)


class ScopeTests(unittest.TestCase):
    SPEC = {
        "docs/INDEX.md": "# Index\n\nCatalogue.\n\n- [a](a.md)\n- [b](b.md)\n",
        "docs/a.md": "# A\n\nSummary.\n\n[bad](nope-a.md)\n",
        "docs/b.md": "# B\n\nSummary.\n\n[to a](a.md) and [bad](nope-b.md)\n",
    }

    def setUp(self):
        self.tmp, self.root = build_tree(self.SPEC)
        self.addCleanup(self.tmp.cleanup)

    def test_unscoped_sees_both_broken_links(self):
        findings, _, _ = lint.lint(self.root)
        paths = {f.path for f in findings if f.check == "broken_link"}
        self.assertEqual(paths, {"docs/a.md", "docs/b.md"})

    def test_file_scope_reports_only_that_file(self):
        findings, n_files, n_roots = lint.lint(self.root, ["docs/a.md"])
        self.assertTrue(findings, "file scope must not silently scan nothing")
        self.assertTrue(all(f.path == "docs/a.md" for f in findings))
        self.assertEqual(n_files, 1)
        self.assertEqual(n_roots, 1)

    def test_scope_keeps_global_context(self):
        # a.md is linked by b.md, so even when scoping to a.md it must NOT be orphaned
        findings, _, _ = lint.lint(self.root, ["docs/a.md"])
        self.assertNotIn("orphaned", {f.check for f in findings})


class RoundTripTest(unittest.TestCase):
    """The manual inject/restore test, automated."""

    def test_inject_then_restore(self):
        tmp, root = build_tree(CLEAN)
        self.addCleanup(tmp.cleanup)
        good = root / "docs/good.md"
        original = good.read_text()

        self.assertEqual(lint.lint(root)[0], [], "clean baseline")

        good.write_text(original + "\nSee [x](does-not-exist.md).\n")
        findings, _, _ = lint.lint(root)
        self.assertIn("broken_link", {f.check for f in findings})

        good.write_text(original)
        self.assertEqual(lint.lint(root)[0], [], "restored to clean")


if __name__ == "__main__":
    unittest.main(verbosity=2)
