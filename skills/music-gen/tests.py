#!/usr/bin/env python3
"""Offline stdlib unit tests for the music-gen engine. No network, no API cost.

Run:  python .claude/skills/music-gen/tests.py
"""
import base64
import tempfile
import unittest
from pathlib import Path

import generate as g


class PureHelpers(unittest.TestCase):
    def test_parse_env_file(self):
        text = '# comment\nOPENROUTER_API_KEY = "sk-abc"\n\nJUNK\nFOO=bar\n'
        self.assertEqual(g.parse_env_file(text), {"OPENROUTER_API_KEY": "sk-abc", "FOO": "bar"})

    def test_pick_api_key_canonical_first(self):
        self.assertEqual(g.pick_api_key({"OPENROUTER_API_KEY": "a", "OPEN_ROUTER_API_KEY": "b"}),
                         ("OPENROUTER_API_KEY", "a"))

    def test_pick_api_key_tolerates_variant(self):
        self.assertEqual(g.pick_api_key({"OPEN_ROUTER_API_KEY": "b"}), ("OPEN_ROUTER_API_KEY", "b"))

    def test_pick_api_key_none(self):
        self.assertEqual(g.pick_api_key({"NOPE": "x"}), (None, None))

    def test_build_messages_text_only(self):
        self.assertEqual(g.build_messages("hi", []),
                         [{"role": "user", "content": [{"type": "text", "text": "hi"}]}])

    def test_build_messages_with_refs(self):
        msgs = g.build_messages("hi", ["data:image/png;base64,AAA"])
        self.assertEqual(msgs[0]["content"][1],
                         {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAA"}})

    def test_build_payload_shape(self):
        p = g.build_payload("google/lyria-3-pro-preview", [{"role": "user", "content": []}], "wav")
        self.assertEqual(p["model"], "google/lyria-3-pro-preview")
        self.assertEqual(p["modalities"], ["text", "audio"])
        self.assertEqual(p["audio"], {"format": "wav"})
        self.assertTrue(p["stream"])

    def test_slug(self):
        self.assertEqual(g.slug("google/lyria-3-pro-preview"), "google_lyria-3-pro-preview")

    def test_output_filename(self):
        self.assertEqual(g.output_filename("track", 1, "mp3"), "track.mp3")
        self.assertEqual(g.output_filename("track", 2, "mp3"), "track_2.mp3")


class SseParsing(unittest.TestCase):
    def test_extracts_audio_data(self):
        line = 'data: {"choices":[{"delta":{"audio":{"data":"QUJD","transcript":"la"}}}]}'
        self.assertEqual(g.audio_chunk_from_sse_line(line), "QUJD")

    def test_ignores_done_and_blank_and_text_delta(self):
        self.assertIsNone(g.audio_chunk_from_sse_line("data: [DONE]"))
        self.assertIsNone(g.audio_chunk_from_sse_line(""))
        self.assertIsNone(g.audio_chunk_from_sse_line(": keep-alive comment"))
        self.assertIsNone(g.audio_chunk_from_sse_line('data: {"choices":[{"delta":{"content":"hi"}}]}'))

    def test_ignores_malformed_json(self):
        self.assertIsNone(g.audio_chunk_from_sse_line("data: {not json"))

    def test_iter_audio_chunks(self):
        lines = [
            'data: {"choices":[{"delta":{"audio":{"data":"QQ=="}}}]}',
            ": comment",
            'data: {"choices":[{"delta":{"audio":{"data":"Qg=="}}}]}',
            "data: [DONE]",
        ]
        self.assertEqual(list(g.iter_audio_chunks(lines)), ["QQ==", "Qg=="])

    def test_assemble_audio_concatenates_then_decodes(self):
        raw = b"ID3\x00fake-audio-bytes-\xff\xfe payload"
        b64 = base64.b64encode(raw).decode()
        # split the base64 stream into arbitrary slices, as SSE would deliver it
        chunks = [b64[:5], b64[5:11], b64[11:]]
        self.assertEqual(g.assemble_audio(chunks), raw)

    def test_assemble_audio_empty(self):
        self.assertEqual(g.assemble_audio([]), b"")


class GenerateWithInjectedCaller(unittest.TestCase):
    def _caller_for(self, raw: bytes):
        b64 = base64.b64encode(raw).decode()
        chunks = [b64[: len(b64) // 2], b64[len(b64) // 2:]]
        return lambda payload, api_key: list(chunks)

    def test_generate_saves_file(self):
        raw = b"RIFFfake-wav-data"
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m/x", "prompt", [], 1, d, "KEY", fmt="wav",
                             caller=self._caller_for(raw), log=lambda *a: None, name="track")
            self.assertTrue(res["ok"])
            self.assertEqual(res["count"], 1)
            saved = Path(res["saved"][0])
            self.assertEqual(saved.name, "track.wav")
            self.assertEqual(saved.read_bytes(), raw)

    def test_generate_n_two(self):
        raw = b"abc123"
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m/x", "p", [], 2, d, "KEY", fmt="mp3",
                             caller=self._caller_for(raw), log=lambda *a: None)
            self.assertEqual(res["count"], 2)
            names = sorted(Path(p).name for p in res["saved"])
            self.assertEqual(names, ["m_x.mp3", "m_x_2.mp3"])

    def test_generate_no_audio_is_not_ok(self):
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m/x", "p", [], 1, d, "KEY",
                             caller=lambda payload, key: [], log=lambda *a: None)
            self.assertFalse(res["ok"])
            self.assertEqual(res["count"], 0)

    def test_generate_transport_error_becomes_result(self):
        def boom(payload, key):
            raise RuntimeError("network down")
        with tempfile.TemporaryDirectory() as d:
            res = g.generate("m/x", "p", [], 1, d, "KEY", caller=boom, log=lambda *a: None)
            self.assertFalse(res["ok"])
            self.assertIn("network down", res["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
