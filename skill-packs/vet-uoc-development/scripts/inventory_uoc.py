#!/usr/bin/env python3
"""Extract every PC / FS / PE / KE / AC from a cluster's transcribed UoC .md files
as pre-tagged, verbatim item lines — the faithful raw material for consolidation.

The point is the same as the transcriber's: the consolidation step should ARRANGE
items into topic groups, never RETYPE them. This script lifts each item's text
straight from the (already validated) transcription and stamps it with its source
tag `[UNIT SECTION numbering]`, so the editorial step only moves tagged lines around
and can never drop, alter, or mis-tag an item.

The itemisation and numbering rules mirror exactly what `validate_consolidated.py`
enforces, so the emitted tags are precisely the set that validator expects:
  - PC  — the "N.N ..." entries in the Elements & Performance Criteria table
  - FS  — each row of the Foundation Skills table (skill name -> tag, description -> text)
  - PE/KE/AC — top-level bullets numbered 1..N in source order, with the special case
    that a section whose ONLY top-level bullet ends in ':' is a parent whose immediate
    sub-bullets are the items (e.g. ICTICT517 PE). Nested sub-bullets under a normal
    item are kept indented beneath it, as part of that one item.
  - the trailing "Assessors of this unit must satisfy..." paragraph is emitted as one
    extra AC item only when --assessor-ac is given (CL1/CL2 style; off for CL3).

Output is Markdown: '- [UNIT SEC num] <verbatim text>' lines, organised under
'## UNIT — SECTION' comments for navigation. Feed it to the grouping step.

stdlib only.

Usage:
  inventory_uoc.py --unit CODE=path/to/UNIT.md [--unit CODE=path ...] [--assessor-ac]
"""
import argparse
import re
import sys
from pathlib import Path

SECTIONS = [
    ("PC", "Elements and Performance Criteria"),
    ("FS", "Foundation Skills"),
    ("PE", "Performance Evidence"),
    ("KE", "Knowledge Evidence"),
    ("AC", "Assessment Conditions"),
]


def section_body(md: str, heading: str) -> str:
    """The text between '# heading' and the next '# ' heading (or end of doc)."""
    m = re.search(rf"# {re.escape(heading)}\n(.*?)(?=\n# )", md, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(rf"# {re.escape(heading)}\n(.*?)(?=\n# |\Z)", md, re.DOTALL)
    return m.group(1) if m else ""


def table_rows(section: str):
    """Yield each table row as a list of stripped cell strings, skipping the
    '| --- |' separator rows."""
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-+:?", c or "") for c in cells if c is not None) \
                and any(c for c in cells):
            continue  # separator row
        yield cells


def parse_pcs(md: str):
    """[(num, 'N.N text'), ...] from the performance-criteria column."""
    out = []
    for cells in table_rows(section_body(md, "Elements and Performance Criteria")):
        if len(cells) < 2:
            continue
        for piece in cells[1].split("<br>"):
            piece = piece.strip()
            m = re.match(r"^(\d+\.\d+)\s", piece)
            if m:
                out.append((m.group(1), piece))
    return out


def parse_fs(md: str):
    """[(skill_name, description), ...] from the Foundation Skills table."""
    out = []
    for cells in table_rows(section_body(md, "Foundation Skills")):
        if len(cells) < 2 or not cells[0]:
            continue
        if cells[0].lower().startswith("skill"):
            continue  # header row
        out.append((cells[0], cells[1]))
    return out


def parse_bullets(md: str, heading: str):
    """[(item_lines, ...)] for PE/KE/AC. Each item is a list of markdown lines:
    the parent bullet plus any nested children. Applies the single-parent-ending-':'
    special case (the children become the items)."""
    section = section_body(md, heading)
    lines = section.splitlines()

    blocks = []          # each block = list of lines (a top-level bullet + its children)
    for line in lines:
        if re.match(r"^- ", line):
            blocks.append([line])
        elif re.match(r"^\s+- ", line) and blocks:
            blocks[-1].append(line)
        # non-bullet lines (intro paragraphs, blanks) are ignored for itemisation

    if len(blocks) == 1 and blocks[0][0].rstrip().endswith(":"):
        # parent-with-children: the immediate sub-bullets are the items
        children = blocks[0][1:]
        return [[re.sub(r"^\s+- ", "- ", c)] for c in children]
    return blocks


def trailing_assessor_ac(md: str):
    """The 'Assessors of this unit must satisfy...' paragraph text, or None."""
    section = section_body(md, "Assessment Conditions")
    for line in section.splitlines():
        if line.strip().startswith("Assessors of this unit must"):
            return line.strip()
    return None


def emit_item(tag: str, parent_line: str, children=None) -> str:
    """Render one tagged item in house style: '- text [tag]' plus any indented
    child lines. The source tag sits at the end of the parent line (the convention
    used by CL2/CL3); nested sub-bullets follow, untagged, as part of this item."""
    text = re.sub(r"^- ", "", parent_line).strip()
    out = [f"- {text} [{tag}]"]
    for c in (children or []):
        out.append(c)  # child lines keep their source indentation
    return "\n".join(out)


def inventory(code: str, md: str, assessor_ac: bool):
    """Yield ('## CODE — SECTION', [rendered item lines]) for each section."""
    # PC
    pcs = parse_pcs(md)
    yield (f"## {code} — Performance Criteria",
           [f"- {text} [{code} PC {num}]" for num, text in pcs])
    # FS — house style bolds the skill name and separates it from the description
    fs = parse_fs(md)
    yield (f"## {code} — Foundation Skills",
           [f"- **{name}** — {desc} [{code} FS {name}]" for name, desc in fs])
    # PE / KE
    for sec, heading in (("PE", "Performance Evidence"), ("KE", "Knowledge Evidence")):
        blocks = parse_bullets(md, heading)
        items = [emit_item(f"{code} {sec} {i}", b[0], b[1:]) for i, b in enumerate(blocks, 1)]
        yield (f"## {code} — {heading}", items)
    # AC (+ optional trailing assessor paragraph)
    blocks = parse_bullets(md, "Assessment Conditions")
    items = [emit_item(f"{code} AC {i}", b[0], b[1:]) for i, b in enumerate(blocks, 1)]
    if assessor_ac:
        para = trailing_assessor_ac(md)
        if para:
            items.append(f"- {para} [{code} AC {len(blocks) + 1}]")
    yield (f"## {code} — Assessment Conditions", items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", required=True, action="append", help="CODE=path/to/UNIT.md")
    ap.add_argument("--assessor-ac", action="store_true",
                    help="emit the trailing assessor-requirements paragraph as one extra AC item")
    args = ap.parse_args()

    out = []
    total = 0
    for spec in args.unit:
        code, _, path = spec.partition("=")
        if not code or not path:
            ap.error(f"--unit must be CODE=PATH, got {spec!r}")
        md = Path(path).read_text(encoding="utf-8")
        out.append(f"# {code}")
        for header, items in inventory(code, md, args.assessor_ac):
            out.append(header)
            out.extend(items)
            out.append("")
            total += len(items)
    sys.stdout.write("\n".join(out).rstrip() + "\n")
    print(f"\n<!-- {total} items extracted across {len(args.unit)} unit(s) -->", file=sys.stderr)


if __name__ == "__main__":
    main()
