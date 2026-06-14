#!/usr/bin/env python3
"""Validate an assessment task's UoC traceability — the bidirectional rule that every marking
criterion carries a unit-of-competency reference and every referenced item is a real UoC item.

This enforces, mechanically, the traceability discipline that is otherwise checked by eye:
  * No phantom references — every tag in the AT resolves to a real item in the cluster's
    consolidated_uoc.md (catches typos, wrong unit codes, stale numbers).
  * No free-floating criteria — every criterion in the Marking Benchmark / UoC-traceability
    section carries at least one tag (catches a criterion added without provenance).
  * Optionally, coverage — every item the AT is expected to evidence appears against a criterion
    (pass --expect with the per-AT allocation from the assessment plan).

It also reports, as advisories:
  * Abbreviated tags (e.g. `[KE 2]` with the unit implied) — the convention is full unit refs;
    these are resolved against the nearest preceding full tag on the line, but flagged.
  * Marking-guide criteria not found in the benchmark section (best-effort — depends on the AT's
    criterion-id scheme; skipped cleanly if none is detected).

Reads the AT from its .docx (the artefact of record) or a .md companion. Reuses the bundled
docx_to_text extractor; stdlib only.

Usage:
  validate_at_traceability.py --at <AT.docx|AT.md> --consolidated <cluster>/consolidated_uoc.md
      [--expect "<UNIT SEC num>" --expect "..."]      # optional reverse-coverage check

Exit 0 = PASS (no phantom tags, no untagged criteria, expected coverage met if given).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_uoc import docx_to_text  # bundled, stdlib-only

FULL = re.compile(r"^(ICT\w+|BSB\w+|VU\d+)\s+(PC|FS|PE|KE|AC)\s+(.+)$")
ABBR = re.compile(r"^(PC|FS|PE|KE|AC)\s+(.+)$")
ANY_BRACKET = re.compile(r"\[([^\]]+)\]")
CRIT_ID = re.compile(r"^([A-Z]{1,2}\d+)\s*[—–-]\s*(.*)$")
BENCH_HEADING = re.compile(r"(benchmark|traceability)", re.IGNORECASE)


def load_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        return docx_to_text(path)
    return path.read_text(encoding="utf-8")


def valid_tag_set(consolidated: Path) -> set:
    """Every real item tag from the cluster's consolidated_uoc.md (code spans stripped)."""
    txt = re.sub(r"`[^`]*`", "", consolidated.read_text(encoding="utf-8"))
    out = set()
    for m in re.finditer(r"\[(ICT\w+|BSB\w+|VU\d+) (PC|FS|PE|KE|AC) ([^\]]+)\]", txt):
        out.add(f"{m.group(1)} {m.group(2)} {m.group(3).strip()}")
    return out


RANGE = re.compile(r"^(\d+(?:\.\d+)?)\s*[–—-]\s*(\d+(?:\.\d+)?)$")


def is_compressed(num: str) -> bool:
    return ("," in num) or bool(re.search(r"\d\s*[–—-]\s*\d", num))


def expand_numbering(num: str):
    """Expand a compressed numbering string into its individual members.
    'KE'-style ints: '1–6' -> 1..6, '3, 4, 6' -> [3,4,6]. 'PC'-style: '1.1–1.4' -> 1.1..1.4
    within the same major. Plain singles and FS skill-names pass through unchanged."""
    num = num.strip()
    if "," in num:
        return [m for part in num.split(",") for m in expand_numbering(part)]
    r = RANGE.match(num)
    if r:
        a, b = r.group(1), r.group(2)
        if "." in a and "." in b:
            amaj, amin = a.split("."); bmaj, bmin = b.split(".")
            if amaj == bmaj and amin.isdigit() and bmin.isdigit():
                return [f"{amaj}.{i}" for i in range(int(amin), int(bmin) + 1)]
            return [a, b]
        if a.isdigit() and b.isdigit():
            return [str(i) for i in range(int(a), int(b) + 1)]
        return [a, b]
    # numeric item with a trailing qualifier (e.g. '4.3 — partial') -> just the number;
    # a Foundation-skill name (no leading digit) passes through unchanged
    mnum = re.match(r"^(\d+(?:\.\d+)?)\b", num)
    return [mnum.group(1)] if mnum else [num]


def resolve_tags(line: str):
    """Yield (resolved 'UNIT SEC num', form) for each UoC item referenced on a line. Compressed
    range/list tags are expanded into one entry per member. Abbreviated tags (no unit) inherit the
    nearest preceding full tag's unit. form is one of: full | abbrev | compressed | unresolved."""
    current_unit = None
    for m in ANY_BRACKET.finditer(line):
        inside = m.group(1).strip()
        # compound multi-item tags join several references with a middle dot,
        # e.g. [ICTCLD401 KE 1 · ICTCLD502 KE 1]; resolve each part on its own
        for part in re.split(r"\s*·\s*", inside):
            part = part.strip()
            compound = part != inside
            mf = FULL.match(part)
            if mf:
                unit, sec, num = mf.group(1), mf.group(2), mf.group(3).strip()
                current_unit = unit
                form = "compressed" if (is_compressed(num) or compound) else "full"
                for member in expand_numbering(num):
                    yield (f"{unit} {sec} {member}", form)
                continue
            ma = ABBR.match(part)
            if ma:
                sec, num = ma.group(1), ma.group(2).strip()
                if not current_unit:
                    yield (f"?? {sec} {num}", "unresolved")
                    continue
                form = "compressed" if (is_compressed(num) or compound) else "abbrev"
                for member in expand_numbering(num):
                    yield (f"{current_unit} {sec} {member}", form)
            # other parts (placeholders, prose) are ignored


def split_benchmark(text: str):
    """Return (pre_benchmark_text, benchmark_text). The benchmark section starts at the last
    heading-like line mentioning 'benchmark' or 'traceability'."""
    lines = text.splitlines()
    idx = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if BENCH_HEADING.search(s) and len(s) < 80 and "[" not in s:
            idx = i
    if idx is None:
        return text, ""
    return "\n".join(lines[:idx]), "\n".join(lines[idx:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", required=True, type=Path, help="the AT .docx or .md")
    ap.add_argument("--consolidated", required=True, type=Path,
                    help="the cluster's consolidated_uoc.md (the valid-tag set)")
    ap.add_argument("--expect", action="append", default=[],
                    help="a UoC item the AT must evidence, e.g. 'BSBXTW401 PC 1.1' (repeatable)")
    args = ap.parse_args()

    text = load_text(args.at)
    valid = valid_tag_set(args.consolidated)
    pre, bench = split_benchmark(text)

    problems = []     # hard failures
    advisories = []   # warnings

    # ---- Parse the benchmark: criterion id -> resolved tags ----
    bench_criteria = {}   # id -> list[(tag, form)]
    covered = set()       # all resolved item tags across the AT (for reverse coverage)
    nonconforming = []    # tags not in individual full-ref form (abbreviated or compressed)
    invalid = []
    unresolved = []

    scan = bench if bench else text
    for line in scan.splitlines():
        m = CRIT_ID.match(line.strip())
        tags = list(resolve_tags(line))
        for tag, form in tags:
            if form == "unresolved":
                unresolved.append((line.strip()[:60], tag))
                continue
            covered.add(tag)
            if form != "full":
                nonconforming.append(tag)
            if tag not in valid:
                invalid.append(tag)
        if m:
            bench_criteria.setdefault(m.group(1), []).extend(tags)

    if not bench:
        problems.append("No 'Marking Benchmark / UoC traceability' section found — the AT has no "
                        "traceability table to validate. Add one (criterion -> UoC tags).")

    # ---- Hard check 1: phantom / invalid tags ----
    invalid = sorted(set(invalid))
    if invalid:
        problems.append(f"{len(invalid)} reference(s) not found in the consolidated UoC "
                        f"(phantom or mistyped):\n    " + "\n    ".join(invalid))
    if unresolved:
        problems.append(f"{len(unresolved)} abbreviated tag(s) with no preceding full tag to "
                        f"resolve the unit:\n    " + "\n    ".join(f"{t}  (in: {ln})" for ln, t in unresolved))

    # ---- Hard check 2: free-floating criteria (benchmark criterion with no tag) ----
    untagged = sorted(cid for cid, tags in bench_criteria.items()
                      if not any(f != "unresolved" for _, f in tags))
    if untagged:
        problems.append(f"{len(untagged)} benchmark criterion(s) with no UoC tag (free-floating): "
                        + ", ".join(untagged))

    # ---- Advisory: tags not in individual full-ref form ----
    if nonconforming:
        uniq = sorted(set(nonconforming))
        advisories.append(f"{len(uniq)} reference(s) not in individual full-ref form (abbreviated, "
                          f"or a range/list — expanded and validated here, but the convention prefers "
                          f"one full [UNIT SEC num] per item):\n    " + "\n    ".join(uniq))

    # ---- Advisory: marking-guide criteria missing from the benchmark (best-effort) ----
    # Only meaningful when the benchmark uses an identifiable criterion-id scheme; restrict the
    # guide scan to the same letter prefix(es) so task labels (AT1) and conditions (C1) don't match.
    if bench and bench_criteria:
        bench_prefixes = {re.match(r"[A-Z]+", cid).group() for cid in bench_criteria}
        guide_ids = set()
        for line in pre.splitlines():
            m = CRIT_ID.match(line.strip())
            if m and re.match(r"[A-Z]+", m.group(1)).group() in bench_prefixes:
                guide_ids.add(m.group(1))
        missing = sorted(guide_ids - set(bench_criteria))
        if missing:
            advisories.append(f"{len(missing)} marking-guide criterion(s) not found in the benchmark "
                              f"(possible free-floating — verify): " + ", ".join(missing))

    # ---- Optional reverse coverage vs an expected allocation ----
    if args.expect:
        expected = {e.strip() for e in args.expect}
        uncovered = sorted(expected - covered)
        if uncovered:
            problems.append(f"{len(uncovered)} expected item(s) not evidenced by any criterion:\n    "
                            + "\n    ".join(uncovered))

    # ---- Report ----
    print(f"AT:           {args.at.name}")
    print(f"Consolidated: {args.consolidated}")
    print(f"Tags found:   {len(covered)} unique  |  benchmark criteria: {len(bench_criteria)}")
    if args.expect:
        print(f"Expected:     {len(args.expect)} item(s) to cover")
    print()
    for a in advisories:
        print(f"ADVISORY: {a}\n")
    if problems:
        for p in problems:
            print(f"FAIL: {p}\n")
        print("RESULT: FAIL")
        sys.exit(1)
    print("RESULT: PASS — every criterion is tagged and every reference is a real UoC item"
          + (" with expected coverage met." if args.expect else "."))
    sys.exit(0)


if __name__ == "__main__":
    main()
