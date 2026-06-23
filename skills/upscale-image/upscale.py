#!/usr/bin/env python3
"""upscale — deterministic Pillow image upscaler to an exact print-resolution size.

Take a source image and produce a print-resolution copy at an EXACT target size (e.g. 5175x2625 at
300 DPI for an 8.5x8.5 full-bleed spread). Deterministic: Lanczos resampling + cover-fit centre-crop
— same input + params -> same output pixels. No model, no network, no API key.

    python .claude/skills/upscale-image/upscale.py <input> --out <dir> --width 5175 --height 2625 [--dpi 300] [--name page-01]

Saves <name>.png (lossless) into <out>, stamped at the given DPI. Prints a RESULT json line.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit(
        "ERROR: Pillow is required for the upscale skill but is not installed.\n"
        "Set up the skill's virtualenv (see .claude/skills/upscale-image/SKILL.md), then run via that python:\n"
        "  python -m venv .claude/skills/upscale-image/.venv\n"
        "  .claude/skills/upscale-image/.venv/Scripts/python -m pip install -r .claude/skills/upscale-image/requirements.txt   (Windows)\n"
        "  .claude/skills/upscale-image/.venv/bin/python   -m pip install -r .claude/skills/upscale-image/requirements.txt   (macOS/Linux)"
    )

RESAMPLE = Image.LANCZOS


# --- pure helpers (unit-tested, no image I/O) --------------------------------
def cover_scale(sw: int, sh: int, tw: int, th: int) -> float:
    """Scale factor so a (sw x sh) image fully COVERS a (tw x th) box (overflow is cropped)."""
    return max(tw / sw, th / sh)


def scaled_dims(sw: int, sh: int, scale: float):
    return (round(sw * scale), round(sh * scale))


def center_crop_box(w: int, h: int, tw: int, th: int):
    """Box (left, top, right, bottom) that centre-crops a (w x h) image to (tw x th)."""
    left = (w - tw) // 2
    top = (h - th) // 2
    return (left, top, left + tw, top + th)


# --- the op (Pillow) ---------------------------------------------------------
def upscale_image(in_path, out_path, tw: int, th: int, dpi: int = 300, resample=RESAMPLE) -> dict:
    """Resize (Lanczos) to cover the target, centre-crop to exact (tw x th), save PNG at `dpi`."""
    img = Image.open(in_path).convert("RGB")
    sw, sh = img.size
    scale = cover_scale(sw, sh, tw, th)
    img = img.resize(scaled_dims(sw, sh, scale), resample)
    img = img.crop(center_crop_box(img.width, img.height, tw, th))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", dpi=(dpi, dpi))
    return {"input": str(in_path), "in_size": [sw, sh], "out_size": [tw, th],
            "scale": round(scale, 3), "dpi": dpi, "saved": str(out_path), "ok": True}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic Pillow upscaler (Lanczos, cover-fit).")
    ap.add_argument("input", help="path to the source image")
    ap.add_argument("--out", required=True, help="output folder (created if absent)")
    ap.add_argument("--width", type=int, required=True, help="target width px")
    ap.add_argument("--height", type=int, required=True, help="target height px")
    ap.add_argument("--dpi", type=int, default=300, help="DPI metadata to stamp (default 300)")
    ap.add_argument("--name", default=None, help="output filename stem (default: the input's stem)")
    args = ap.parse_args(argv)

    p = Path(args.input)
    if not p.is_file():
        sys.exit(f"ERROR: not a file: {p}")
    stem = args.name or p.stem
    out = Path(args.out) / f"{stem}.png"
    result = upscale_image(p, out, args.width, args.height, args.dpi)
    print("RESULT " + json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
