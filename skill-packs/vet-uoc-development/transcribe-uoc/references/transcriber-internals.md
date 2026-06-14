# transcribe_uoc.py — internals & how to extend

Read this when a transcription does not validate as `EXACT MATCH` (a structural style the converter
doesn't yet handle), or when adapting to a training package whose Word template differs. For normal
use the SKILL.md is enough.

## The core idea

Content fidelity comes from **never retyping**. The converter walks the document body and copies the
text of each `w:t` run in document order — exactly as the validator's extractor reads it. The only
judgement it makes is *structural*: from each paragraph's **style**, decide whether it is a heading,
a bullet, or plain text, and render the Markdown accordingly. So the worst a structural bug can do
is mis-shape a heading/bullet/table — it can never change, drop, or invent a word. The validator
then catches any structural mistake, and the fix is made once in the script for all future units.

## Style → Markdown mapping (as observed across the ICT and BSB UoC corpus)

| Source paragraph style | Rendered as |
|---|---|
| `Title`, `Heading1`–`Heading6` | `#`…`######` heading (Title and Heading1 both → `#`) |
| `ListBullet` | top-level `- ` bullet |
| `ListBullet2`, `ListBullet3`, … | nested bullet, indented 2 spaces per level past the first |
| `SuperHeading`, `Version`, `BodyText`, unstyled | plain paragraph |
| empty / `AllowPageBreak` | dropped (spacer) |
| `w:tbl` (table) | Markdown table; each cell = its non-empty paragraphs joined with `<br>` |

Nesting depth is taken from the **style-name suffix** (`ListBullet2` → depth 1), with a
`w:numPr`/`w:ilvl` fallback for numbered lists. Preserving depth as 2-space indentation matters
downstream: the consolidation validator counts only top-level `- ` bullets and treats indented
sub-bullets as part of their parent item, so flattening them would inflate the item inventory.

## Deliberate behaviours (don't "fix" these)

1. **Headers/footers excluded.** Only `word/document.xml` (the body) is read; page furniture lives
   in separate parts and is correctly absent — it is not unit content.
2. **Horizontal whitespace collapsed.** Runs of spaces/tabs become one space. This is whitespace
   only, never a word, so it doesn't affect the validator's word-level check; it just keeps output
   clean and consistent with the existing corpus (some source docs carry stray double spaces).
3. **Tables always get a header underline.** Row 0 is treated as the header and a `| --- |`
   separator is emitted after it — matching how the validator skips that separator row.
4. **Structured-document tags (`w:sdt`) are traversed**, so content wrapped in content-controls is
   not lost.

## Why output round-trips through the validator

The validator's `md_to_text` strips Markdown syntax (headings, table pipes, the `| --- |` row,
leading bullets, `<br>`→newline) and compares the remaining words to the `.docx`. The converter is
built so that stripping its output's syntax recovers exactly the source words in order — which is
why `transcribe_uoc.py` then `validate_uoc.py` yields `EXACT MATCH`. The two scripts share the same
text-extraction semantics, so they agree by design.

## Adapting to a new structural style

If a unit fails to validate, diff the generated `.md` against the source to find the mis-shaped
region, then identify the source paragraph's style:

```bash
python3 - <<'PY'
import zipfile, xml.etree.ElementTree as ET
W="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
body=ET.parse(zipfile.ZipFile("<source.docx>").open("word/document.xml")).getroot().find(f"{W}body")
for p in body.iter(f"{W}p"):
    txt="".join(n.text or "" for n in p.iter() if n.tag==f"{W}t")
    pPr=p.find(f"{W}pPr"); s=pPr.find(f"{W}pStyle") if pPr is not None else None
    style=s.get(f"{W}val") if s is not None else None
    if txt.strip(): print(style, "|", txt[:70])
PY
```

Then extend the relevant classifier in `transcribe_uoc.py`:
- a new heading style → `heading_level`
- a new list style → the `List…` pattern in `list_level`
- a new table shape → `render_table` / `cell_md`

Keep the change minimal and re-run the full corpus sweep (transcribe every existing unit, validate,
and diff against the known-good `.md`) to confirm no regression before relying on it.
