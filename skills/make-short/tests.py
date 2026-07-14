"""Offline/local tests for make-short. Run: `.venv/bin/python tests.py`.

`render_overlay`, `parse_rgb`, `find_ffmpeg`, and the ffmpeg command assembly (via an injected `run`)
need no ffmpeg. The end-to-end render generates its own test clip + tone and needs a working ffmpeg
(system PATH or the bundled imageio-ffmpeg); it skips if none is resolvable.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import make_short as ms


class PureHelpers(unittest.TestCase):
    def test_parse_rgb(self):
        self.assertEqual(ms.parse_rgb("239,227,207", (0, 0, 0)), (239, 227, 207))
        self.assertEqual(ms.parse_rgb(None, (1, 2, 3)), (1, 2, 3))

    def test_find_ffmpeg_returns_a_binary(self):
        ff = ms.find_ffmpeg()
        self.assertTrue(ff and Path(ff).exists(), "expected system ffmpeg or bundled imageio-ffmpeg")


class Overlay(unittest.TestCase):
    def test_overlay_size_and_has_text(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ov.png"
            ms.render_overlay("A hook line", "Full mix on YouTube", "@channel", p)
            im = Image.open(p)
            self.assertEqual(im.size, (ms.W, ms.H))          # 1080×1920
            alpha = im.getchannel("A")
            self.assertGreater(alpha.getextrema()[1], 0)     # some non-transparent pixels (text drawn)

    def test_overlay_empty_cta_and_handle(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ov.png"
            ms.render_overlay("Just the hook", "", "", p)    # empty cta/handle must not error
            self.assertEqual(Image.open(p).size, (ms.W, ms.H))


class CommandAssembly(unittest.TestCase):
    def test_build_short_cmd(self):
        captured = {}

        def fake_run(cmd, check):
            captured["cmd"] = cmd
            Path(cmd[-1]).write_bytes(b"stub")   # pretend ffmpeg produced the file

        with tempfile.TemporaryDirectory() as d:
            out = str(Path(d) / "short.mp4")
            ms.build_short("loop.mp4", "track.mp3", out, "Hook", cta="CTA", handle="@h",
                           duration=70.0, audio_start=20.0, ffmpeg="/usr/bin/ffmpeg", run=fake_run)
            cmd = captured["cmd"]
            self.assertEqual(cmd[0], "/usr/bin/ffmpeg")
            self.assertIn("-stream_loop", cmd)               # the visual loops
            self.assertIn("loop.mp4", cmd)
            self.assertIn("track.mp3", cmd)
            self.assertEqual(cmd[-1], out)
            self.assertIn("20.0", cmd)                       # audio-start
            # the fade-out start = duration - 2 appears in the -af argument
            self.assertTrue(any("afade=t=out:st=68.0" in str(x) for x in cmd))
            self.assertIn("1080:1920", " ".join(cmd))        # 9:16 reframe in the filter graph


class EndToEnd(unittest.TestCase):
    def test_real_render(self):
        ff = ms.find_ffmpeg()
        if not ff:
            self.skipTest("no ffmpeg resolvable")
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            loop, audio, out = d / "loop.mp4", d / "tone.m4a", d / "short.mp4"
            subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi",
                            "-i", "testsrc=size=1280x720:rate=24:duration=2", str(loop)], check=True)
            subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi",
                            "-i", "sine=frequency=440:duration=3", str(audio)], check=True)
            ms.build_short(str(loop), str(audio), str(out), "Test hook",
                           duration=2.0, audio_start=0.0, ffmpeg=ff)
            self.assertTrue(out.exists() and out.stat().st_size > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
