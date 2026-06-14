# validate_uoc.py — internals & deliberate behaviours

Read this when a validation result is surprising, or when adapting the validator to a course whose
UoC documents are structured differently. For normal use, the SKILL.md is enough.

## What it compares

For each `<docx> <md>` pair the script builds two word sequences and diffs them.

**From the `.docx`** (`docx_to_text`): textual content in document order, read straight from
`word/document.xml` — paragraphs and table-cell paragraphs. Within the XML it maps `w:t` → text,
`w:tab` → tab, `w:br` → newline, and recurses into `w:sdt` (structured-document-tag) content.
Table cells are emitted in row/column order with intra-cell line breaks preserved as newlines, so
they line up with `<br>` markers used inside Markdown table cells.

**From the `.md`** (`md_to_text`): the prose with Markdown *syntax* removed — heading markers
(`#`…), table pipe borders and `|---|` separator rows, leading list bullets (`-`/`*`/`+`/`N.`),
and `<br>` → newline. Table rows are split into their cell contents. The point is to strip only
syntax, never content.

Both sides are then tokenised on whitespace and compared as word lists.

## Two-tier diff

- **Substantive** — a real word add/remove/change. Computed on the cosmetically-normalised text,
  so it never fires on punctuation style alone. Any substantive block ⇒ `SUBSTANTIVE DIFFERENCES
  FOUND` and exit code 1.
- **Cosmetic** — the normalised sequences match but the raw ones differ: smart vs straight quotes
  (`' ' " "` → `' "`), en/em/minus dashes → `-`, non-breaking space → space, `…` → `...`, soft
  hyphen and BOM removed, Unicode NFC. Reported as `VERBATIM after cosmetic normalisation`, exit
  code 0.

## Deliberate exclusions and special cases (do not "fix" these)

These are intentional decisions baked into the tool. Re-flagging them as bugs wastes time.

1. **Headers and footers are excluded.** The `.docx` `word/header*.xml` / `word/footer*.xml`
   (training-package attribution, unit code, page numbers) are *not* part of the transcription and
   are not compared. Content that lives only in a header/footer will not appear as "missing".

2. **Markdown list bullets are syntax, not content.** A leading `- ` is stripped before
   comparison. If it were not, every bulleted PE/KE/AC line would show as a spurious insertion.

3. **Foundation-skill names keep their exact casing and spacing.** Source documents are
   inconsistent (`Oral communication` in one unit, `Oral Communication` in another; `Get the work
   done`). The transcription must preserve the source casing verbatim — the diff will catch a
   "correction".

4. **Nested structures are quoted whole.** A parent bullet with indented children (e.g. a KE item
   listing IaaS/PaaS/SaaS sub-points) is one block of text in both the `.docx` and the `.md`; the
   diff sees the combined words.

## Adapting to a new course

The comparison is content-agnostic — it works on any `<docx> <md>` pair regardless of unit code or
training package. The only assumptions are the OOXML structure of a standard `.docx` and that the
`.md` uses ordinary Markdown. If a new course's `.md` introduces syntax this script does not strip
(an unusual table style, footnotes, embedded HTML beyond `<br>`), extend `md_to_text` rather than
loosening the diff — keeping the comparison strict is the whole point.

## Invocation reference

```
python3 validate_uoc.py <docx1> <md1> [<docx2> <md2> ...]
```

Exit `0` = all pairs verbatim (cosmetic differences allowed); exit `1` = at least one pair has a
substantive difference; exit `2` = bad arguments (odd number of paths).
