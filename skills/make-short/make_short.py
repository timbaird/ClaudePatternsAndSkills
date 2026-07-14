#!/usr/bin/env python3
"""make-short — deterministic 9:16 vertical short from a 16:9 loop clip + one audio track + a text hook.

Reframes a 16:9 clip into 1080×1920 (blurred-fill: the scene in a centre band, a blurred enlarged copy
filling top/bottom), overlays a top hook line and a bottom CTA/handle in the blurred bands (so the scene
stays clear), loops the visual to length, and lays a fade-in/out snippet of one track. For YouTube
Shorts / Reels / TikTok. No LLM in the loop — same args build the same short.

Needs ffmpeg: uses the system `ffmpeg` on PATH, falling back to the bundled `imageio-ffmpeg` binary.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("make-short needs Pillow. Set up the per-skill venv (see SKILL.md) and invoke with it.")

DEFAULT_TEXT = (239, 227, 207)   # default overlay text colour (cream); override with --text-color
W, H = 1080, 1920                # 9:16 vertical


def find_ffmpeg():
    """Resolve an ffmpeg binary: system PATH first, then the bundled imageio-ffmpeg, else None."""
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


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


def render_overlay(hook, cta, handle, path, font=None, text_color=DEFAULT_TEXT):
    """Author the transparent 1080×1920 overlay: hook in the top band, CTA + handle in the bottom band.
    Plain text only (this ffmpeg/font renders emoji as tofu — put emoji in the platform caption)."""
    text_color = tuple(text_color)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f_hook = _font(font, 66)
    f_cta = _font(font, 52)
    f_handle = _font(font, 56)

    def centered(text, fnt, y):
        for line in textwrap.wrap(text, width=20):
            w = d.textbbox((0, 0), line, font=fnt)[2]
            x = (W - w) // 2
            d.text((x + 3, y + 3), line, font=fnt, fill=(0, 0, 0, 200))
            d.text((x, y), line, font=fnt, fill=text_color + (255,))
            y += (getattr(fnt, "size", 56)) + 14
        return y

    if hook:
        centered(hook, f_hook, 210)          # top blurred band
    y = centered(cta, f_cta, 1560) if cta else 1560   # bottom blurred band
    if handle:
        centered(handle, f_handle, y + 6)
    img.save(path)


def build_short(loop, audio, out, hook, cta="", handle="", font=None, text_color=DEFAULT_TEXT,
                duration=70.0, audio_start=20.0, ffmpeg=None, run=subprocess.run):
    """Render the short. `run` is injected for testing. Returns the output path."""
    ffmpeg = ffmpeg or find_ffmpeg()
    if not ffmpeg:
        sys.exit("ERROR: ffmpeg not found. Install it (e.g. `brew install ffmpeg`) or "
                 "`pip install imageio-ffmpeg` into this skill's venv.")
    tmp = tempfile.mkdtemp(prefix="short_")
    overlay = os.path.join(tmp, "overlay.png")
    render_overlay(hook, cta, handle, overlay, font=font, text_color=text_color)

    fade_out = max(0.0, duration - 2.0)
    fc = (
        "[0:v]split=2[a][b];"
        f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:2[bg];"
        f"[b]scale={W}:-2[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
        "[base][2:v]overlay=0:0,format=yuv420p[v]"
    )
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-stream_loop", "-1", "-i", loop,
        "-ss", str(audio_start), "-t", str(duration), "-i", audio,
        "-i", overlay,
        "-filter_complex", fc,
        "-map", "[v]", "-map", "1:a",
        "-t", str(duration),
        "-af", f"afade=t=in:st=0:d=1,afade=t=out:st={fade_out}:d=2",
        "-r", "24", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        out,
    ]
    run(cmd, check=True)
    return out


def parse_rgb(s, default):
    return tuple(int(x) for x in str(s).split(",")) if s else tuple(default)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic 9:16 vertical short from a 16:9 loop + audio + hook.")
    ap.add_argument("--loop", required=True, help="16:9 loop clip to reframe")
    ap.add_argument("--audio", required=True, help="track to snippet")
    ap.add_argument("--hook", required=True, help="top hook line (plain text, no emoji)")
    ap.add_argument("--out", required=True, help="output .mp4 (1080×1920)")
    ap.add_argument("--cta", default="", help="bottom call-to-action (omit → none)")
    ap.add_argument("--handle", default="", help="handle under the CTA (omit → none)")
    ap.add_argument("--font", default=None, help="TrueType font path (omit → Pillow's built-in font)")
    ap.add_argument("--text-color", dest="text_color", default=None, help="overlay text colour R,G,B")
    ap.add_argument("--duration", type=float, default=70.0,
                    help="seconds (default 70; >60 keeps shorts eligible for TikTok Creator Rewards)")
    ap.add_argument("--audio-start", type=float, default=20.0, dest="audio_start",
                    help="seconds into the track to start the snippet")
    a = ap.parse_args(argv)
    out = build_short(a.loop, a.audio, a.out, a.hook, cta=a.cta, handle=a.handle, font=a.font,
                      text_color=parse_rgb(a.text_color, DEFAULT_TEXT),
                      duration=a.duration, audio_start=a.audio_start)
    print(f"RESULT saved {out} (1080x1920, {a.duration:.0f}s)")


if __name__ == "__main__":
    main()
