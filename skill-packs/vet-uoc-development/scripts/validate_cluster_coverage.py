#!/usr/bin/env python3
"""Cluster coverage — do a cluster's assessment tasks, taken together, evidence EVERY item in its
consolidated UoC? This is the capstone check: the per-AT traceability validator proves each AT's
references are valid and tagged; this proves the ATs collectively leave nothing unassessed.

It builds the expected item set from the cluster's consolidated_uoc.md, collects the UoC references
from each AT's benchmark/traceability section (resolving abbreviated tags and expanding range/list
tags exactly as the traceability validator does), and reports:
  * MISSING — consolidated items that no AT evidences (the gap that must be closed before the
    cluster is complete).
  * PHANTOM — AT references that are not consolidated items (per-AT traceability issues, surfaced
    again at the cluster level).
Overlap is expected and fine — an item may be evidenced by more than one AT — so items covered by
several ATs are reported only as an informational count, never as an error (unlike the
single-document consolidation check, where each item must appear exactly once).

Reuses the bundled traceability/consolidation helpers; stdlib only.

Usage:
  validate_cluster_coverage.py --cluster <dir> [--at <Assessor.docx> ...] [--consolidated <path>]
      (auto-discovers assessments/**/*Assessor*.docx if --at is omitted)

Exit 0 = PASS (every consolidated item is evidenced by at least one AT).
"""
import argparse
import glob
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_at_traceability import load_text, resolve_tags, valid_tag_set, split_benchmark


def at_items(path: Path) -> set:
    """Resolved UoC item tags referenced in an AT's benchmark section (whole doc if none)."""
    text = load_text(path)
    _, bench = split_benchmark(text)
    scan = bench if bench else text
    items = set()
    for line in scan.splitlines():
        for tag, _form in resolve_tags(line):
            if not tag.startswith("?? "):
                items.add(tag)
    return items


def by_section(tags):
    """Group 'UNIT SEC num' tags by section for a readable report."""
    out = {}
    for t in sorted(tags):
        sec = t.split()[1] if len(t.split()) > 1 else "?"
        out.setdefault(sec, []).append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster", required=True, type=Path)
    ap.add_argument("--at", action="append", type=Path, default=[],
                    help="an AT assessor file (repeatable); auto-discovered if omitted")
    ap.add_argument("--consolidated", type=Path,
                    help="defaults to <cluster>/consolidated_uoc.md")
    ap.add_argument("--include-ac", action="store_true",
                    help="also require Assessment Condition (AC) items to be referenced; by default "
                         "AC items are treated as satisfied by the assessment setup, not by criteria")
    args = ap.parse_args()

    consolidated = args.consolidated or (args.cluster / "consolidated_uoc.md")
    expected = valid_tag_set(consolidated)

    ats = list(args.at)
    if not ats:
        found = glob.glob(str(args.cluster / "assessments" / "**" / "*Assessor*.docx"), recursive=True)
        ats = sorted(Path(p) for p in found)
    if not ats:
        print(f"No AT assessor files found under {args.cluster}/assessments/. "
              f"Pass them with --at.", file=sys.stderr)
        sys.exit(2)

    per_at = {at.name: at_items(at) for at in ats}
    all_refs = Counter()
    for items in per_at.values():
        all_refs.update(items)
    covered = set(all_refs)

    secof = lambda t: t.split()[1] if len(t.split()) > 1 else "?"
    required = {t for t in expected if args.include_ac or secof(t) != "AC"}
    ac_items = {t for t in expected if secof(t) == "AC"}

    missing = sorted(required - covered)
    phantom = sorted(covered - expected)
    overlap = sorted(t for t, c in all_refs.items() if c > 1 and t in expected)

    print(f"Cluster:    {args.cluster.name}")
    print(f"ATs:        {len(ats)}")
    print(f"Required:   {len(required)} items (PC/FS/PE/KE" + ("/AC" if args.include_ac else "") + ")")
    print(f"Covered:    {len(covered & required)} / {len(required)} "
          f"({100 * len(covered & required) // max(len(required), 1)}%)")
    if not args.include_ac and ac_items:
        print(f"AC:         {len(covered & ac_items)} / {len(ac_items)} Assessment Conditions "
              f"referenced (satisfied by the assessment setup, not required in criteria — informational)")
    print()
    for name, items in per_at.items():
        print(f"  {name}: {len(items & expected)} items evidenced"
              + (f" (+{len(items - expected)} not in consolidated)" if (items - expected) else ""))
    print()

    if overlap:
        print(f"Overlap (evidenced by >1 AT — expected, informational): {len(overlap)} item(s)")
        print()

    if phantom:
        print(f"PHANTOM ({len(phantom)}) — AT references not in the consolidated UoC "
              f"(per-AT traceability issues):")
        for sec, tags in by_section(phantom).items():
            for t in tags:
                print(f"  - {t}")
        print()

    if missing:
        print(f"MISSING ({len(missing)}) — consolidated items no AT evidences:")
        for sec, tags in by_section(missing).items():
            print(f"  {sec}:")
            for t in tags:
                print(f"    - {t}")
        print()

    if not missing and not phantom:
        print("RESULT: PASS — every consolidated item is evidenced by at least one AT.")
        sys.exit(0)
    print("RESULT: FAIL"
          + (" — uncovered items remain" if missing else "")
          + (" — phantom references present" if phantom else "") + ".")
    sys.exit(1)


if __name__ == "__main__":
    main()
