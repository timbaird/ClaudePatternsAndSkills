"""Deterministic YouTube-thumbnail compositor (Pillow) — one hero/scene image + title → a 1280×720 JPEG.

Two house-template LAYOUTS, chosen with `--layout`:

  band     A fixed translucent title BAND across the bottom + an auto-fit, auto-contrast title, a soft
           shade rising into the band, and an optional corner WORDMARK. The band colour is a parameter
           (e.g. a per-item signature colour); the title auto-contrasts (dark on a light band, white on
           a dark one). `--variants N` sweeps the crop for a human to pick the framing.

  caption  A shadowed title (+ optional subtitle) set bottom-left, over an optional dark bottom SCRIM
           for bright scenes where light text would wash out.

Both cover-fit + centre-crop the source to the frame (no distortion). Brand is DATA, not code: colours,
font, wordmark, and sizes are all parameters — nothing here is tied to a specific channel. No LLM, no
network — same args build the same image.
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("ERROR: Pillow is required for the thumbnail skill (see SKILL.md to set up the venv).")

W, H = 1280, 720                 # YouTube thumbnail spec (16:9)
INK = (56, 66, 92)               # default dark text/contrast colour (override with --ink)
BAND = (255, 200, 70)            # default band colour — a placeholder; override with --band-color
CAPTION = (239, 227, 207)        # default caption colour (cream); override with --caption-color
BAND_H = 150
BAND_ALPHA = 0.78


# ── helpers (unit-tested) ────────────────────────────────────────────────────
def parse_rgb(s, default):
    """'R,G,B' → (r,g,b); None/'' → default."""
    if not s:
        return tuple(default)
    return tuple(int(x) for x in str(s).split(","))


def _font(path, size, weight=800):
    """A truetype font at `size` if `path` is given and loads; otherwise Pillow's built-in font.
    Making the font optional keeps the skill usable out-of-box (and testable without an asset)."""
    if path:
        try:
            f = ImageFont.truetype(str(path), size)
            try:
                f.set_variation_by_axes([weight])   # variable fonts only; harmless otherwise
            except Exception:
                pass
            return f
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)     # Pillow ≥10.1 supports a size
    except TypeError:
        return ImageFont.load_default()


def _fit_font(draw, text, font_path, max_w, start, weight=800, floor=40):
    """Largest font size (≤ start) at which `text` fits `max_w`."""
    size = start
    while size > floor:
        f = _font(font_path, size, weight)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return _font(font_path, floor, weight)


def cover_fit(im, w, h, focus_y=0.5):
    """Scale to fill w×h and centre-crop (focus_y biases the vertical crop: 0=top, 1=bottom)."""
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = round((im.height - h) * focus_y)
    return im.crop((x, y, x + w, y + h))


def _ctext(draw, text, font, cx, y, fill, stroke=0, stroke_fill=(255, 255, 255)):
    tw = draw.textlength(text, font=font)
    draw.text((cx - tw / 2, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def _shadowed(draw, xy, text, font, sh, fill):
    x, y = xy
    draw.text((x + sh, y + sh), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


# ── layouts ──────────────────────────────────────────────────────────────────
def _layout_band(im, title, font, w, h, band_color, band_alpha, band_h, ink, wordmark):
    d = ImageDraw.Draw(im, "RGBA")
    # soft shade rising into the band so the art never fights the title
    for i in range(110):
        a = int(105 * (i / 110))
        d.line([(0, h - band_h - 110 + i), (w, h - band_h - 110 + i)], fill=(40, 46, 70, a))
    # the fixed title band — translucent, so the art shows through
    d.rectangle((0, h - band_h, w, h), fill=tuple(band_color) + (int(255 * band_alpha),))
    # title — auto-fit to the band; auto-contrast so it reads on any band colour
    tf = _fit_font(d, title, font, w - 110, start=int(band_h * 0.74))
    asc, desc = tf.getmetrics()
    ty = h - band_h + (band_h - (asc + desc)) // 2
    lum = 0.299 * band_color[0] + 0.587 * band_color[1] + 0.114 * band_color[2]
    fill, outline = (ink, (255, 255, 255)) if lum >= 140 else ((255, 255, 255), ink)
    _ctext(d, title, tf, w // 2, ty, fill, stroke=6, stroke_fill=outline)
    # optional fixed corner wordmark — the recognisability anchor
    if wordmark:
        wf = _font(font, 40, 700)
        pad = 18
        ww = d.textlength(wordmark, font=wf)
        d.rounded_rectangle((24, 24, 24 + ww + pad * 2, 24 + 56), radius=14, fill=(255, 255, 255, 235))
        d.text((24 + pad, 24 + 6), wordmark, font=wf, fill=ink)


def _layout_caption(im, title, subtitle, font, w, h, caption_color, scrim, title_size, subtitle_size):
    if scrim:
        mask = Image.new("L", (w, h), 0)
        sd = ImageDraw.Draw(mask)
        start = int(h * 0.65)
        for y in range(start, h):
            sd.line([(0, y), (w, y)], fill=int((y - start) / (h - start) * 150))
        im.paste(Image.new("RGB", im.size, (0, 0, 0)), (0, 0), mask)
    d = ImageDraw.Draw(im)
    y_title = int(h * 0.75)
    _shadowed(d, (52, y_title), title, _font(font, title_size), 3, caption_color)
    if subtitle:
        _shadowed(d, (55, y_title + title_size + 18), subtitle, _font(font, subtitle_size), 2, caption_color)


def build(image, title, out, layout="band", font=None, w=W, h=H, focus_y=0.5,
          band_color=BAND, band_alpha=BAND_ALPHA, band_h=BAND_H, ink=INK, wordmark="",
          subtitle="", scrim=False, title_size=78, subtitle_size=33, caption_color=CAPTION):
    """Compose one thumbnail and save it (JPEG). Returns the output Path."""
    im = cover_fit(Image.open(image).convert("RGB"), w, h, focus_y)
    if layout == "caption":
        _layout_caption(im, title, subtitle, font, w, h, tuple(caption_color), scrim, title_size, subtitle_size)
    else:
        _layout_band(im, title, font, w, h, tuple(band_color), band_alpha, band_h, tuple(ink), wordmark)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "JPEG", quality=90)
    return Path(out)


def candidates(image, title, out_dir, n=5, lo=0.30, hi=0.78, **kw):
    """Render n candidates differing only by the crop (focus_y) — the template is fixed; a human picks
    the framing. Returns the candidate paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        fy = lo if n == 1 else round(lo + (hi - lo) * i / (n - 1), 2)
        p = out_dir / f"thumb-{i + 1:02d}-crop{fy:.2f}.jpg"
        build(image, title, p, focus_y=fy, **kw)
        paths.append(p)
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compose a 1280×720 YouTube thumbnail (band or caption layout).")
    ap.add_argument("--image", "--hero", "--scene", dest="image", required=True,
                    help="source hero/scene image (cover-fit + centre-cropped to the frame)")
    ap.add_argument("--title", required=True, help="thumbnail title text")
    ap.add_argument("--out", required=True, help="output .jpg (or a dir, with --variants)")
    ap.add_argument("--layout", choices=["band", "caption"], default="band", help="template layout")
    ap.add_argument("--font", default=None, help="TrueType font path (omit → Pillow's built-in font)")
    ap.add_argument("--width", type=int, default=W, dest="w")
    ap.add_argument("--height", type=int, default=H, dest="h")
    ap.add_argument("--focus-y", type=float, default=0.5, dest="focus_y",
                    help="vertical crop bias 0=top..1=bottom (lower favours faces near the top)")
    # band layout
    ap.add_argument("--band-color", dest="band_color", default=None, help="band colour R,G,B (band layout)")
    ap.add_argument("--band-alpha", type=float, default=BAND_ALPHA, dest="band_alpha")
    ap.add_argument("--band-h", type=int, default=BAND_H, dest="band_h", help="band height in px")
    ap.add_argument("--ink", default=None, help="dark text/contrast colour R,G,B (band layout)")
    ap.add_argument("--wordmark", default="", help="fixed corner wordmark (band layout; omit → none)")
    # caption layout
    ap.add_argument("--subtitle", default="", help="small line under the title (caption layout)")
    ap.add_argument("--scrim", action="store_true", help="dark bottom scrim for bright scenes (caption layout)")
    ap.add_argument("--title-size", type=int, default=78, dest="title_size")
    ap.add_argument("--subtitle-size", type=int, default=33, dest="subtitle_size")
    ap.add_argument("--caption-color", dest="caption_color", default=None, help="caption text colour R,G,B")
    ap.add_argument("--variants", type=int, default=1,
                    help="render N crop candidates into --out (as a dir) for a human to pick (band layout)")
    a = ap.parse_args(argv)

    style = dict(
        layout=a.layout, font=a.font, w=a.w, h=a.h,
        band_color=parse_rgb(a.band_color, BAND), band_alpha=a.band_alpha, band_h=a.band_h,
        ink=parse_rgb(a.ink, INK), wordmark=a.wordmark,
        subtitle=a.subtitle, scrim=a.scrim, title_size=a.title_size, subtitle_size=a.subtitle_size,
        caption_color=parse_rgb(a.caption_color, CAPTION),
    )
    if a.variants > 1:
        paths = candidates(a.image, a.title, a.out, n=a.variants, **style)   # candidates sweeps focus_y
        print(f"RESULT {len(paths)} thumbnail candidates -> {a.out} (pick one)")
        for p in paths:
            print(f"  {p.name}")
    else:
        out = build(a.image, a.title, a.out, focus_y=a.focus_y, **style)
        im = Image.open(out)
        print(f"RESULT saved {out} ({im.width}x{im.height}, {out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
