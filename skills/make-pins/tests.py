"""Offline tests for make-pins. Uses a synthetic scene + Pillow's built-in font (no external asset).
Run: `.venv/bin/python tests.py`.
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import make_pins as mp


def _scene(d, size=(1600, 900), colour=(90, 140, 200)):
    p = Path(d) / "scene.png"
    Image.new("RGB", size, colour).save(p)
    return p


class PureHelpers(unittest.TestCase):
    def test_parse_rgb(self):
        self.assertEqual(mp.parse_rgb("239,227,207", (0, 0, 0)), (239, 227, 207))
        self.assertEqual(mp.parse_rgb(None, (1, 2, 3)), (1, 2, 3))


class BuildPin(unittest.TestCase):
    def test_exact_2x3_size(self):
        with tempfile.TemporaryDirectory() as d:
            out = mp.build_pin(_scene(d), "Cozy Rainy Lofi", Path(d) / "p.jpg",
                               cta="Full mix on YouTube", handle="@channel")
            self.assertEqual(Image.open(out).size, (1000, 1500))

    def test_wide_and_square_scenes_both_fill_frame(self):
        with tempfile.TemporaryDirectory() as d:
            wide = mp.build_pin(_scene(d, (2000, 800)), "T", Path(d) / "w.jpg")
            square = mp.build_pin(_scene(d, (1200, 1200)), "T", Path(d) / "s.jpg")
            self.assertEqual(Image.open(wide).size, (1000, 1500))
            self.assertEqual(Image.open(square).size, (1000, 1500))

    def test_empty_cta_and_handle(self):
        with tempfile.TemporaryDirectory() as d:
            out = mp.build_pin(_scene(d), "Just the headline", Path(d) / "p.jpg")  # no cta/handle
            self.assertEqual(Image.open(out).size, (1000, 1500))

    def test_custom_dimensions(self):
        with tempfile.TemporaryDirectory() as d:
            out = mp.build_pin(_scene(d), "T", Path(d) / "c.jpg", w=800, h=1200)
            self.assertEqual(Image.open(out).size, (800, 1200))

    def test_centre_band_sharper_than_edges(self):
        # the middle band is the un-blurred scene; the top edge is the GaussianBlur fill.
        with tempfile.TemporaryDirectory() as d:
            # a scene with vertical detail so blur vs sharp is measurable
            scene = Image.new("RGB", (1600, 900))
            for x in range(0, 1600, 8):
                for y in range(900):
                    scene.putpixel((x, y), (255, 255, 255))
            sp = Path(d) / "striped.png"
            scene.save(sp)
            out = mp.build_pin(sp, "", Path(d) / "p.jpg")
            im = Image.open(out).convert("L")
            def row_variance(y):
                px = [im.getpixel((x, y)) for x in range(0, 1000, 4)]
                m = sum(px) / len(px)
                return sum((v - m) ** 2 for v in px) / len(px)
            centre_var = row_variance(750)   # middle band (sharp stripes → high variance)
            edge_var = row_variance(30)       # top band (blurred → low variance)
            self.assertGreater(centre_var, edge_var)


if __name__ == "__main__":
    unittest.main(verbosity=2)
