#!/usr/bin/env python3
"""
Unit tests for the image-gen engine. Standard library only, no network, no API cost.

Run:  python .claude/skills/image-gen/tests.py

Covers the deterministic units (env parsing, key selection, data-URL round-trip,
request builders, filename construction, response parsing) and an offline run of
generate() with an injected fake caller — so the whole orchestration is exercised
without ever hitting the paid API.
"""
import base64
import io
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate as g  # noqa: E402


class TestEnvParsing(unittest.TestCase):
    def test_basic(self):
        kv = g.parse_env_file('OPENROUTER_API_KEY="abc123"\n# comment\n\nFOO=bar\n')
        self.assertEqual(kv["OPENROUTER_API_KEY"], "abc123")
        self.assertEqual(kv["FOO"], "bar")

    def test_strips_spaces_and_quotes(self):
        kv = g.parse_env_file("OPENROUTER_API_KEY = \"k k\"\nX='v'\n")
        self.assertEqual(kv["OPENROUTER_API_KEY"], "k k")
        self.assertEqual(kv["X"], "v")

    def test_pick_prefers_canonical(self):
        self.assertEqual(
            g.pick_api_key({"OPENROUTER_API_KEY": "a", "OPEN_ROUTER_API_KEY": "b"}),
            ("OPENROUTER_API_KEY", "a"),
        )

    def test_pick_fallback_variant(self):
        self.assertEqual(g.pick_api_key({"OPEN_ROUTER_API_KEY": "b"}), ("OPEN_ROUTER_API_KEY", "b"))

    def test_pick_ignores_empty(self):
        self.assertEqual(g.pick_api_key({"OPENROUTER_API_KEY": "   ", "OPEN_ROUTER_API_KEY": ""}), (None, None))


class TestDataUrl(unittest.TestCase):
    def test_round_trip_png(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.png"
            data = b"\x89PNG\r\n\x1a\nhello"
            p.write_bytes(data)
            url = g.file_to_data_url(p)
            self.assertTrue(url.startswith("data:image/png;base64,"))
            self.assertEqual(g.decode_data_url(url), (data, "png"))

    def test_jpeg_mime(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.jpg"
            p.write_bytes(b"\xff\xd8\xff")
            self.assertTrue(g.file_to_data_url(p).startswith("data:image/jpeg;base64,"))


class TestBuilders(unittest.TestCase):
    def test_build_messages(self):
        m = g.build_messages("hi", ["data:image/png;base64,AAAA"])
        self.assertEqual(m[0]["role"], "user")
        self.assertEqual(m[0]["content"][0], {"type": "text", "text": "hi"})
        self.assertEqual(m[0]["content"][1]["type"], "image_url")

    def test_build_payload_default(self):
        p = g.build_payload("vendor/model", [{"role": "user", "content": []}])
        self.assertEqual(p["model"], "vendor/model")
        self.assertEqual(p["modalities"], ["image", "text"])

    def test_build_payload_custom_modalities(self):
        p = g.build_payload("m", [], modalities=["image"])
        self.assertEqual(p["modalities"], ["image"])

    def test_slug(self):
        self.assertEqual(g.slug("a/b:c"), "a_b_c")

    def test_output_filename(self):
        self.assertEqual(g.output_filename("hero", 1, "png"), "hero.png")
        self.assertEqual(g.output_filename("hero", 2, "jpg"), "hero_2.jpg")


class TestExtract(unittest.TestCase):
    def test_images_shape(self):
        data = b"img"
        url = "data:image/png;base64," + base64.b64encode(data).decode()
        resp = {"choices": [{"message": {"images": [{"type": "image_url", "image_url": {"url": url}}]}}]}
        self.assertEqual(g.extract_images(resp), [(data, "png")])

    def test_content_list_shape(self):
        data = b"j"
        url = "data:image/jpeg;base64," + base64.b64encode(data).decode()
        resp = {"choices": [{"message": {"content": [{"type": "image_url", "image_url": {"url": url}}]}}]}
        self.assertEqual(g.extract_images(resp), [(data, "jpg")])

    def test_empty_and_garbage(self):
        self.assertEqual(g.extract_images({}), [])
        self.assertEqual(g.extract_images({"choices": []}), [])
        self.assertEqual(g.extract_images({"choices": [{"message": {"content": "text only"}}]}), [])


class TestGenerateOffline(unittest.TestCase):
    @staticmethod
    def _one_image_caller(data):
        url = "data:image/png;base64," + base64.b64encode(data).decode()
        def caller(payload, api_key, timeout=180):
            return {"choices": [{"message": {"images": [{"image_url": {"url": url}}]}}]}
        return caller

    def test_saves_candidates_with_fake_caller(self):
        data = b"PNGDATA"
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("vendor/model", "p", [], 2, d, "secret",
                             caller=self._one_image_caller(data), log=lambda *a: None)
            self.assertTrue(res["ok"])
            self.assertEqual(res["count"], 2)
            for path in res["saved"]:
                self.assertEqual(Path(path).read_bytes(), data)

    def test_name_controls_filename(self):
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("vendor/model", "p", [], 1, d, "k",
                             caller=self._one_image_caller(b"X"), log=lambda *a: None, name="hero")
            self.assertTrue(res["saved"][0].endswith("hero.png"))

    def test_extra_images_get_numeric_suffix(self):
        data = b"Y"
        url = "data:image/png;base64," + base64.b64encode(data).decode()
        def two_image_caller(payload, api_key, timeout=180):
            return {"choices": [{"message": {"images": [{"image_url": {"url": url}}, {"image_url": {"url": url}}]}}]}
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("vendor/model", "p", [], 1, d, "k",
                             caller=two_image_caller, log=lambda *a: None, name="coco")
            self.assertTrue(res["saved"][0].endswith("coco.png"))
            self.assertTrue(res["saved"][1].endswith("coco_2.png"))

    def test_http_error_returns_not_ok(self):
        def boom(payload, api_key, timeout=180):
            raise urllib.error.HTTPError("u", 402, "Payment Required", {}, io.BytesIO(b"no credit"))

        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m", "p", [], 1, d, "k", caller=boom, log=lambda *a: None)
            self.assertFalse(res["ok"])
            self.assertEqual(res["count"], 0)
            self.assertIn("402", res["error"])

    def test_no_image_returns_not_ok(self):
        def empty(payload, api_key, timeout=180):
            return {"choices": [{"message": {"content": "I cannot do that"}}]}

        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m", "p", [], 1, d, "k", caller=empty, log=lambda *a: None)
            self.assertFalse(res["ok"])
            self.assertEqual(res["saved"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
