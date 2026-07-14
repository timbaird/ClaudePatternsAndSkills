#!/usr/bin/env python3
"""Offline tests for review-slides. Run with the venv python: `.venv/bin/python tests.py`.

Covers the pure `soffice` resolver and a real PDF -> PNG rasterise round-trip. The render test uses a
`.pdf` input, which skips LibreOffice — so the core rasterisation is exercised with PyMuPDF alone (no
system app needed). LibreOffice itself is a system dependency and is not tested here.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import render_deck as rd


class FindSoffice(unittest.TestCase):
    def test_found_on_path(self):
        with mock.patch.object(rd.shutil, "which", side_effect=lambda c: "/usr/bin/soffice" if c == "soffice" else None):
            self.assertEqual(rd.find_soffice(), "/usr/bin/soffice")

    def test_libreoffice_alias_on_path(self):
        with mock.patch.object(rd.shutil, "which", side_effect=lambda c: "/opt/libreoffice" if c == "libreoffice" else None):
            self.assertEqual(rd.find_soffice(), "/opt/libreoffice")

    def test_mac_fallback_when_app_present(self):
        with tempfile.NamedTemporaryFile(suffix="-soffice") as fake_app:
            with mock.patch.object(rd.shutil, "which", return_value=None), \
                 mock.patch.object(rd, "MAC_SOFFICE", fake_app.name):
                self.assertEqual(rd.find_soffice(), fake_app.name)

    def test_none_when_absent(self):
        with mock.patch.object(rd.shutil, "which", return_value=None), \
             mock.patch.object(rd, "MAC_SOFFICE", "/no/such/soffice"):
            self.assertIsNone(rd.find_soffice())


class MainFlow(unittest.TestCase):
    def test_deck_not_found_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            argv = ["render_deck.py", "--deck", str(Path(d) / "missing.pptx"), "--out", str(Path(d) / "o")]
            with mock.patch.object(sys, "argv", argv):
                self.assertEqual(rd.main(), 2)

    def test_pdf_renders_one_png_per_page(self):
        import fitz  # PyMuPDF — present in the skill venv
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            pdf = d / "deck.pdf"
            doc = fitz.open()
            for _ in range(3):
                doc.new_page(width=320, height=180)
            doc.save(str(pdf))
            doc.close()

            out = d / "review"
            argv = ["render_deck.py", "--deck", str(pdf), "--out", str(out), "--dpi", "72"]
            with mock.patch.object(sys, "argv", argv):
                rc = rd.main()
            self.assertEqual(rc, 0)
            pngs = sorted(out.glob("slide-*.png"))
            self.assertEqual([p.name for p in pngs], ["slide-001.png", "slide-002.png", "slide-003.png"])
            self.assertTrue(all(p.stat().st_size > 0 for p in pngs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
