#!/usr/bin/env python3
"""
Factory music-generation engine — deterministic orchestration, model-agnostic, via OpenRouter.

NO LLM in the loop: this is a mechanical wrapper. It takes a fully-resolved prompt (+ optional
reference image(s)) and a model name, calls the OpenRouter audio API, and saves N candidate
songs for human curation. It performs NO prompt composition and holds NO channel/IP knowledge —
that is the job of the use-case skills that compose ON TOP of this base unit.

Model-agnostic by design: `--model` is a required parameter, never hardcoded. Any OpenRouter
model that emits audio via chat/completions works; swap models with a flag, not a code edit.
(The recommended default lives in the project docs, not here.)

Audio output on OpenRouter requires STREAMING: the response is Server-Sent Events, each SSE
chunk carrying a base64 slice at `choices[0].delta.audio.data`. This engine concatenates those
slices and decodes once to the final audio file.

CLI:
  python .claude/skills/music-gen/generate.py \
      --model google/lyria-3-pro-preview \
      --prompt "tropical chill-out, warm rhodes, gentle waves, 90 BPM, instrumental" \
      --format mp3 \
      --n 2 --out review_dir \
      [--ref mood.png]        # optional reference image(s) -> refs[]
      [--name track]          # output filename stem -> track.mp3 (else the model slug)

Key: OPENROUTER_API_KEY from the environment or the repo-root .env. Never printed. Stdlib only.
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


def build_messages(prompt: str, ref_data_urls) -> list:
    content = [{"type": "text", "text": prompt}]
    for url in ref_data_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})
    return [{"role": "user", "content": content}]


def build_payload(model: str, messages: list, fmt: str) -> dict:
    """Chat-completions body for audio output. Streaming is required for audio on OpenRouter."""
    return {
        "model": model,
        "messages": messages,
        "modalities": ["text", "audio"],
        "audio": {"format": fmt},
        "stream": True,
    }


def slug(s: str) -> str:
    """Filesystem-safe stem: '/' and ':' -> '_'."""
    return s.replace("/", "_").replace(":", "_")


def output_filename(stem: str, seq: int, ext: str) -> str:
    """First song is <stem>.<ext>; extras get a numeric suffix (<stem>_2.<ext>, ...)."""
    return f"{stem}.{ext}" if seq == 1 else f"{stem}_{seq}.{ext}"


def audio_chunk_from_sse_line(line: str):
    """Extract a base64 audio slice from one SSE line, or None.

    SSE lines look like `data: {json}` (and a terminal `data: [DONE]`). Audio slices live at
    choices[0].delta.audio.data. Blank lines, comments, [DONE], and non-audio deltas -> None.
    """
    line = line.strip()
    if not line.startswith("data:"):
        return None
    payload = line[len("data:"):].strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError:
        return None
    try:
        delta = obj["choices"][0].get("delta") or {}
    except (KeyError, IndexError, TypeError):
        return None
    audio = delta.get("audio") if isinstance(delta, dict) else None
    if isinstance(audio, dict):
        data = audio.get("data")
        if isinstance(data, str) and data:
            return data
    return None


def iter_audio_chunks(lines):
    """Yield each base64 audio slice from an iterable of SSE text lines (pure; testable)."""
    for line in lines:
        chunk = audio_chunk_from_sse_line(line)
        if chunk is not None:
            yield chunk


def assemble_audio(chunks) -> bytes:
    """Concatenate the base64 slices and decode once to raw audio bytes."""
    joined = "".join(chunks)
    if not joined:
        return b""
    return base64.b64decode(joined)


# ---- network (NOT unit-tested; injected into generate() as `caller`) ------------

def stream_openrouter(payload: dict, api_key: str, timeout: int = 300) -> list:
    """POST the streaming request and return the list of base64 audio slices (in order)."""
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "HTTP-Referer": "https://factory.local",
            "X-Title": "Factory music generation",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        lines = (raw.decode("utf-8", errors="replace") for raw in r)
        return list(iter_audio_chunks(lines))


# ---- orchestration (testable via injected `caller` / `log`) ---------------------

def generate(model, prompt, refs, n, out, api_key, fmt="mp3",
             caller=stream_openrouter, log=print, name=None) -> dict:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    messages = build_messages(prompt, [file_to_data_url(r) for r in refs])
    stem = slug(name) if name else slug(model)
    saved: list = []
    seq = 0
    for i in range(1, n + 1):
        try:
            chunks = caller(build_payload(model, messages, fmt), api_key)
        except urllib.error.HTTPError as e:
            log(f"[{model}] HTTP {e.code}: {e.read().decode(errors='replace')[:600]}")
            return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved), "error": f"http {e.code}"}
        except Exception as e:  # noqa: BLE001 - surface any transport error as a result, not a crash
            log(f"[{model}] request failed: {e}")
            return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved), "error": str(e)}

        log(f"[{model}] song {i}: received {len(chunks)} audio chunk(s)")
        audio = assemble_audio(chunks)
        if not audio:
            log(f"[{model}] song {i}: no audio returned")
            continue
        seq += 1
        fn = out_dir / output_filename(stem, seq, fmt)
        fn.write_bytes(audio)
        log(f"  saved {fn} ({len(audio)} bytes)")
        saved.append(str(fn))

    return {"model": model, "count": len(saved), "saved": saved, "ok": bool(saved)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic OpenRouter music-gen engine (no LLM).")
    ap.add_argument("--model", required=True, help="OpenRouter model slug, e.g. google/lyria-3-pro-preview")
    ap.add_argument("--prompt", required=True, help="fully-resolved music prompt (style, mood, tempo, lyrics/instrumental)")
    ap.add_argument("--ref", action="append", default=[], help="optional reference image path (repeatable -> refs[])")
    ap.add_argument("--n", type=int, default=1, help="candidate songs to generate")
    ap.add_argument("--out", required=True, help="folder to save into (created if absent)")
    ap.add_argument("--format", default="mp3", choices=["mp3", "wav"], help="output audio format")
    ap.add_argument("--name", default=None, help="output filename stem (e.g. 'track' -> track.mp3); omit to name by model slug")
    args = ap.parse_args(argv)
    result = generate(args.model, args.prompt, args.ref, args.n, args.out, load_api_key(),
                      fmt=args.format, name=args.name)
    print("RESULT " + json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
