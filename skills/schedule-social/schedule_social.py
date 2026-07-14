#!/usr/bin/env python3
"""schedule_social.py — deterministic engine to schedule ONE social post via GHL Social Planner.

Channel- and platform-agnostic. Same args -> same request (no LLM in the loop). It:
  1. resolves the destination from the CHANNEL'S ALLOWLIST (the composite-key guard, built in) —
     you pass a factory channel slug, never a GHL display name;
  2. uploads the media to GHL's CDN;
  3. builds the correct per-platform create-post payload (per-platform builder functions);
  4. schedules the post.

Per-platform field mechanics live in the builder functions below + SKILL.md (the single source of truth,
so no session ever re-probes GHL's field names).

Config (non-secret) from repo-root `distribution.yaml` + `channels/<slug>/distribution.yaml`;
secret PITs from `.env` (never printed).
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

try:
    import requests
    import yaml
except ImportError:
    sys.exit("schedule-social needs `requests` + `PyYAML` — see SKILL.md (per-skill .venv).")

REST_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"


# --------------------------------------------------------------------------- config
def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p, *p.parents]:
        if (cand / "distribution.yaml").is_file():
            return cand
    sys.exit("could not locate repo-root distribution.yaml")


def load_env(root: Path) -> dict:
    env = dict(os.environ)
    envfile = root / ".env"
    if envfile.is_file():
        for line in envfile.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def load_config(channel: str, start: Path | None = None) -> dict:
    root = find_repo_root(start or Path.cwd())
    shared = yaml.safe_load((root / "distribution.yaml").read_text())["ghl"]
    chpath = root / "channels" / channel / "distribution.yaml"
    if not chpath.is_file():
        sys.exit(f"no distribution.yaml for channel '{channel}' at {chpath}")
    ch = yaml.safe_load(chpath.read_text())
    env = load_env(root)
    read_pit = env.get(shared.get("read_pit_env", "GHL_SOCIAL_READ_PIT"))
    write_pit = env.get(shared.get("write_pit_env", "GHL_SOCIAL_WRITE_PIT"))
    if not write_pit:
        sys.exit("write PIT not set in .env")
    return {
        "root": root,
        "location_id": shared["location_id"],
        "endpoint": shared.get("mcp_endpoint", f"{REST_BASE}/mcp/anthropic/v2"),
        "read_pit": read_pit or write_pit,
        "write_pit": write_pit,
        "user_id": ch["ghl_user_id"],
        "destinations": ch.get("destinations", []),
    }


# ------------------------------------------------- per-platform payload builders (PURE + TESTABLE)
def youtube_payload(account_id, media_url, *, description, title, schedule_date, user_id,
                    yt_type="short", **_ignored):
    """YouTube Short/video. `youtubePostDetails.type` MUST be 'short' or 'video'. Description keeps the link."""
    if yt_type not in ("short", "video"):
        raise ValueError("yt_type must be 'short' or 'video'")
    if not title:
        raise ValueError("youtube requires a title")
    return {
        "accountIds": [account_id], "summary": description, "type": "post", "userId": user_id,
        "media": [{"url": media_url, "type": "video/mp4"}], "status": "scheduled",
        "scheduleDate": schedule_date, "youtubePostDetails": {"type": yt_type, "title": title},
    }


def tiktok_payload(account_id, media_url, *, description, schedule_date, user_id,
                   privacy="PUBLIC_TO_EVERYONE", **_ignored):
    """TikTok video. Caption = description (no clickable link on TikTok)."""
    return {
        "accountIds": [account_id], "summary": description, "type": "post", "userId": user_id,
        "media": [{"url": media_url, "type": "video/mp4"}], "status": "scheduled",
        "scheduleDate": schedule_date, "tiktokPostDetails": {"privacyLevel": privacy},
    }


def pinterest_payload(account_id, media_url, *, description, title, link, board_id,
                      schedule_date, user_id, **_ignored):
    """Pinterest pin. link is the destination URL; boardIds is an object keyed by the full account id."""
    if not link:
        raise ValueError("pinterest requires --link (the pin destination URL)")
    if not board_id:
        raise ValueError("pinterest requires --board (a board id or name from the channel allowlist)")
    return {
        "accountIds": [account_id], "summary": description, "type": "post", "userId": user_id,
        "media": [{"url": media_url, "type": "image/jpeg"}], "status": "scheduled",
        "scheduleDate": schedule_date,
        "pinterestPostDetails": {"link": link, "title": title, "boardIds": {account_id: [board_id]}},
    }


def instagram_payload(account_id, media_url, *, description, schedule_date, user_id, **_ignored):
    """Instagram Reel. A professional IG account publishes any video post as a Reel — no detail block
    or link needed (IG captions aren't clickable). Caption = description."""
    return {
        "accountIds": [account_id], "summary": description, "type": "post", "userId": user_id,
        "media": [{"url": media_url, "type": "video/mp4"}], "status": "scheduled",
        "scheduleDate": schedule_date,
    }


def facebook_payload(account_id, media_url, *, description, schedule_date, user_id, **_ignored):
    """Facebook Page Reel. A single video posted to a Page publishes as a Reel — no detail block.
    Reels only (never link posts): FB throttles off-platform links. Caption = description."""
    return {
        "accountIds": [account_id], "summary": description, "type": "post", "userId": user_id,
        "media": [{"url": media_url, "type": "video/mp4"}], "status": "scheduled",
        "scheduleDate": schedule_date,
    }


BUILDERS = {"youtube": youtube_payload, "tiktok": tiktok_payload, "pinterest": pinterest_payload,
            "instagram": instagram_payload, "facebook": facebook_payload}
MEDIA_MIME = {"youtube": "video/mp4", "tiktok": "video/mp4", "pinterest": "image/jpeg",
              "instagram": "video/mp4", "facebook": "video/mp4"}


# ------------------------------------------------------------------------- HTTP + guard
def _mcp(cfg, pit, name, arguments):
    r = requests.post(cfg["endpoint"], headers={
        "Authorization": f"Bearer {pit}", "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": name, "arguments": arguments}}, timeout=60)
    for line in r.text.splitlines():
        if line.startswith("data: "):
            outer = json.loads(line[6:])
            return json.loads(outer["result"]["content"][0]["text"])
    raise RuntimeError(f"no SSE data in response: {r.text[:200]}")


def get_accounts(cfg):
    res = _mcp(cfg, cfg["read_pit"], "execute_operation",
               {"operationId": "get-account", "params": {"locationId": cfg["location_id"]},
                "reason": "schedule-social: resolve account"})
    return res.get("data", {}).get("results", {}).get("accounts", [])


def find_destination(cfg, platform):
    """The channel's allowlisted destination for this platform. Refuses if not allowlisted."""
    matches = [d for d in cfg["destinations"] if d.get("platform") == platform]
    if not matches:
        sys.exit(f"GUARD: platform '{platform}' is not on this channel's allowlist — refusing.")
    if len(matches) > 1:
        sys.exit(f"GUARD: multiple '{platform}' destinations allowlisted; ambiguous — refusing.")
    return matches[0]


def resolve_account_id(cfg, platform):
    """Composite-key guard: allowlisted native_id -> the live GHL account id carrying it. Refuses otherwise."""
    dest = find_destination(cfg, platform)
    native = str(dest["native_id"])
    for acct in get_accounts(cfg):
        if acct.get("platform") == platform and native in acct.get("id", ""):
            return acct["id"]
    sys.exit(f"GUARD: no connected {platform} account matches allowlisted native_id {native} — refusing.")


def resolve_board_id(cfg, platform, board):
    if platform != "pinterest" or not board:
        return board
    dest = find_destination(cfg, platform)
    boards = dest.get("boards", {})
    return boards.get(board, board)  # name -> id, or pass through if already an id


def upload_media(cfg, file_path, mime):
    src = Path(file_path)
    if not src.is_file():
        sys.exit(f"media not found: {src}")
    # copy to a local temp first (Drive File Stream lazy-loads -> upload read can fail)
    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / src.name
        shutil.copy(src, local)
        with open(local, "rb") as fh:
            r = requests.post(f"{REST_BASE}/medias/upload-file",
                              params={"locationId": cfg["location_id"]},
                              headers={"Authorization": f"Bearer {cfg['write_pit']}",
                                       "Version": GHL_VERSION, "Accept": "application/json"},
                              files={"file": (src.name, fh, mime)},
                              data={"hosted": "false", "name": src.name}, timeout=300)
    r.raise_for_status()
    url = r.json().get("url")
    if not url:
        sys.exit(f"media upload returned no url: {r.text[:200]}")
    return url


def create_post(cfg, body):
    res = _mcp(cfg, cfg["write_pit"], "execute_operation",
               {"operationId": "create-post", "idempotencyKey": f"sched-{uuid.uuid4().hex[:16]}",
                "reason": "schedule-social", "params": {"locationId": cfg["location_id"], "body": body}})
    return res


# ---------------------------------------------------------------------------- orchestration
def schedule(channel, platform, media, date, *, title=None, desc=None, link=None,
             board=None, yt_type="short", dry_run=False, start=None):
    if platform not in BUILDERS:
        sys.exit(f"unknown platform '{platform}' (choose: {', '.join(BUILDERS)})")
    cfg = load_config(channel, start)
    account_id = resolve_account_id(cfg, platform)        # <-- the guard
    board_id = resolve_board_id(cfg, platform, board)
    if dry_run:
        media_url = "<dry-run: media not uploaded>"
    else:
        media_url = upload_media(cfg, media, MEDIA_MIME[platform])
    body = BUILDERS[platform](
        account_id, media_url, description=desc, title=title, link=link,
        board_id=board_id, schedule_date=date, user_id=cfg["user_id"], yt_type=yt_type)
    if dry_run:
        return {"dryRun": True, "platform": platform, "account_id": account_id, "body": body}
    return create_post(cfg, body)


def main():
    ap = argparse.ArgumentParser(description="Schedule one social post via GHL Social Planner.")
    ap.add_argument("--channel", required=True, help="channel slug (e.g. my-channel)")
    ap.add_argument("--platform", required=True, choices=list(BUILDERS))
    ap.add_argument("--media", required=True, help="local media file (video for TikTok/YT, image for Pinterest)")
    ap.add_argument("--date", required=True, help="ISO 8601 schedule datetime, e.g. 2026-07-26T00:00:00Z")
    ap.add_argument("--desc", required=True, help="caption / description")
    ap.add_argument("--title", help="YouTube/Pinterest title")
    ap.add_argument("--link", help="Pinterest destination URL")
    ap.add_argument("--board", help="Pinterest board name (from the channel allowlist) or board id")
    ap.add_argument("--yt-type", default="short", choices=["short", "video"])
    ap.add_argument("--dry-run", action="store_true", help="resolve + build payload without uploading/posting")
    a = ap.parse_args()
    out = schedule(a.channel, a.platform, a.media, a.date, title=a.title, desc=a.desc,
                   link=a.link, board=a.board, yt_type=a.yt_type, dry_run=a.dry_run)
    print("RESULT " + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
