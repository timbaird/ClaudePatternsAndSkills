#!/usr/bin/env python3
"""Transcribe a .docx unit-of-competency document into verbatim Markdown.

The content is taken **straight from the Word XML runs** — never retyped — so the transcription
is faithful by construction: no paraphrasing, no omission, no "tidying". Page furniture that is
not part of the unit (headers, footers, page numbers) is excluded automatically, because this
reads only `word/document.xml` (the body); headers/footers live in separate parts.

Structure is reconstructed from the source paragraph styles, which are consistent across the ICT
training-package UoC documents:

    Title / Heading1..6   -> '# ' .. '###### ' headings
    ListBullet / numbered -> '- ' bullets
    table (w:tbl)         -> a Markdown table; multi-paragraph cells joined with '<br>'
    everything else       -> a plain paragraph
    empty / spacer paras  -> dropped

The output is designed to round-trip through the companion validator: running
`validate_uoc.py <docx> <this-output>` should report EXACT MATCH. That validation is the proof of
fidelity and MUST be run after transcribing (the transcribe-uoc skill does this automatically).

stdlib only — runs anywhere with python3, no virtualenv.

Usage:  python3 transcribe_uoc.py <source.docx> [output.md]
        (writes to stdout if no output path is given)
"""
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def para_text(p) -> str:
    """Concatenate a paragraph's text runs, mirroring the validator's extraction:
    w:t -> text, w:tab -> tab, w:br -> newline (rendered as <br> when inlined)."""
    parts = []
    for node in p.iter():
        tag = node.tag
        if tag == f"{W}t":
            parts.append(node.text or "")
        elif tag == f"{W}tab":
            parts.append("\t")
        elif tag == f"{W}br":
            parts.append("\n")
    return "".join(parts)


def inline(text: str) -> str:
    """Render extracted text as a single Markdown line.

    Internal line breaks become <br>. Runs of horizontal whitespace (stray double
    spaces and tabs left in the source Word doc) are collapsed to a single space —
    this only ever touches spacing, never a word, so the verbatim word sequence the
    validator checks is unchanged, while the output stays clean and house-consistent."""
    text = re.sub(r"[ \t]+", " ", text)
    return text.replace("\n", "<br>").strip()


def get_style(p):
    pPr = p.find(f"{W}pPr")
    if pPr is None:
        return None
    s = pPr.find(f"{W}pStyle")
    return s.get(f"{W}val") if s is not None else None


def heading_level(style):
    """Title and Heading1 are top-level (#). HeadingN -> N hashes. Else not a heading."""
    if not style:
        return None
    if style == "Title":
        return 1
    m = re.fullmatch(r"Heading([1-6])", style)
    return int(m.group(1)) if m else None


def list_level(p, style):
    """Return the 0-based nesting depth if this paragraph is a list item, else None.

    Depth comes from the style-name suffix used by the ICT UoC documents
    (ListBullet -> 0, ListBullet2 -> 1, ListBullet3 -> 2, ...). A numbered-list
    indent level (w:numPr/w:ilvl) is used as a fallback when present. Nesting is
    preserved as 2-space indentation so the consolidation step still counts only
    top-level bullets and treats sub-bullets as part of their parent item."""
    if style:
        m = re.fullmatch(r"List(?:Bullet|Number|Paragraph)(\d*)", style)
        if m:
            return int(m.group(1)) - 1 if m.group(1) else 0
    pPr = p.find(f"{W}pPr")
    if pPr is not None:
        npr = pPr.find(f"{W}numPr")
        if npr is not None:
            il = npr.find(f"{W}ilvl")
            return int(il.get(f"{W}val")) if il is not None else 0
    return None


def cell_md(cell) -> str:
    """A table cell's content: its non-empty paragraphs joined with <br>."""
    paras = [inline(para_text(p)) for p in cell.findall(f"{W}p")]
    return "<br>".join(p for p in paras if p)


def render_table(tbl) -> str:
    out = []
    rows = tbl.findall(f"{W}tr")
    for ri, row in enumerate(rows):
        cells = [cell_md(c) for c in row.findall(f"{W}tc")]
        out.append("| " + " | ".join(cells) + " |")
        if ri == 0:  # header underline
            out.append("| " + " | ".join("---" for _ in cells) + " |")
    return "\n".join(out)


def iter_blocks(parent):
    """Yield ('p'|'tbl', element) in document order, recursing through structured-doc tags."""
    for child in parent:
        tag = child.tag
        if tag == f"{W}p":
            yield ("p", child)
        elif tag == f"{W}tbl":
            yield ("tbl", child)
        elif tag == f"{W}sdt":
            content = child.find(f"{W}sdtContent")
            if content is not None:
                yield from iter_blocks(content)


def transcribe(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path) as z:
        tree = ET.parse(z.open("word/document.xml"))
    body = tree.getroot().find(f"{W}body")
    if body is None:
        return ""

    blocks = []
    listbuf = []

    def flush():
        if listbuf:
            blocks.append("\n".join(listbuf))
            listbuf.clear()

    for kind, elem in iter_blocks(body):
        if kind == "tbl":
            flush()
            blocks.append(render_table(elem))
            continue

        style = get_style(elem)
        text = inline(para_text(elem))
        if not text:                       # spacer paragraph — also ends any open list
            flush()
            continue

        lvl = heading_level(style)
        depth = list_level(elem, style)
        if lvl is not None:
            flush()
            blocks.append("#" * lvl + " " + text)
        elif depth is not None:
            listbuf.append("  " * depth + "- " + text)   # consecutive bullets stay a tight list
        else:
            flush()
            blocks.append(text)

    flush()
    return "\n\n".join(blocks) + "\n"


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: transcribe_uoc.py <source.docx> [output.md]", file=sys.stderr)
        sys.exit(2)
    docx = Path(sys.argv[1])
    md = transcribe(docx)
    if len(sys.argv) == 3:
        out = Path(sys.argv[2])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"Wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
