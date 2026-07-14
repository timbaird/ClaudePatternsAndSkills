#!/usr/bin/env python3
"""Offline unit tests for schedule_social — every per-platform builder + the allowlist guard.
Run: python .claude/skills/schedule-social/tests.py   (no network, no API cost)."""
import unittest

import schedule_social as ss

CFG = {  # a fake resolved config for guard tests (placeholder ids)
    "destinations": [
        {"platform": "youtube", "native_id": "UC_CHANNEL_A_YT", "handle": "@channel-a"},
        {"platform": "tiktok", "native_id": "TT_CHANNEL_A", "handle": "@channel.a"},
        {"platform": "pinterest", "native_id": "PIN_CHANNEL_A", "handle": "@channela",
         "boards": {"My Board": "BOARD_123"}},
    ],
}
ACCTS = [
    {"platform": "youtube", "id": "oa_loc_UC_CHANNEL_A_YT_profile"},
    {"platform": "youtube", "id": "oa_loc_UC_CHANNEL_B_YT_profile"},   # a different channel's YT
    {"platform": "tiktok", "id": "oa_loc_TT_CHANNEL_A_business"},
]


class Builders(unittest.TestCase):
    def test_youtube_short(self):
        b = ss.youtube_payload("ACC", "u.mp4", description="d", title="t", schedule_date="D", user_id="U")
        self.assertEqual(b["youtubePostDetails"], {"type": "short", "title": "t"})
        self.assertEqual(b["media"][0]["type"], "video/mp4")
        self.assertEqual(b["accountIds"], ["ACC"])
        self.assertEqual(b["status"], "scheduled")

    def test_youtube_video_type(self):
        b = ss.youtube_payload("A", "u", description="d", title="t", schedule_date="D", user_id="U", yt_type="video")
        self.assertEqual(b["youtubePostDetails"]["type"], "video")

    def test_youtube_requires_title(self):
        with self.assertRaises(ValueError):
            ss.youtube_payload("A", "u", description="d", title=None, schedule_date="D", user_id="U")

    def test_youtube_bad_type(self):
        with self.assertRaises(ValueError):
            ss.youtube_payload("A", "u", description="d", title="t", schedule_date="D", user_id="U", yt_type="reel")

    def test_tiktok(self):
        b = ss.tiktok_payload("ACC", "u.mp4", description="cap", schedule_date="D", user_id="U")
        self.assertEqual(b["tiktokPostDetails"], {"privacyLevel": "PUBLIC_TO_EVERYONE"})
        self.assertNotIn("youtubePostDetails", b)

    def test_pinterest(self):
        b = ss.pinterest_payload("ACC", "u.jpg", description="d", title="t",
                                 link="https://youtu.be/x", board_id="B", schedule_date="D", user_id="U")
        self.assertEqual(b["pinterestPostDetails"]["link"], "https://youtu.be/x")
        self.assertEqual(b["pinterestPostDetails"]["boardIds"], {"ACC": ["B"]})
        self.assertEqual(b["media"][0]["type"], "image/jpeg")

    def test_instagram(self):
        b = ss.instagram_payload("ACC", "u.mp4", description="cap", schedule_date="D", user_id="U")
        self.assertEqual(b["media"][0]["type"], "video/mp4")
        self.assertEqual(b["accountIds"], ["ACC"])
        self.assertEqual(b["status"], "scheduled")
        self.assertNotIn("youtubePostDetails", b)  # no detail block — IG auto-Reels a video

    def test_facebook(self):
        b = ss.facebook_payload("ACC", "u.mp4", description="cap", schedule_date="D", user_id="U")
        self.assertEqual(b["media"][0]["type"], "video/mp4")
        self.assertEqual(b["accountIds"], ["ACC"])
        self.assertEqual(b["status"], "scheduled")

    def test_pinterest_requires_link_and_board(self):
        with self.assertRaises(ValueError):
            ss.pinterest_payload("A", "u", description="d", title="t", link=None, board_id="B",
                                 schedule_date="D", user_id="U")
        with self.assertRaises(ValueError):
            ss.pinterest_payload("A", "u", description="d", title="t", link="l", board_id=None,
                                 schedule_date="D", user_id="U")


class Guard(unittest.TestCase):
    def test_find_destination_ok(self):
        self.assertEqual(ss.find_destination(CFG, "tiktok")["handle"], "@channel.a")

    def test_find_destination_refuses_unlisted(self):
        with self.assertRaises(SystemExit):
            ss.find_destination(CFG, "instagram")  # not on allowlist

    def test_resolve_board_name_to_id(self):
        self.assertEqual(ss.resolve_board_id(CFG, "pinterest", "My Board"), "BOARD_123")

    def test_resolve_board_passthrough_id(self):
        self.assertEqual(ss.resolve_board_id(CFG, "pinterest", "9999"), "9999")

    def test_resolve_account_matches_allowlisted(self):
        ss.get_accounts = lambda cfg: ACCTS  # inject
        cfg = dict(CFG); cfg["location_id"] = "loc"; cfg["read_pit"] = "x"; cfg["endpoint"] = "x"
        self.assertEqual(ss.resolve_account_id(cfg, "youtube"), "oa_loc_UC_CHANNEL_A_YT_profile")

    def test_resolve_account_refuses_when_native_absent(self):
        ss.get_accounts = lambda cfg: [a for a in ACCTS if "UC_CHANNEL_A_YT" not in a["id"]]  # only channel B's YT
        cfg = dict(CFG); cfg["location_id"] = "loc"; cfg["read_pit"] = "x"; cfg["endpoint"] = "x"
        with self.assertRaises(SystemExit):
            ss.resolve_account_id(cfg, "youtube")  # must NOT fall through to the wrong YT account


if __name__ == "__main__":
    unittest.main(verbosity=2)
