#!/usr/bin/env python3
"""
Factory video-generation engine — deterministic orchestration, model-agnostic, via OpenRouter.

NO LLM in the loop: this is a mechanical wrapper. It takes a fully-resolved prompt, an optional
start/end frame image, and a model name, calls OpenRouter's async video API, waits for the job,
and downloads the finished MP4(s). It performs NO prompt composition and holds NO channel/IP
knowledge — that is the job of the use-case skills that compose ON TOP of this base unit.

Model-agnostic by design: `--model` is a required parameter, never hardcoded. Any OpenRouter
video model works; swap models with a flag, not a code edit. (The recommended default lives in
the project docs, not here.)

Video generation on OpenRouter is ASYNC — submit -> poll -> download:
  1. POST /api/v1/videos            -> { id, polling_url, status: "pending" }
  2. GET  <polling_url> (every ~30s) until status == "completed"
     (terminal failures: "failed" | "cancelled" | "expired" -> surface the `error` field)
  3. GET  unsigned_urls[0] (with auth) -> MP4 bytes

Seamless-loop trick: pass the SAME image as both first_frame and last_frame (`--frame X --loop`)
so the clip ends exactly where it began and can be repeated without a visible seam.

CLI:
  python .claude/skills/video-gen/generate.py \
      --model kwaivgi/kling-v3.0-std \
      --prompt "slow drift over a moonlit tropical beach, gentle waves" \
      --frame scene.png --loop \
      --duration 5 --aspect-ratio 16:9 \
      --n 2 --out review_dir \
      [--last-frame end.png]   # explicit end frame (instead of --loop)
      [--name clip]            # output stem -> clip.mp4 (else the model slug)

Key: OPENROUTER_API_KEY from the environment or the repo-root .env. Never printed. Stdlib only.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SUBMIT_URL = "https://openrouter.ai/api/v1/videos"
KEY_NAMES = ("OPENROUTER_API_KEY", "OPEN_ROUTER_API_KEY")  # canonical first; tolerate the variant
DONE = "completed"
TERMINAL_FAILS = ("failed", "cancelled", "expired")


# ---- pure helpers (unit-tested) -------------------------------------------------

def parse_env_file(text: str) -> dict:
    """Parse KEY=VALUE lines; strip surrounding quotes and whitespace; skip blanks/comments."""
    kv: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        kv[k.strip()] = v.strip().strip('"').strip("'")
    return kv


def pick_api_key(sources: dict):
    """Return (name, value) for the first non-empty known key name, else (None, None)."""
    for name in KEY_NAMES:
        v = sources.get(name)
        if v and v.strip():
            return name, v.strip()
    return None, None


def repo_root() -> Path:
    """Walk up from this file to the repo root (the dir containing .git)."""
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / ".git").exists():
            return parent
    return here.parents[-1]


def load_api_key() -> str:
    name, key = pick_api_key(dict(os.environ))
    if not key:
        env_path = repo_root() / ".env"
        if env_path.exists():
            name, key = pick_api_key(parse_env_file(env_path.read_text()))
    if not key:
        sys.exit("ERROR: OPENROUTER_API_KEY not found (env or repo-root .env).")
    if name != KEY_NAMES[0]:
        print(f"NOTE: using {name}; consider renaming to {KEY_NAMES[0]}")
    return key


def file_to_data_url(path) -> str:
    p = Path(path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def _frame(url: str, frame_type: str) -> dict:
    return {"type": "image_url", "image_url": {"url": url}, "frame_type": frame_type}


def build_frame_images(first_url=None, last_url=None, loop=False) -> list:
    """Assemble the frame_images array.

    - loop=True with a first_url -> same image as first_frame AND last_frame (seamless loop).
    - otherwise -> a first_frame (if given) and/or a last_frame (if given).
    """
    frames: list = []
    if first_url:
        frames.append(_frame(first_url, "first_frame"))
    if loop and first_url:
        frames.append(_frame(first_url, "last_frame"))
    elif last_url:
        frames.append(_frame(last_url, "last_frame"))
    return frames


def build_submit_payload(model, prompt, frame_images=None, duration=None,
                         resolution=None, aspect_ratio=None, size=None) -> dict:
    """Submit body; only include fields that were supplied (out-of-set values 400 upstream)."""
    payload = {"model": model, "prompt": prompt}
    if frame_images:
        payload["frame_images"] = frame_images
    if duration is not None:
        payload["duration"] = duration
    if resolution:
        payload["resolution"] = resolution
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if size:
        payload["size"] = size
    return payload


def slug(s: str) -> str:
    """Filesystem-safe stem: '/' and ':' -> '_'."""
    return s.replace("/", "_").replace(":", "_")


def output_filename(stem: str, seq: int, ext: str = "mp4") -> str:
    """First clip is <stem>.<ext>; extras get a numeric suffix (<stem>_2.<ext>, ...)."""
    return f"{stem}.{ext}" if seq == 1 else f"{stem}_{seq}.{ext}"


def job_status(resp: dict) -> str:
    return (resp or {}).get("status", "")


def download_url(resp: dict):
    """The first downloadable video URL from a completed poll response, or None."""
    urls = (resp or {}).get("unsigned_urls")
    if isinstance(urls, list) and urls:
        return urls[0]
    return None


# ---- network (NOT unit-tested; injected into generate()) ------------------------

def _get_json(url: str, api_key: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def submit_video(payload: dict, api_key: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        SUBMIT_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://factory.local",
            "X-Title": "Factory video generation",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def poll_video(polling_url: str, api_key: str, timeout: int = 60) -> dict:
    return _get_json(polling_url, api_key, timeout)


def download_bytes(url: str, api_key: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---- orchestration (testable via injected network fns + sleep) ------------------

def run_one(payload, api_key, out_path, submit, poll, download, sleep, log,
            interval=30, max_wait=600) -> dict:
    """Submit one job, poll to completion, download the MP4. Returns a per-clip result dict."""
    sub = submit(payload, api_key)
    job_id = sub.get("id")
    polling_url = sub.get("polling_url")
    log(f"[{payload['model']}] submitted job {job_id} (status {sub.get('status')})")
    if not polling_url:
        return {"ok": False, "error": f"no polling_url in submit response: {str(sub)[:300]}"}

    polls = max(1, math.ceil(max_wait / interval))
    for _ in range(polls):
        sleep(interval)
        resp = poll(polling_url, api_key)
        st = job_status(resp)
        log(f"[{payload['model']}] job {job_id}: {st}")
        if st == DONE:
            url = download_url(resp)
            if not url:
                return {"ok": False, "error": "completed but no unsigned_urls to download"}
            out_path.write_bytes(download(url, api_key))
            return {"ok": True, "path": str(out_path)}
        if st in TERMINAL_FAILS:
            return {"ok": False, "error": f"{st}: {resp.get('error', 'unknown')}"}
    return {"ok": False, "error": f"timed out after ~{max_wait}s still not {DONE}"}


def generate(model, prompt, n, out, api_key, frame_images=None, duration=None, resolution=None,
             aspect_ratio=None, size=None, name=None,
             submit=submit_video, poll=poll_video, download=download_bytes, sleep=time.sleep,
             log=print, interval=30, max_wait=600) -> dict:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_submit_payload(model, prompt, frame_images, duration, resolution, aspect_ratio, size)
    stem = slug(name) if name else slug(model)
    saved: list = []
    for i in range(1, n + 1):
        fn = out_dir / output_filename(stem, i)
        try:
            res = run_one(payload, api_key, fn, submit, poll, download, sleep, log, interval, max_wait)
        except urllib.error.HTTPError as e:
            log(f"[{model}] HTTP {e.code}: {e.read().decode(errors='replace')[:600]}")
            return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved), "error": f"http {e.code}"}
        except Exception as e:  # noqa: BLE001 - surface any transport error as a result, not a crash
            log(f"[{model}] request failed: {e}")
            return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved), "error": str(e)}
        if res["ok"]:
            log(f"  saved {res['path']}")
            saved.append(res["path"])
        else:
            log(f"[{model}] clip {i} failed: {res['error']}")
            return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved), "error": res["error"]}
    return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic OpenRouter video-gen engine (no LLM).")
    ap.add_argument("--model", required=True, help="OpenRouter video model slug, e.g. kwaivgi/kling-v3.0-std")
    ap.add_argument("--prompt", required=True, help="fully-resolved video/motion prompt")
    ap.add_argument("--frame", default=None, help="start-frame image path (image-to-video)")
    ap.add_argument("--last-frame", dest="last_frame", default=None, help="explicit end-frame image path")
    ap.add_argument("--loop", action="store_true", help="use the start frame as BOTH first and last frame (seamless loop)")
    ap.add_argument("--duration", type=int, default=None, help="clip duration (must be one of the model's supported_durations)")
    ap.add_argument("--resolution", default=None, help="e.g. 720p (model-specific)")
    ap.add_argument("--aspect-ratio", dest="aspect_ratio", default=None, help="e.g. 16:9 (model-specific)")
    ap.add_argument("--size", default=None, help="e.g. 1280x720 (interchangeable with resolution+aspect_ratio)")
    ap.add_argument("--n", type=int, default=1, help="clips to generate (one job each)")
    ap.add_argument("--out", required=True, help="folder to save into (created if absent)")
    ap.add_argument("--name", default=None, help="output filename stem (e.g. 'clip' -> clip.mp4); omit to name by model slug")
    ap.add_argument("--poll-interval", dest="interval", type=int, default=30, help="seconds between status polls")
    ap.add_argument("--max-wait", dest="max_wait", type=int, default=600, help="give up after this many seconds per clip")
    args = ap.parse_args(argv)

    first_url = file_to_data_url(args.frame) if args.frame else None
    last_url = file_to_data_url(args.last_frame) if args.last_frame else None
    frames = build_frame_images(first_url, last_url, args.loop)

    result = generate(args.model, args.prompt, args.n, args.out, load_api_key(),
                      frame_images=frames, duration=args.duration, resolution=args.resolution,
                      aspect_ratio=args.aspect_ratio, size=args.size, name=args.name,
                      interval=args.interval, max_wait=args.max_wait)
    print("RESULT " + json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
