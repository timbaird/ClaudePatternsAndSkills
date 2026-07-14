#!/usr/bin/env python3
"""
Deterministic image-generation engine — model-agnostic, via OpenRouter.

NO LLM in the loop: this is a mechanical wrapper. It takes a fully-resolved
prompt + reference image(s) + a model name, calls the OpenRouter image API, and
saves N candidate images for human curation. It performs NO prompt composition
and holds NO domain knowledge — that is the job of the use-case skills that
compose ON TOP of this base unit.

"Deterministic" here means the call-assembly is mechanical: the same arguments
build the same request. The image *output* is of course non-deterministic — that
is the model's doing, not this script's.

CLI:
  python .claude/skills/image-gen/generate.py \
      --model google/gemini-3-pro-image-preview \
      --prompt "flat 2D vector ..." \
      --ref a.png --ref b.png \
      --n 1 --out review_dir \
      [--name hero]          # output filename stem -> hero.png (else the model slug)
      [--modalities image]    # image-only models (FLUX, Seedream) need just 'image'

Key: OPENROUTER_API_KEY from the environment or the repo-root .env (the legacy
OPEN_ROUTER_API_KEY name is tolerated). The key is never printed. Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_NAMES = ("OPENROUTER_API_KEY", "OPEN_ROUTER_API_KEY")  # canonical first; tolerate the variant
DEFAULT_MODALITIES = ("image", "text")  # works for Gemini/GPT; image-only models need ("image",)


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


def decode_data_url(url: str):
    header, _, b64 = url.partition(",")
    return base64.b64decode(b64), ("png" if "png" in header else "jpg")


def build_messages(prompt: str, ref_data_urls) -> list:
    content = [{"type": "text", "text": prompt}]
    for url in ref_data_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})
    return [{"role": "user", "content": content}]


def build_payload(model: str, messages: list, modalities=DEFAULT_MODALITIES) -> dict:
    return {"model": model, "messages": messages, "modalities": list(modalities)}


def slug(s: str) -> str:
    """Filesystem-safe stem: '/' and ':' -> '_'."""
    return s.replace("/", "_").replace(":", "_")


def output_filename(stem: str, seq: int, ext: str) -> str:
    """First image is <stem>.<ext>; extras get a numeric suffix (<stem>_2.<ext>, ...)."""
    return f"{stem}.{ext}" if seq == 1 else f"{stem}_{seq}.{ext}"


def extract_images(resp: dict):
    """Pull (bytes, ext) for each image data-URL in an OpenRouter chat-completion response."""
    out = []
    try:
        msg = resp["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return out
    if not isinstance(msg, dict):
        return out
    for img in (msg.get("images") or []):
        url = (img.get("image_url") or {}).get("url") if isinstance(img, dict) else None
        if isinstance(url, str) and url.startswith("data:"):
            out.append(decode_data_url(url))
    content = msg.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                url = (part.get("image_url") or {}).get("url", "")
                if isinstance(url, str) and url.startswith("data:"):
                    out.append(decode_data_url(url))
    return out


# ---- network (NOT unit-tested; injected into generate() for tests) --------------

def call_openrouter(payload: dict, api_key: str, timeout: int = 180) -> dict:
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://image-gen.local",
            "X-Title": "image-gen (deterministic OpenRouter engine)",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


# ---- orchestration (testable via injected `caller` / `log`) ---------------------

def generate(model, prompt, refs, n, out, api_key, caller=call_openrouter, log=print,
             modalities=DEFAULT_MODALITIES, name=None) -> dict:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    messages = build_messages(prompt, [file_to_data_url(r) for r in refs])
    stem = slug(name) if name else slug(model)
    saved: list = []
    seq = 0
    for i in range(1, n + 1):
        try:
            resp = caller(build_payload(model, messages, modalities), api_key)
        except urllib.error.HTTPError as e:
            log(f"[{model}] HTTP {e.code}: {e.read().decode(errors='replace')[:600]}")
            return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved), "error": f"http {e.code}"}
        except Exception as e:  # noqa: BLE001 - surface any transport error as a result, not a crash
            log(f"[{model}] request failed: {e}")
            return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved), "error": str(e)}

        if i == 1:  # confirm plumbing on the first call: response shape only (no base64, no secrets)
            msg0 = (resp.get("choices") or [{}])[0].get("message", {}) or {}
            log(f"[{model}] response keys={list(resp.keys())} message keys={list(msg0.keys())} usage={resp.get('usage')}")

        imgs = extract_images(resp)
        if not imgs:
            msg = (resp.get("choices") or [{}])[0].get("message", {}) or {}
            note = msg.get("content") if isinstance(msg.get("content"), str) else ""
            log(f"[{model}] candidate {i}: no image returned. note: {str(note)[:300]}")
            continue
        for blob, ext in imgs:
            seq += 1
            fn = out_dir / output_filename(stem, seq, ext)
            fn.write_bytes(blob)
            log(f"  saved {fn} ({len(blob)} bytes)")
            saved.append(str(fn))

    return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic OpenRouter image-gen engine (no LLM).")
    ap.add_argument("--model", required=True, help="OpenRouter model slug, e.g. google/gemini-3-pro-image-preview")
    ap.add_argument("--prompt", required=True, help="fully-resolved generation prompt")
    ap.add_argument("--ref", action="append", default=[], help="reference image path (repeatable -> refs[])")
    ap.add_argument("--n", type=int, default=1, help="candidates to generate")
    ap.add_argument("--out", required=True, help="folder to save into (created if absent)")
    ap.add_argument("--name", default=None,
                    help="output filename stem (e.g. 'hero' -> hero.png); omit to name by model slug")
    ap.add_argument("--modalities", default="image,text",
                    help="comma-separated output modalities; image-only models (FLUX, Seedream) need just 'image'")
    args = ap.parse_args(argv)
    modalities = [m.strip() for m in args.modalities.split(",") if m.strip()]
    result = generate(args.model, args.prompt, args.ref, args.n, args.out, load_api_key(),
                      modalities=modalities, name=args.name)
    print("RESULT " + json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
