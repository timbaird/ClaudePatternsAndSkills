#!/usr/bin/env python3
"""Offline stdlib unit tests for the video-gen engine. No network, no API cost.

Run:  python .claude/skills/video-gen/tests.py
"""
import tempfile
import unittest
from pathlib import Path

import generate as g


class PureHelpers(unittest.TestCase):
    def test_parse_env_file(self):
        self.assertEqual(g.parse_env_file('OPENROUTER_API_KEY="sk-x"\n# c\nFOO=bar'),
                         {"OPENROUTER_API_KEY": "sk-x", "FOO": "bar"})

    def test_pick_api_key(self):
        self.assertEqual(g.pick_api_key({"OPEN_ROUTER_API_KEY": "b"}), ("OPEN_ROUTER_API_KEY", "b"))

    def test_slug_and_filename(self):
        self.assertEqual(g.slug("kwaivgi/kling-v3.0-std"), "kwaivgi_kling-v3.0-std")
        self.assertEqual(g.output_filename("clip", 1), "clip.mp4")
        self.assertEqual(g.output_filename("clip", 3), "clip_3.mp4")

    def test_build_frame_images_loop(self):
        frames = g.build_frame_images(first_url="data:img", loop=True)
        self.assertEqual([f["frame_type"] for f in frames], ["first_frame", "last_frame"])
        # same image in both -> seamless loop
        self.assertEqual(frames[0]["image_url"]["url"], frames[1]["image_url"]["url"])

    def test_build_frame_images_first_only(self):
        frames = g.build_frame_images(first_url="data:img", loop=False)
        self.assertEqual([f["frame_type"] for f in frames], ["first_frame"])

    def test_build_frame_images_explicit_last(self):
        frames = g.build_frame_images(first_url="data:a", last_url="data:b", loop=False)
        self.assertEqual([f["frame_type"] for f in frames], ["first_frame", "last_frame"])
        self.assertEqual(frames[1]["image_url"]["url"], "data:b")

    def test_build_frame_images_none(self):
        self.assertEqual(g.build_frame_images(), [])

    def test_build_submit_payload_omits_unset(self):
        p = g.build_submit_payload("m/x", "prompt")
        self.assertEqual(p, {"model": "m/x", "prompt": "prompt"})

    def test_build_submit_payload_includes_supplied(self):
        p = g.build_submit_payload("m/x", "p", frame_images=[{"a": 1}], duration=5,
                                   resolution="720p", aspect_ratio="16:9")
        self.assertEqual(p["duration"], 5)
        self.assertEqual(p["resolution"], "720p")
        self.assertEqual(p["aspect_ratio"], "16:9")
        self.assertEqual(p["frame_images"], [{"a": 1}])

    def test_job_status_and_download_url(self):
        self.assertEqual(g.job_status({"status": "pending"}), "pending")
        self.assertEqual(g.job_status({}), "")
        self.assertEqual(g.download_url({"unsigned_urls": ["u1", "u2"]}), "u1")
        self.assertIsNone(g.download_url({"unsigned_urls": []}))
        self.assertIsNone(g.download_url({}))


class Orchestration(unittest.TestCase):
    def _fakes(self, poll_sequence, video=b"MP4DATA"):
        """Build fake submit/poll/download. poll_sequence is a list of status responses."""
        calls = {"poll": 0}

        def submit(payload, key):
            return {"id": "job-1", "polling_url": "https://poll/job-1", "status": "pending"}

        def poll(url, key):
            i = min(calls["poll"], len(poll_sequence) - 1)
            calls["poll"] += 1
            return poll_sequence[i]

        def download(url, key):
            return video

        return submit, poll, download

    def test_completes_and_downloads(self):
        submit, poll, download = self._fakes([
            {"status": "pending"},
            {"status": "completed", "unsigned_urls": ["https://cdn/v.mp4"]},
        ], video=b"MP4DATA")
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("kwaivgi/kling-v3.0-std", "drift", 1, d, "KEY",
                             submit=submit, poll=poll, download=download,
                             sleep=lambda s: None, log=lambda *a: None, interval=1, max_wait=10)
            self.assertTrue(res["ok"])
            self.assertEqual(res["count"], 1)
            saved = Path(res["saved"][0])
            self.assertEqual(saved.name, "kwaivgi_kling-v3.0-std.mp4")
            self.assertEqual(saved.read_bytes(), b"MP4DATA")

    def test_terminal_failure_surfaces_error(self):
        submit, poll, download = self._fakes([{"status": "failed", "error": "nsfw block"}])
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m/x", "p", 1, d, "KEY", submit=submit, poll=poll, download=download,
                             sleep=lambda s: None, log=lambda *a: None, interval=1, max_wait=10)
            self.assertFalse(res["ok"])
            self.assertIn("nsfw block", res["error"])

    def test_timeout(self):
        submit, poll, download = self._fakes([{"status": "pending"}])
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m/x", "p", 1, d, "KEY", submit=submit, poll=poll, download=download,
                             sleep=lambda s: None, log=lambda *a: None, interval=1, max_wait=3)
            self.assertFalse(res["ok"])
            self.assertIn("timed out", res["error"])

    def test_no_polling_url(self):
        def submit(payload, key):
            return {"id": "x", "status": "pending"}  # missing polling_url
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m/x", "p", 1, d, "KEY", submit=submit,
                             poll=lambda u, k: {}, download=lambda u, k: b"",
                             sleep=lambda s: None, log=lambda *a: None, interval=1, max_wait=3)
            self.assertFalse(res["ok"])
            self.assertIn("no polling_url", res["error"])

    def test_two_clips(self):
        submit, poll, download = self._fakes([
            {"status": "completed", "unsigned_urls": ["https://cdn/v.mp4"]},
        ], video=b"X")
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m/x", "p", 2, d, "KEY", submit=submit, poll=poll, download=download,
                             sleep=lambda s: None, log=lambda *a: None, interval=1, max_wait=10, name="clip")
            self.assertEqual(res["count"], 2)
            self.assertEqual(sorted(Path(p).name for p in res["saved"]), ["clip.mp4", "clip_2.mp4"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
