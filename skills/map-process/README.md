# map-process

Turn a factory's **step→gate run-sheet** into a **Mermaid process map** + a **structured audit model**.
A visual summary of the process a factory currently implements — and the input to a process audit.

- **What / how:** see [SKILL.md](SKILL.md).
- **Engine:** [`map_process.py`](map_process.py) — stdlib only (no venv, no third-party deps).
- **Output:** `docs/process-maps/<slug>.md` (flowchart + tooling/locus + audit table) and `<slug>.json`
  (the model a downstream audit consumes); `factory-overview.md` when ≥2 run-sheets are mapped together.

**Internally created.** `python3`, stdlib only. `tests.py` covers the run-sheet parser, the inventory +
name resolver, the gate cross-check/audit, data/locus harvesting, and an end-to-end render.

Quick run (from the repo root):

```bash
python3 .claude/skills/map-process/map_process.py \
    docs/run-sheet.md \
    --skills-root .claude --engines-root scripts --out docs/process-maps
```

Regenerate whenever the run-sheets or the skills inventory change — the maps are generated artefacts,
not hand-edited. The `.md` files render their Mermaid on GitHub / in a VS Code Markdown-Mermaid preview.
