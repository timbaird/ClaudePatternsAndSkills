#!/usr/bin/env python3
"""make-pins — deterministic 2:3 (1000×1500) Pinterest pin from a scene image + a headline.

Blurred-fill layout: the scene sits in a centre band, a blurred enlarged copy fills top/bottom, a
headline goes up top and an optional CTA + handle at the bottom. Plain text only (no emoji — a rounded
font renders them as tofu; put emoji in the pin's typed description). The pin's destination LINK is set
when you post it, not baked into the image. Brand is data (text colour, font, CTA, handle are params).
Pure Pillow — no LLM, no network; same args build the same pin.
"""
import argparse
import sys
import textwrap

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("make-pins needs Pillow. Set up the per-skill venv (see SKILL.md) and invoke with it.")

CREAM = (239, 227, 207)   # default text colour; override with --text-color


def parse_rgb(s, default):
    return tuple(int(x) for x in str(s).split(",")) if s else tuple(default)


def _font(path, size):
    if path:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def draw_wrapped(d, text, font, cx, y, fill, width_chars, line_gap=14):
    for line in textwrap.wrap(text, width=width_chars):
        w = d.textbbox((0, 0), line, font=font)[2]
        x = cx - w // 2
        d.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0))
        d.text((x, y), line, font=font, fill=fill)
        y += getattr(font, "size", 50) + line_gap
    return y


def build_pin(scene, title, out, cta="", handle="", font=None, text_color=CREAM, w=1000, h=1500):
    """Compose the pin and save it (JPEG). Returns the output path."""
    text_color = tuple(text_color)
    src = Image.open(scene).convert("RGB")
    # blurred cover background filling the whole 2:3 frame
    bg = src.resize((w, round(w * src.height / src.width)), Image.LANCZOS)
    if bg.height < h:
        bg = src.resize((round(h * src.width / src.height), h), Image.LANCZOS)
    left, top = (bg.width - w) // 2, (bg.height - h) // 2
    bg = bg.crop((left, top, left + w, top + h)).filter(ImageFilter.GaussianBlur(28))
    # the sharp scene band, centred
    band = src.resize((w, round(w * src.height / src.width)), Image.LANCZOS)
    bg.paste(band, (0, (h - band.height) // 2))

    d = ImageDraw.Draw(bg)
    band_top = (h - band.height) // 2
    draw_wrapped(d, title, _font(font, 62), w // 2, int(band_top * 0.28), text_color, 16)
    y = band_top + band.height + int((h - (band_top + band.height)) * 0.28)
    if cta:
        y = draw_wrapped(d, cta, _font(font, 44), w // 2, y, text_color, 22)
    if handle:
        draw_wrapped(d, handle, _font(font, 50), w // 2, y + 8, text_color, 22)

    bg.save(out, "JPEG", quality=90)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic 2:3 (1000×1500) Pinterest pin from a scene + headline.")
    ap.add_argument("--scene", required=True, help="source scene image")
    ap.add_argument("--title", required=True, help="headline (plain text, no emoji)")
    ap.add_argument("--out", required=True, help="output .jpg (2:3)")
    ap.add_argument("--cta", default="", help="bottom call-to-action (omit → none)")
    ap.add_argument("--handle", default="", help="brand line under the CTA (omit → none)")
    ap.add_argument("--font", default=None, help="TrueType font path (omit → Pillow's built-in font)")
    ap.add_argument("--text-color", dest="text_color", default=None, help="text colour R,G,B")
    ap.add_argument("--width", type=int, default=1000)
    ap.add_argument("--height", type=int, default=1500)
    a = ap.parse_args(argv)
    out = build_pin(a.scene, a.title, a.out, cta=a.cta, handle=a.handle, font=a.font,
                    text_color=parse_rgb(a.text_color, CREAM), w=a.width, h=a.height)
    print(f"RESULT saved {out} ({a.width}x{a.height})")


if __name__ == "__main__":
    main()
