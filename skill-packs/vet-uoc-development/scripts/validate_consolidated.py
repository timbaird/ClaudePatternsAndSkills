#!/usr/bin/env python3
"""Validate that a cluster's consolidated_uoc.md references every PC/FS/PE/KE/AC
from each source UoC exactly once.

General, argument-driven version of validate_consolidated_uoc.py (which is
hardcoded to S1-CL2). Parsing logic is identical; the cluster directory, the
source unit files, and the trailing-assessor-AC behaviour are all parameters,
so the same tool validates any cluster.

Usage:
  validate_consolidated.py --cluster <CLUSTER_DIR> \
      --unit ICTCLD504=units_of_competency/ICTCLD504_Complete_R1.md \
      --unit BSBXTW401=units_of_competency/BSBXTW401_Complete_R2.md \
      [--assessor-ac]

  --cluster        path to the cluster dir (contains consolidated_uoc.md)
  --unit CODE=PATH  a source unit: its tag code and its .md path (relative to
                    the cluster dir, or absolute). Repeatable.
  --assessor-ac     count the trailing "Assessors of this unit must satisfy..."
                    paragraph as one extra AC item per unit (CL1/CL2 style).
                    Omit for clusters that do not tag it (CL3 style).

Exit 0 = PASS (every expected item present exactly once, nothing extra).
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


def parse_pcs(md_text: str) -> list[str]:
    """Extract PC numbers (e.g. '1.2') from the Elements and Performance Criteria table."""
    m = re.search(r"# Elements and Performance Criteria\n(.*?)(?=\n# )", md_text, re.DOTALL)
    if not m:
        return []
    section = m.group(1)
    return re.findall(r"\b(\d+\.\d+)\s+", section)


def parse_fs(md_text: str) -> list[str]:
    """Extract Foundation Skill names from the Foundation Skills table."""
    m = re.search(r"# Foundation Skills\n(.*?)(?=\n# )", md_text, re.DOTALL)
    if not m:
        return []
    section = m.group(1)
    names = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"\|\s*(SKILL|Skill)\s*\|", line):
            continue
        if re.match(r"\|\s*-+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and not cells[0].lower().startswith("skill"):
            names.append(cells[0])
    return names


def parse_section_bullets(md_text: str, heading: str) -> int:
    """Count assessable bullets under a heading (PE, KE, AC).

    Counts top-level bullets ('- '). Special case: a single top-level bullet
    ending in ':' is a parent with nested children — count the immediate
    sub-bullets ('  - ') instead.
    """
    pattern = rf"# {re.escape(heading)}\n(.*?)(?=\n# )"
    m = re.search(pattern, md_text, re.DOTALL)
    if not m:
        sections = re.findall(rf"# {re.escape(heading)}\n(.*?)(?=\n# |\Z)", md_text, re.DOTALL)
        if not sections:
            return 0
        section = sections[-1]
    else:
        section = m.group(1)

    lines = section.splitlines()
    top_level = [line for line in lines if re.match(r"^- ", line)]

    if len(top_level) == 1 and top_level[0].rstrip().endswith(":"):
        sub = [line for line in lines if re.match(r"^  - ", line)]
        return len(sub)

    return len(top_level)


def build_inventory(units: list[tuple[str, Path]], assessor_ac: bool) -> set[str]:
    """Build the expected set of reference tags from the source UoCs."""
    expected = set()
    for unit, md_path in units:
        md = md_path.read_text(encoding="utf-8")
        for pc in parse_pcs(md):
            expected.add(f"{unit} PC {pc}")
        for fs in parse_fs(md):
            expected.add(f"{unit} FS {fs}")
        for n in range(1, parse_section_bullets(md, "Performance Evidence") + 1):
            expected.add(f"{unit} PE {n}")
        for n in range(1, parse_section_bullets(md, "Knowledge Evidence") + 1):
            expected.add(f"{unit} KE {n}")
        ac_count = parse_section_bullets(md, "Assessment Conditions")
        if assessor_ac:
            # CL1/CL2 numbered the trailing assessor-requirements paragraph
            # as one extra AC item after the "access to" bullets.
            ac_count += 1
        for n in range(1, ac_count + 1):
            expected.add(f"{unit} AC {n}")
    return expected


def extract_refs(text: str) -> list[tuple[str, str, str]]:
    """Pull every reference tag from the consolidated doc, skipping code spans."""
    cleaned = re.sub(r"`[^`]*`", "", text)
    return re.findall(r"\[(ICT\w+|BSB\w+|VU\d+) (PC|FS|PE|KE|AC) ([^\]]+)\]", cleaned)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster", required=True, type=Path)
    ap.add_argument("--unit", required=True, action="append",
                    help="CODE=relative/or/abs/path.md")
    ap.add_argument("--assessor-ac", action="store_true",
                    help="count trailing assessor-requirements paragraph as an AC item")
    args = ap.parse_args()

    cluster_dir = args.cluster
    units = []
    for spec in args.unit:
        code, _, path = spec.partition("=")
        if not code or not path:
            ap.error(f"--unit must be CODE=PATH, got {spec!r}")
        p = Path(path)
        if not p.is_absolute():
            p = cluster_dir / p
        units.append((code, p))

    consolidated_path = cluster_dir / "consolidated_uoc.md"

    expected = build_inventory(units, args.assessor_ac)
    consolidated = consolidated_path.read_text(encoding="utf-8")
    raw_refs = extract_refs(consolidated)
    found = [f"{u} {s} {n}" for u, s, n in raw_refs]
    counts = Counter(found)

    found_set = set(found)
    missing = sorted(expected - found_set)
    unexpected = sorted(found_set - expected)
    duplicated = sorted([(ref, c) for ref, c in counts.items() if c > 1])

    print(f"Cluster:          {cluster_dir.name}")
    print(f"Units:            {', '.join(u for u, _ in units)}")
    print(f"Assessor-AC mode: {'on' if args.assessor_ac else 'off'}")
    print(f"Expected items:   {len(expected)}")
    print(f"Found references: {len(found)} ({len(found_set)} unique)")
    print()

    if missing:
        print(f"MISSING ({len(missing)}):")
        for ref in missing:
            print(f"  - {ref}")
        print()

    if unexpected:
        print(f"UNEXPECTED ({len(unexpected)}):")
        for ref in unexpected:
            print(f"  - {ref}  (count={counts[ref]})")
        print()

    if duplicated:
        print(f"DUPLICATED ({len(duplicated)}):")
        for ref, c in duplicated:
            print(f"  - {ref}  ({c} times)")
        print()

    if not missing and not unexpected and not duplicated:
        print("RESULT: PASS — every expected item appears exactly once, nothing extra.")
        sys.exit(0)
    else:
        print("RESULT: FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
