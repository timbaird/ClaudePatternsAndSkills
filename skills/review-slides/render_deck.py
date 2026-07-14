#!/usr/bin/env python3
"""render_deck — render a .pptx (or .pdf) deck to one PNG per slide for visual review.

Pipeline: LibreOffice (`soffice --headless`) converts the deck to PDF, then PyMuPDF rasterises each
page to a PNG at the requested DPI, into a review folder. Deterministic, offline, headless — same deck
→ same images. Re-runnable: point it at a rebuilt deck and it refreshes the PNGs.

Dependencies:
  - LibreOffice — a SYSTEM app, not a pip package (macOS: `brew install --cask libreoffice`). Detected on
    PATH (`soffice`/`libreoffice`) or at the standard macOS app path.
  - PyMuPDF — the venv dependency (see requirements.txt); import-guarded below.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAC_SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def find_soffice():
    for c in ("soffice", "libreoffice"):
        p = shutil.which(c)
        if p:
            return p
    return MAC_SOFFICE if Path(MAC_SOFFICE).exists() else None


def main():
    ap = argparse.ArgumentParser(description="Render a .pptx/.pdf deck to one PNG per slide.")
    ap.add_argument("--deck", required=True, help="path to the .pptx (or .pdf) deck")
    ap.add_argument("--out", required=True, help="folder to write slide-NNN.png into (created if absent)")
    ap.add_argument("--dpi", type=int, default=110, help="render resolution (default 110)")
    args = ap.parse_args()

    deck = Path(args.deck).resolve()
    if not deck.exists():
        print(f"ERROR: deck not found: {deck}")
        return 2
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    try:
        import fitz  # PyMuPDF
    except ImportError:
        skill = Path(__file__).resolve().parent
        print("ERROR: PyMuPDF missing. One-time setup (from the repo root):\n"
              f"  python3 -m venv {skill}/.venv\n"
              f"  {skill}/.venv/bin/python -m pip install -r {skill}/requirements.txt\n"
              "then invoke render_deck.py with that venv's python.")
        return 3

    # 1) get a PDF (LibreOffice converts .pptx; a .pdf is used directly)
    tmp = None
    if deck.suffix.lower() == ".pdf":
        pdf = deck
    else:
        soffice = find_soffice()
        if not soffice:
            print("ERROR: LibreOffice not found. Install it (macOS):\n"
                  "  brew install --cask libreoffice\n"
                  "or put `soffice` on PATH. It renders the .pptx exactly as PowerPoint would.")
            return 4
        tmp = Path(tempfile.mkdtemp(prefix="review_slides_"))
        # a private profile dir lets soffice run headless + repeatably (no 'already running' lock)
        cmd = [soffice, "--headless", "--norestore",
               f"-env:UserInstallation=file://{tmp / 'lo_profile'}",
               "--convert-to", "pdf", "--outdir", str(tmp), str(deck)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            print("ERROR: LibreOffice conversion timed out (240s).")
            return 5
        pdf = tmp / (deck.stem + ".pdf")
        if not pdf.exists():
            print(f"ERROR: LibreOffice did not produce a PDF.\nSTDOUT:{res.stdout}\nSTDERR:{res.stderr}")
            return 5

    # 2) rasterise each page to a PNG
    doc = fitz.open(str(pdf))
    mat = fitz.Matrix(args.dpi / 72.0, args.dpi / 72.0)
    n = 0
    for i, page in enumerate(doc, 1):
        page.get_pixmap(matrix=mat).save(str(out / f"slide-{i:03d}.png"))
        n = i
    doc.close()
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f'RESULT {{"deck": "{deck.name}", "slides": {n}, "out": "{out}", "ok": true}}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
