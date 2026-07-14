"""Offline tests for the thumbnail skill. Uses a synthetic hero + Pillow's built-in font (no external
asset), so the render round-trips run anywhere. Run: `.venv/bin/python tests.py`.
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

import thumb


def _hero(d, size=(2000, 1000), colour=(120, 170, 210)):
    p = Path(d) / "hero.png"
    Image.new("RGB", size, colour).save(p)
    return p


class PureHelpers(unittest.TestCase):
    def test_parse_rgb(self):
        self.assertEqual(thumb.parse_rgb("255,200,70", (0, 0, 0)), (255, 200, 70))
        self.assertEqual(thumb.parse_rgb("", (1, 2, 3)), (1, 2, 3))
        self.assertEqual(thumb.parse_rgb(None, (9, 9, 9)), (9, 9, 9))

    def test_cover_fit_exact_size_no_distortion(self):
        im = Image.new("RGB", (2000, 500), (10, 20, 30))   # very wide source
        out = thumb.cover_fit(im, 1280, 720, focus_y=0.5)
        self.assertEqual(out.size, (1280, 720))            # fills the frame exactly (crop, not stretch)

    def test_fit_font_fits_and_shrinks(self):
        im = Image.new("RGB", (1280, 720))
        d = ImageDraw.Draw(im)
        # a title that CAN fit shrinks until it fits the width budget
        fitted = thumb._fit_font(d, "A Medium Title", None, 800, start=110)
        self.assertLessEqual(d.textlength("A Medium Title", font=fitted), 800)
        # a tighter width budget forces a smaller font (probe with a fixed glyph)
        narrow = thumb._fit_font(d, "A Medium Title", None, 200, start=110)
        self.assertLess(d.textlength("W", font=narrow), d.textlength("W", font=fitted))


class BandLayout(unittest.TestCase):
    def test_exact_size_and_under_2mb(self):
        with tempfile.TemporaryDirectory() as d:
            out = thumb.build(_hero(d), "A Short Title", Path(d) / "t.jpg", layout="band")
            im = Image.open(out)
            self.assertEqual(im.size, (1280, 720))
            self.assertLess(out.stat().st_size, 2 * 1024 * 1024)   # under YouTube's 2MB cap

    def test_long_title_still_fits(self):
        with tempfile.TemporaryDirectory() as d:
            out = thumb.build(_hero(d), "A Very Long Thumbnail Title That Must Auto Shrink To Fit",
                              Path(d) / "t.jpg", layout="band")
            self.assertEqual(Image.open(out).size, (1280, 720))

    def test_band_colour_light_and_dark_autocontrast(self):
        with tempfile.TemporaryDirectory() as d:
            light = thumb.build(_hero(d), "T", Path(d) / "l.jpg", layout="band", band_color=(255, 200, 70))
            dark = thumb.build(_hero(d), "T", Path(d) / "k.jpg", layout="band", band_color=(30, 40, 120))
            self.assertEqual(Image.open(light).size, (1280, 720))
            self.assertEqual(Image.open(dark).size, (1280, 720))

    def test_wordmark_renders(self):
        with tempfile.TemporaryDirectory() as d:
            out = thumb.build(_hero(d), "T", Path(d) / "w.jpg", layout="band", wordmark="My Channel")
            self.assertEqual(Image.open(out).size, (1280, 720))

    def test_custom_dimensions(self):
        with tempfile.TemporaryDirectory() as d:
            out = thumb.build(_hero(d), "T", Path(d) / "c.jpg", layout="band", w=1000, h=1000)
            self.assertEqual(Image.open(out).size, (1000, 1000))


class CaptionLayout(unittest.TestCase):
    def test_exact_size_with_subtitle(self):
        with tempfile.TemporaryDirectory() as d:
            out = thumb.build(_hero(d), "Cabin Study", Path(d) / "t.jpg",
                              layout="caption", subtitle="1 hour of calm")
            self.assertEqual(Image.open(out).size, (1280, 720))

    def test_scrim_darkens_the_bottom(self):
        with tempfile.TemporaryDirectory() as d:
            bright = _hero(d, colour=(255, 255, 255))     # a washed-out bright scene
            plain = thumb.build(bright, "T", Path(d) / "plain.jpg", layout="caption", scrim=False)
            scrim = thumb.build(bright, "T", Path(d) / "scrim.jpg", layout="caption", scrim=True)
            # sample a bottom pixel away from the text (top-right of the bottom strip)
            xy = (1200, 700)
            plain_lum = sum(Image.open(plain).convert("RGB").getpixel(xy))
            scrim_lum = sum(Image.open(scrim).convert("RGB").getpixel(xy))
            self.assertLess(scrim_lum, plain_lum)          # the scrim genuinely darkens the bottom


class Candidates(unittest.TestCase):
    def test_sweep_the_crop(self):
        with tempfile.TemporaryDirectory() as d:
            paths = thumb.candidates(_hero(d), "A Title", Path(d) / "cand", n=5, layout="band")
            self.assertEqual(len(paths), 5)
            for p in paths:
                self.assertTrue(p.exists() and Image.open(p).size == (1280, 720))


if __name__ == "__main__":
    unittest.main(verbosity=2)
