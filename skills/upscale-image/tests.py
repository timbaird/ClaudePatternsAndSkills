#!/usr/bin/env python3
"""Offline unit tests for the upscale skill — pure geometry helpers + a real round-trip.

    python .claude/skills/upscale/tests.py
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import upscale  # noqa: E402
from PIL import Image  # noqa: E402


class UpscaleTests(unittest.TestCase):
    # --- pure helpers ---------------------------------------------------------
    def test_cover_scale_takes_larger_ratio(self):
        # 1456x720 -> 5175x2625: height ratio (3.646) > width ratio (3.554)
        self.assertAlmostEqual(upscale.cover_scale(1456, 720, 5175, 2625), 2625 / 720, places=6)

    def test_scaled_dims_round(self):
        self.assertEqual(upscale.scaled_dims(1456, 720, 2625 / 720), (5308, 2625))

    def test_center_crop_box_centers(self):
        # a 5308-wide resize cropped to 5175 trims (5308-5175)//2 = 66 each side
        self.assertEqual(upscale.center_crop_box(5308, 2625, 5175, 2625), (66, 0, 5241, 2625))

    # --- real round-trip (Pillow available) -----------------------------------
    def test_upscale_hits_exact_target_and_dpi(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src.png"
            Image.new("RGB", (1456, 720), (240, 192, 32)).save(src)
            out = Path(d) / "out.png"
            res = upscale.upscale_image(src, out, 5175, 2625, dpi=300)
            self.assertTrue(res["ok"])
            with Image.open(out) as im:
                self.assertEqual(im.size, (5175, 2625))
                dpi = im.info.get("dpi")  # Pillow round-trips DPI as a rational (~299.9994)
                self.assertAlmostEqual(dpi[0], 300, delta=0.1)
                self.assertAlmostEqual(dpi[1], 300, delta=0.1)

    def test_upscale_converts_to_rgb(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src.png"
            Image.new("RGBA", (100, 100), (10, 20, 30, 255)).save(src)
            out = Path(d) / "out.png"
            upscale.upscale_image(src, out, 200, 200)
            with Image.open(out) as im:
                self.assertEqual(im.mode, "RGB")


if __name__ == "__main__":
    unittest.main(verbosity=2)
