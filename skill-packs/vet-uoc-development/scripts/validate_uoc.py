#!/usr/bin/env python3
"""Validate that a .md UoC transcription is verbatim against the source .docx.

For each pair, extract textual content in document order from the .docx
(paragraphs + table cells, preserving line breaks within cells), strip
markdown syntax from the .md, and diff the resulting word sequences.

Reports differences in two tiers:
  - Substantive: words added/removed/changed
  - Cosmetic: punctuation/quote/whitespace normalisation differences
"""

import difflib
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_to_text(docx_path: Path) -> str:
    """Extract textual content from a .docx in document order.

    Paragraphs are separated by newlines. Table cell content is also
    paragraph-like; line breaks within a cell (w:br) become newlines, so
    they line up with the <br> markers used in the .md.
    """
    with zipfile.ZipFile(docx_path) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)

    body = tree.getroot().find(f"{W_NS}body")
    if body is None:
        return ""

    out_lines = []

    def render_paragraph(p_elem) -> str:
        parts = []
        for node in p_elem.iter():
            tag = node.tag
            if tag == f"{W_NS}t":
                parts.append(node.text or "")
            elif tag == f"{W_NS}tab":
                parts.append("\t")
            elif tag == f"{W_NS}br":
                parts.append("\n")
        return "".join(parts)

    def walk(elem):
        for child in elem:
            tag = child.tag
            if tag == f"{W_NS}p":
                out_lines.append(render_paragraph(child))
            elif tag == f"{W_NS}tbl":
                for row in child.findall(f"{W_NS}tr"):
                    for cell in row.findall(f"{W_NS}tc"):
                        cell_parts = []
                        for cp in cell.findall(f"{W_NS}p"):
                            cell_parts.append(render_paragraph(cp))
                        # Use newline within cells so it lines up with <br> in md
                        out_lines.append("\n".join(cell_parts))
            elif tag == f"{W_NS}sdt":
                # Structured document tag — recurse into content
                content = child.find(f"{W_NS}sdtContent")
                if content is not None:
                    walk(content)
            else:
                walk(child)

    walk(body)
    return "\n".join(out_lines)


def md_to_text(md_path: Path) -> str:
    """Strip markdown syntax from a .md file, leaving the textual content.

    Removes heading markers, table pipes, table separator rows, and converts
    <br> tags to newlines. Leaves prose otherwise untouched.
    """
    raw = md_path.read_text(encoding="utf-8")
    out_lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        # Skip empty lines (we'll re-add structure via newlines)
        if not stripped:
            out_lines.append("")
            continue
        # Table separator row: | --- | --- | ...
        if re.fullmatch(r"\|?\s*(:?-{3,}:?\s*\|\s*)+:?-{3,}:?\s*\|?", stripped):
            continue
        # Heading: # Foo, ## Foo, etc.
        m = re.match(r"^#{1,6}\s+(.*)$", stripped)
        if m:
            out_lines.append(m.group(1))
            continue
        # List item: - foo, * foo, + foo, or numbered "1. foo"
        # (preserve indentation in the original line; we operate on stripped here,
        # but indented sub-bullets still start with "- " after .strip())
        m = re.match(r"^([-*+]|\d+\.)\s+(.*)$", stripped)
        if m:
            stripped = m.group(2)
        # Table row: | a | b | ... → split into cell contents (one per line)
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # Convert <br> within cells to newlines
            cell_lines = []
            for c in cells:
                cell_lines.extend(re.split(r"<br\s*/?>", c, flags=re.IGNORECASE))
            out_lines.extend(cl.strip() for cl in cell_lines)
            continue
        # Regular line: convert any inline <br> to newlines
        parts = re.split(r"<br\s*/?>", stripped, flags=re.IGNORECASE)
        out_lines.extend(p.strip() for p in parts)
    return "\n".join(out_lines)


def normalise_cosmetic(text: str) -> str:
    """Apply cosmetic normalisations: smart quotes, dashes, NBSPs, NFC."""
    text = unicodedata.normalize("NFC", text)
    replacements = {
        "‘": "'", "’": "'", "‚": "'", "‛": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"',
        "–": "-", "—": "-", "−": "-",  # en/em/minus → hyphen
        " ": " ",  # non-breaking space
        "…": "...",  # horizontal ellipsis
        "­": "",   # soft hyphen
        "﻿": "",   # BOM
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def to_words(text: str) -> list[str]:
    """Tokenise to words, ignoring all whitespace and line structure."""
    # Collapse all whitespace, split on whitespace
    return text.split()


def diff_report(label: str, docx_text: str, md_text: str) -> dict:
    """Compare docx and md texts. Returns a dict of findings."""
    # Stage 1: raw word diff (substantive)
    docx_words = to_words(docx_text)
    md_words = to_words(md_text)

    raw_match = docx_words == md_words

    # Stage 2: cosmetic normalisation
    docx_norm = normalise_cosmetic(docx_text)
    md_norm = normalise_cosmetic(md_text)
    docx_norm_words = to_words(docx_norm)
    md_norm_words = to_words(md_norm)

    cosmetic_match = docx_norm_words == md_norm_words

    findings = {
        "label": label,
        "docx_word_count": len(docx_words),
        "md_word_count": len(md_words),
        "exact_match": raw_match,
        "cosmetic_match": cosmetic_match,
        "substantive_diff": [],
        "cosmetic_diff": [],
    }

    if not cosmetic_match:
        # Substantive differences (after cosmetic normalisation)
        sm = difflib.SequenceMatcher(a=docx_norm_words, b=md_norm_words, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            findings["substantive_diff"].append({
                "op": tag,
                "docx_range": (i1, i2),
                "md_range": (j1, j2),
                "docx_words": docx_norm_words[i1:i2],
                "md_words": md_norm_words[j1:j2],
            })

    if cosmetic_match and not raw_match:
        # Find cosmetic differences character-by-character
        sm = difflib.SequenceMatcher(a=docx_words, b=md_words, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            findings["cosmetic_diff"].append({
                "op": tag,
                "docx_words": docx_words[i1:i2],
                "md_words": md_words[j1:j2],
            })

    return findings


def print_findings(f: dict) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {f['label']}")
    print(f"{'=' * 70}")
    print(f"  docx words: {f['docx_word_count']}    md words: {f['md_word_count']}")
    if f["exact_match"]:
        print("  RESULT: EXACT MATCH (byte-equivalent at word level)")
        return
    if f["cosmetic_match"]:
        print("  RESULT: VERBATIM after cosmetic normalisation (quotes/dashes/whitespace)")
        if f["cosmetic_diff"]:
            print(f"  Cosmetic-only diffs ({len(f['cosmetic_diff'])} blocks):")
            for d in f["cosmetic_diff"][:10]:
                print(f"    [{d['op']}]  docx: {d['docx_words']!r}")
                print(f"          md:   {d['md_words']!r}")
            if len(f["cosmetic_diff"]) > 10:
                print(f"    ... and {len(f['cosmetic_diff']) - 10} more")
        return
    print("  RESULT: SUBSTANTIVE DIFFERENCES FOUND")
    print(f"  Substantive diff blocks: {len(f['substantive_diff'])}")
    for d in f["substantive_diff"]:
        print(f"\n    [{d['op']}] docx[{d['docx_range'][0]}:{d['docx_range'][1]}]  md[{d['md_range'][0]}:{d['md_range'][1]}]")
        print(f"      docx: {' '.join(d['docx_words'])!r}")
        print(f"      md:   {' '.join(d['md_words'])!r}")


def main():
    pairs = sys.argv[1:]
    if not pairs or len(pairs) % 2 != 0:
        print("Usage: validate_uoc.py <docx1> <md1> [<docx2> <md2> ...]", file=sys.stderr)
        sys.exit(2)

    any_substantive = False
    for i in range(0, len(pairs), 2):
        docx_path = Path(pairs[i])
        md_path = Path(pairs[i + 1])
        label = f"{docx_path.name}  vs  {md_path.name}"
        docx_text = docx_to_text(docx_path)
        md_text = md_to_text(md_path)
        f = diff_report(label, docx_text, md_text)
        print_findings(f)
        if not f["cosmetic_match"]:
            any_substantive = True

    print()
    sys.exit(1 if any_substantive else 0)


if __name__ == "__main__":
    main()
