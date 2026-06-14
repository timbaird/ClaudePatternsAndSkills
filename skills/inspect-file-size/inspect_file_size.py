#!/usr/bin/env python3
"""Inspect a file (.pptx/.docx/.xlsx or any zip) and report what's driving its size.

A size/bloat check to run BEFORE committing a large file to git: if the file is big,
this shows where the bytes are so you can optimise (compress images, drop an embedded
video, remove dragged-in slide masters) and keep the repo small. It is format-agnostic —
it flags whatever the big objects are, not any one type.

Usage:
    python inspect_file_size.py <path> [--top N] [--warn-mb 25]

Exit code 1 if the file exceeds --warn-mb (handy for a pre-commit gate).
"""
import argparse
import os
import sys
import zipfile
from collections import defaultdict


def human(n):
    return f"{n / 1e6:.2f} MB"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="path to the file (.pptx/.docx/.xlsx or any zip)")
    ap.add_argument("--top", type=int, default=15, help="how many largest entries to list (default 15)")
    ap.add_argument("--warn-mb", type=float, default=25.0, help="warn if the file on disk exceeds this many MB (default 25)")
    args = ap.parse_args()

    if not os.path.isfile(args.path):
        sys.exit(f"Not a file: {args.path}")

    on_disk = os.path.getsize(args.path)
    try:
        z = zipfile.ZipFile(args.path)
    except zipfile.BadZipFile:
        sys.exit(f"Not a zip/Office file: {args.path}")

    infos = z.infolist()
    total = sum(i.file_size for i in infos)
    print(f"On disk (compressed): {human(on_disk)}")
    print(f"Uncompressed total:   {human(total)} across {len(infos)} files\n")

    print(f"--- {args.top} largest internal entries ---")
    for i in sorted(infos, key=lambda i: i.file_size, reverse=True)[: args.top]:
        print(f"{human(i.file_size):>10}  {i.filename}")

    # Group embedded media by type so the culprit category is obvious.
    by_ext = defaultdict(lambda: [0, 0])  # ext -> [count, bytes]
    for i in infos:
        low = i.filename.lower()
        if "/media/" in low or "/embeddings/" in low:
            ext = i.filename.rsplit(".", 1)[-1].lower() if "." in i.filename else "(none)"
            by_ext[ext][0] += 1
            by_ext[ext][1] += i.file_size
    if by_ext:
        print("\n--- embedded media / objects by type ---")
        for ext, (n, s) in sorted(by_ext.items(), key=lambda x: -x[1][1]):
            print(f"{human(s):>10}  {n:4d} x .{ext}")

    big = args.warn_mb * 1e6
    print()
    if on_disk > big:
        print(f"WARNING: file is {human(on_disk)} -- over the {args.warn_mb:.0f} MB guideline.")
        print("   Optimise before committing: e.g. for slides, PowerPoint > Compress Pictures")
        print("   (whole file, 150 ppi, delete cropped areas), or drop the offending object above; then re-run.")
        sys.exit(1)
    print(f"OK: file is {human(on_disk)} -- within the {args.warn_mb:.0f} MB guideline.")


if __name__ == "__main__":
    main()
