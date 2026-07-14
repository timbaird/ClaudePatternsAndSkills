#!/usr/bin/env python3
"""map-process — turn a factory run-sheet into a Mermaid process map + audit model.

Stdlib only. Reads a run-sheet doc written in the factory step->gate convention
(``**N · `skill` — Title** *(scope)*`` step headers; ``> **⟱ Gate N→M:** *kind* `validator` = …``
gate blockquotes) and emits, per run-sheet:

  <out>/<slug>.md    — a Mermaid flowchart (steps -> gates -> done) + legend + an audit table
  <out>/<slug>.json  — the structured process model (the seam a downstream audit skill consumes)

Given ≥2 run-sheets it also writes <out>/factory-overview.md, chaining them in argument
order (last gate of one -> first step of the next).

The map's colour + the audit flags come from a **cross-check**: every validator a gate NAMES is
resolved against what actually exists under the skills root (a skill dir, a scripts/ engine, or an
agent). A named validator that resolves nowhere, or a doc status marker that contradicts reality
(prose says "to build" but the skill exists, or vice-versa), is flagged — that flag set is the
input to a process audit.

Usage (from the repo root):
  python .claude/skills/map-process/map_process.py \
      docs/run-sheet.md \
      --skills-root .claude --engines-root scripts --out docs/process-maps
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# ── run-sheet grammar ────────────────────────────────────────────────────────
# **N · `skill` — Title** *(scope)*   (skill + em-dash optional; scope optional)
STEP_RE = re.compile(r"^\*\*(\d+)\s*·\s*(.+?)\*\*\s*(?:\*\((.+?)\)\*)?\s*$")
STEP_SKILL_RE = re.compile(r"^`([^`]+)`\s*—\s*(.+)$")
# > **⟱ Gate N→M (label):** rest…
GATE_RE = re.compile(r"^>\s*\*\*⟱\s*Gate\s*(\w+)\s*→\s*(\w+)\s*(?:\((.+?)\))?\s*:\*\*\s*(.*)$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
H1_RE = re.compile(r"^#\s+(.+?)\s*$")


def _status(text: str) -> str | None:
    """'planned' (a 'to build' marker), 'built' (a 'built' marker), or None."""
    t = text.lower()
    if re.search(r"\bto build\b", t):
        return "planned"
    if re.search(r"\bbuilt\b", t):
        return "built"
    return None


def _gate_kind(text: str) -> str:
    t = text.lower()
    if "*validator*" in t:
        return "validator"
    if "*human" in t or "human review" in t or "human /" in t or "institutional*" in t:
        return "human"
    return "other"


def parse_runsheet(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    name = path.stem
    for ln in lines:
        m = H1_RE.match(ln)
        if m:
            name = m.group(1)
            break

    # locate every step header and gate header with its line index
    marks = []  # (idx, 'step'|'gate', match)
    for i, ln in enumerate(lines):
        mg = GATE_RE.match(ln)
        if mg:
            marks.append((i, "gate", mg))
            continue
        ms = STEP_RE.match(ln)
        if ms:
            marks.append((i, "step", ms))

    steps, gates = [], []
    for k, (idx, kind, m) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        block = "\n".join(lines[idx:end])
        if kind == "step":
            num, title, scope = m.group(1), m.group(2).strip(), (m.group(3) or "").strip() or None
            skill = None
            ms = STEP_SKILL_RE.match(title)
            if ms:
                skill, title = ms.group(1), ms.group(2).strip()
            steps.append({
                "num": num, "title": title, "skill": skill, "scope": scope,
                "status": _status(block), "_block": block,
            })
        else:
            g_from, g_to, label = m.group(1), m.group(2), (m.group(3) or "").strip() or None
            # gate body = the leading blockquote run from this line
            body = [m.group(4)]
            for ln in lines[idx + 1:end]:
                if ln.lstrip().startswith(">"):
                    body.append(ln.lstrip()[1:].strip())
                elif ln.strip() == "":
                    continue
                else:
                    break
            body_txt = " ".join(body)
            names = [n for n in BACKTICK_RE.findall(body_txt)]
            gates.append({
                "from": g_from, "to": g_to, "label": label,
                "kind": _gate_kind(body_txt),
                "names": names,
                "human": bool(re.search(r"\+\s*human|human review|human\s*/|institutional", body_txt, re.I)),
                "status": _status(body_txt),
            })

    # detail sections (## §N — …) keyed by step number, so a step's tooling can be
    # harvested from its deep detail as well as its terse pipeline block.
    details, cur, buf = {}, None, []
    detail_re = re.compile(r"^##\s*§\s*(\d+)\b")
    for ln in lines:
        m = detail_re.match(ln)
        if m:
            if cur:
                details[cur] = "\n".join(buf)
            cur, buf = m.group(1), [ln]
        elif cur is not None:
            if ln.startswith("# "):     # left the detail area entirely
                details[cur] = "\n".join(buf); cur = None; buf = []
            else:
                buf.append(ln)
    if cur:
        details[cur] = "\n".join(buf)

    return {"name": name, "source": str(path), "steps": steps, "gates": gates, "_details": details}


# ── cross-check (the audit seam) ─────────────────────────────────────────────
def load_inventory(skills_root: Path, engines_root: Path) -> dict:
    skills = {p.name for p in (skills_root / "skills").iterdir()
              if p.is_dir() and p.name != "scripts"} if (skills_root / "skills").is_dir() else set()
    scripts = {p.stem for p in (skills_root / "skills" / "scripts").glob("*.py")} \
        if (skills_root / "skills" / "scripts").is_dir() else set()
    agents = {p.stem for p in (skills_root / "agents").glob("*.md")} \
        if (skills_root / "agents").is_dir() else set()
    # the engine scripts under the engines-root (one level deep)
    engines = {p.stem for p in engines_root.glob("*.py")} | \
              {p.stem for p in engines_root.glob("*/*.py")} if engines_root.is_dir() else set()
    return {"skills": skills, "scripts": scripts, "agents": agents, "engines": engines}


def resolve(name: str, inv: dict) -> tuple[str, str] | None:
    """Resolve a named tool to (kind, resolved-name); kind ∈ skill|script|agent|engine|mcp; else None."""
    n = name.strip().strip("`").strip()
    if n.startswith("mcp__"):
        return ("mcp", n)
    n = re.sub(r"\s+agent$", "", n)            # "verify-scenario-realisation agent"
    kebab = n[:-3] if n.endswith(".py") else n
    snake = kebab.replace("-", "_")
    if kebab in inv["skills"]:
        return ("skill", kebab)
    if snake in inv["scripts"] or (n.endswith(".py") and n[:-3] in inv["scripts"]):
        return ("script", snake if snake in inv["scripts"] else n[:-3])
    if kebab in inv["agents"]:
        return ("agent", kebab)
    if snake in inv["engines"] or (n.endswith(".py") and n[:-3] in inv["engines"]):
        return ("engine", snake if snake in inv["engines"] else n[:-3])
    return None


def audit_gate(g: dict, inv: dict) -> dict:
    """Attach resolution + flags to a gate. Returns the enriched gate."""
    resolved, seen_names = [], set()
    for nm in g["names"]:
        if nm in seen_names:      # a validator mentioned twice in the gate prose renders once
            continue
        seen_names.add(nm)
        # skip incidental backticked data files (e.g. notes.md, data.json, …) —
        # only a bare identifier or an explicit *.py can name a validator.
        if "." in nm and not nm.endswith(".py"):
            continue
        r = resolve(nm, inv)
        looks_validatorish = nm.startswith(("validate", "verify", "consolidate", "transcribe",
                                            "generate", "setup", "evaluate")) or nm.endswith(".py")
        if r or looks_validatorish:
            resolved.append({"name": nm, "resolves": r})
    implemented = any(r["resolves"] for r in resolved)
    flags = []
    if g["kind"] == "validator":
        for r in resolved:
            if not r["resolves"]:
                flags.append(f"names `{r['name']}` but no skill/script/agent resolves it")
        if not resolved:
            flags.append("marked *validator* but names no validator")
    if g["status"] == "planned" and implemented:
        flags.append("doc status says 'to build' but an implementation exists (stale doc?)")
    if g["status"] == "built" and g["kind"] == "validator" and not implemented:
        flags.append("doc status says 'built' but no implementation resolves")
    if g["kind"] == "human" and not implemented:
        flags.append("human-only gate — candidate for tooling")
    # colour class
    if any("stale doc" in f or "no skill/script" in f or "no implementation" in f for f in flags):
        cls = "flag"
    elif implemented:
        cls = "built"
    else:
        cls = "human"
    g = dict(g)
    g["resolved"] = resolved
    g["implemented"] = implemented
    g["flags"] = flags
    g["cls"] = cls
    return g


KIND_ICON = {"skill": "🛠", "agent": "🤖", "script": "⚙", "engine": "⚙", "mcp": "🔌"}


def _tool_index(inv: dict) -> list[tuple[str, str, re.Pattern]]:
    """A search index of every known tool: (resolved-name, kind, word-boundary matcher).
    Matches either the canonical form or its kebab/snake variant however the doc spells it."""
    idx = []
    for kind, key in (("skill", "skills"), ("agent", "agents"),
                      ("engine", "engines"), ("script", "scripts")):
        for name in sorted(inv[key], key=len, reverse=True):
            variants = {name, name.replace("_", "-"), name.replace("-", "_")}
            pat = re.compile(r"(?<![\w-])(?:" + "|".join(re.escape(v) for v in variants) + r")(?![\w-])")
            idx.append((name, kind, pat))
    return idx


def attach_tools(model: dict, inv: dict) -> None:
    """Harvest every skill/agent/engine/MCP each step USES (from its pipeline block + §detail) by
    scanning for any KNOWN tool name however it's spelled (backticked, bold, or bare) — minus the
    step's own primary skill and its gate's validators (those render on the step header / gate)."""
    index = _tool_index(inv)
    norm = lambda x: (x or "").replace("_", "-")
    gate_names = {norm(r["resolves"][1]) for g in model["gates"]
                  for r in g.get("resolved", []) if r["resolves"]}
    for s in model["steps"]:
        primary = norm(s["skill"])
        text = (s.pop("_block", "") + "\n" + model["_details"].get(s["num"], ""))
        seen = {}
        for name, kind, pat in index:
            if norm(name) == primary or norm(name) in gate_names:
                continue
            if pat.search(text):
                seen.setdefault(norm(name), {"name": name, "kind": kind})
        for mcp in sorted(set(re.findall(r"mcp__[\w]+", text))):
            seen.setdefault(mcp, {"name": mcp, "kind": "mcp"})
        s["tools"] = list(seen.values())
        s["data"] = harvest_data(text, inv)


DATA_EXT = (".md", ".docx", ".pptx", ".yaml", ".yml", ".json", ".ts", ".astro", ".drawio", ".csv")
WEBSITE_HINT = re.compile(r"\.astro|/src/|website", re.I)


def harvest_data(text: str, inv: dict) -> list[dict]:
    """Data artefacts a step draws on / produces — backticked filenames with a data extension,
    tagged by locus (📦 sub-repo by default; 🌐 website when the token looks website-side).
    A filename whose stem resolves to a known tool (e.g. an agent's `.md`) is a tool, not data."""
    seen = {}
    for nm in BACKTICK_RE.findall(text):
        low = nm.lower().rstrip("/")
        if low.endswith(".py") or not any(low.endswith(e) for e in DATA_EXT):
            continue
        base = nm.rstrip("/").split("/")[-1]
        stem = base[:base.rfind(".")]
        if not stem or any(c in base for c in "<>*…"):
            continue  # bare extension (".docx") or a templated/glob placeholder — not a concrete artefact
        if resolve(stem, inv):
            continue  # this is a tool's own file (agent/skill .md), surfaced as tooling not data
        locus = "website" if WEBSITE_HINT.search(nm) else "subrepo"
        seen.setdefault(base, {"name": base, "path": nm, "locus": locus})
    return list(seen.values())


# ── mermaid emit ─────────────────────────────────────────────────────────────
def _lbl(s: str) -> str:
    return s.replace('"', "'").replace("`", "").strip()


CLASSDEFS = (
    "  classDef step fill:#eef2f7,stroke:#5b6b7f,color:#1f2933;\n"
    "  classDef built fill:#d7ecd9,stroke:#2e7d32,color:#173a1a;\n"
    "  classDef human fill:#fdecc8,stroke:#b8860b,color:#4a3510;\n"
    "  classDef flag fill:#f6c6c6,stroke:#b71c1c,color:#4a1010;\n"
    "  classDef done fill:#dfe7ef,stroke:#5b6b7f,color:#1f2933;\n"
)


def mermaid(model: dict) -> str:
    steps, gates = model["steps"], model["gates"]
    out = ["```mermaid", "flowchart TD"]
    # nodes
    for s in steps:
        sub = []
        # 🏠 factory lane — the primary skill + every tool the stage runs
        factory_tools = ([s["skill"]] if s["skill"] else []) + [t["name"] for t in s.get("tools", [])]
        if factory_tools:
            sub.append(f"<i>🏠 {_lbl(', '.join(factory_tools))}</i>")
        # 📦 / 🌐 data lane — sub-repo / website artefacts the stage draws on
        for locus, icon in (("subrepo", "📦"), ("website", "🌐")):
            names = [d["name"] for d in s.get("data", []) if d["locus"] == locus][:4]
            if names:
                sub.append(f"<i>{icon} {_lbl(', '.join(names))}</i>")
        # 👤 actor — flag the hands-on, human-led stages
        if not s["skill"]:
            sub.append("<i>👤 human-led</i>")
        if s["scope"]:
            sub.append(f"<i>({_lbl(s['scope'])})</i>")
        label = f"{s['num']} · {_lbl(s['title'])}"
        if sub:
            label += "<br/>" + "<br/>".join(sub)
        out.append(f'  S{s["num"]}["{label}"]:::step')
    for g in gates:
        head = f"Gate {g['from']}→{g['to']}"
        validators = [r["name"] for r in g.get("resolved", []) if r["resolves"]]
        if validators:
            head += "<br/>" + _lbl(", ".join(validators))
        elif g["kind"] == "human":
            head += "<br/>human review"
        if g["human"] and validators:
            head += " + human"
        gid = f'G{g["from"]}_{g["to"]}'
        out.append(f'  {gid}{{{{"{head}"}}}}:::{g["cls"]}')
    out.append('  DONE(["done"]):::done')
    # edges — step -> its gate -> next step
    gate_by_from = {g["from"]: g for g in gates}
    for s in steps:
        g = gate_by_from.get(s["num"])
        if not g:
            continue
        gid = f'G{g["from"]}_{g["to"]}'
        out.append(f'  S{s["num"]} --> {gid}')
        if g["to"].isdigit() and any(s2["num"] == g["to"] for s2 in steps):
            out.append(f'  {gid} -->|PASS| S{g["to"]}')
        else:
            out.append(f'  {gid} -->|PASS| DONE')
    out.append(CLASSDEFS.rstrip("\n"))
    out.append("```")
    return "\n".join(out)


def audit_table(model: dict) -> str:
    rows = ["| Gate | Kind | Names | Resolves to | Doc status | Audit flag |",
            "|---|---|---|---|---|---|"]
    for g in model["gates"]:
        res = "; ".join(
            f"`{r['name']}`→{r['resolves'][0]}" if r["resolves"] else f"`{r['name']}`→**none**"
            for r in g["resolved"]) or "—"
        names = ", ".join(f"`{n}`" for n in g["names"]) or ("human" if g["kind"] == "human" else "—")
        flag = "; ".join(g["flags"]) if g["flags"] else ("✓ ok" if g["implemented"] else "—")
        rows.append(
            f"| {g['from']}→{g['to']} | {g['kind']} | {names} | {res} | {g['status'] or '—'} | {flag} |")
    return "\n".join(rows)


def tooling_table(model: dict) -> str:
    rows = ["| Step | 🏠 Factory tooling (skill 🛠 · agent 🤖 · engine ⚙ · MCP 🔌) | 📦/🌐 Project data drawn on | Actor |",
            "|---|---|---|---|"]
    for s in model["steps"]:
        tools = []
        if s["skill"]:
            tools.append(f"🛠 `{s['skill']}`")
        tools += [f"{KIND_ICON.get(t['kind'], '·')} `{t['name']}`" for t in s.get("tools", [])]
        data = ", ".join(
            f"{'🌐' if d['locus'] == 'website' else '📦'} `{d['name']}`" for d in s.get("data", [])) or "—"
        actor = "👤 human-led" if not s["skill"] else "⚙ tool-driven"
        rows.append(f"| {s['num']} · {s['title']} | {', '.join(tools) or '—'} | {data} | {actor} |")
    return "\n".join(rows)


def summary(model: dict) -> str:
    g = model["gates"]
    built = sum(1 for x in g if x["cls"] == "built")
    human = sum(1 for x in g if x["cls"] == "human")
    flagged = sum(1 for x in g if x["cls"] == "flag")
    return (f"**{len(model['steps'])} steps · {len(g)} gates** — "
            f"{built} machine-gated, {human} human-only, **{flagged} flagged** for review.")


def render_md(model: dict) -> str:
    return "\n\n".join([
        f"# Process map — {model['name']}",
        f"> Generated by the `map-process` skill from [{model['source']}]"
        f"(/{model['source']}). **Regenerate — do not hand-edit.**",
        summary(model),
        "## Flowchart",
        mermaid(model),
        "## Tooling & locus by stage",
        tooling_table(model),
        "## Legend",
        "- **Grey step** — a unit of work. Locus sub-lines: **🏠** the factory tooling it runs "
        "(skill/engine/agent), **📦/🌐** the project / website data it draws on, **👤** if human-led, "
        "then loop scope.\n"
        "- **Green gate** — a machine validator resolves (built).  \n"
        "- **Amber gate** — human-only (no validator yet) — candidate for tooling.  \n"
        "- **Red gate** — an audit flag: a named validator that resolves nowhere, or a doc "
        "status marker that contradicts what exists.",
        "## Cross-check / audit table",
        audit_table(model),
        "",
    ]) + "\n"


def overview_md(models: list[dict]) -> str:
    """Chain run-sheets in order: last gate of each -> first step of the next."""
    out = ["```mermaid", "flowchart TD"]
    for mi, model in enumerate(models):
        slug = f"P{mi}"
        out.append(f'  subgraph {slug}["{_lbl(model["name"])}"]')
        for s in model["steps"]:
            out.append(f'    {slug}_S{s["num"]}["{s["num"]} · {_lbl(s["title"])}"]:::step')
        for i, s in enumerate(model["steps"][:-1]):
            nxt = model["steps"][i + 1]
            out.append(f'    {slug}_S{s["num"]} --> {slug}_S{nxt["num"]}')
        out.append("  end")
    for mi in range(len(models) - 1):
        a, b = models[mi], models[mi + 1]
        out.append(f'  P{mi}_S{a["steps"][-1]["num"]} ==>|outputs feed| P{mi+1}_S{b["steps"][0]["num"]}')
    out.append(CLASSDEFS.rstrip("\n"))
    out.append("```")
    body = "\n".join(out)
    names = " → ".join(m["name"] for m in models)
    return (f"# Factory process — overview\n\n"
            f"> Generated by `map-process`. How the factory's run-sheets chain: **{names}**.\n"
            f"> Each pipeline has its own detailed map (with audit table) alongside this file.\n\n"
            f"{body}\n")


def slugify(path: Path) -> str:
    s = path.stem
    return re.sub(r"^process[-_]", "", s) or s


def main() -> None:
    ap = argparse.ArgumentParser(description="Map a factory run-sheet to a Mermaid process map + audit model.")
    ap.add_argument("runsheets", nargs="+", type=Path, help="run-sheet .md file(s), in pipeline order")
    ap.add_argument("--skills-root", type=Path, default=Path(".claude"),
                    help="root holding skills/ + agents/ (default: .claude)")
    ap.add_argument("--engines-root", type=Path, default=Path("scripts"),
                    help="root holding the engine scripts (default: scripts)")
    ap.add_argument("--out", type=Path, default=Path("docs/process-maps"), help="output directory")
    args = ap.parse_args()

    inv = load_inventory(args.skills_root, args.engines_root)
    args.out.mkdir(parents=True, exist_ok=True)
    models = []
    for rs in args.runsheets:
        model = parse_runsheet(rs)
        model["gates"] = [audit_gate(g, inv) for g in model["gates"]]
        attach_tools(model, inv)
        model.pop("_details", None)
        models.append(model)
        slug = slugify(rs)
        (args.out / f"{slug}.md").write_text(render_md(model), encoding="utf-8")
        (args.out / f"{slug}.json").write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
        flagged = [g for g in model["gates"] if g["cls"] == "flag"]
        print(f"✔ {slug}: {len(model['steps'])} steps, {len(model['gates'])} gates, "
              f"{len(flagged)} flagged → {args.out / (slug + '.md')}")
        for g in flagged:
            print(f"    ⚑ Gate {g['from']}→{g['to']}: {'; '.join(g['flags'])}")
    if len(models) > 1:
        (args.out / "factory-overview.md").write_text(overview_md(models), encoding="utf-8")
        print(f"✔ factory-overview → {args.out / 'factory-overview.md'}")


if __name__ == "__main__":
    main()
