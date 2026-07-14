#!/usr/bin/env python3
"""Offline stdlib tests for map-process. No network. Run: `python3 tests.py`.

Covers the run-sheet parser, the inventory + name resolver, the gate cross-check/audit, data
harvesting/locus tagging, slugify, and an end-to-end render of a small synthetic run-sheet.
"""
import json
import tempfile
import unittest
from pathlib import Path

import map_process as mp

RUNSHEET = """# Widget factory

**1 · `brief-widget` — Brief the widget** *(once per widget)*
Draft the brief; draws on `spec.md` and `catalogue.json`.
> **⟱ Gate 1→2:** *validator* — `brief-linter` (0 errors) **+ human review**. built

**2 · Assemble by hand**
A human assembles it.
> **⟱ Gate 2→3:** *human review*.

**3 · `ship-widget` — Ship the widget**
Ship it via `ship_engine`.
> **⟱ Gate 3→done:** *validator* — `validate-ship`. to build
"""


def write_runsheet(d: Path) -> Path:
    p = d / "process-widget.md"
    p.write_text(RUNSHEET, encoding="utf-8")
    return p


class Classifiers(unittest.TestCase):
    def test_status(self):
        self.assertEqual(mp._status("… to build"), "planned")
        self.assertEqual(mp._status("already built"), "built")
        self.assertIsNone(mp._status("nothing here"))

    def test_gate_kind(self):
        self.assertEqual(mp._gate_kind("*validator* — `x`"), "validator")
        self.assertEqual(mp._gate_kind("*human review*"), "human")
        self.assertEqual(mp._gate_kind("something else"), "other")


class ParseRunsheet(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.model = mp.parse_runsheet(write_runsheet(Path(self._tmp.name)))

    def tearDown(self):
        self._tmp.cleanup()

    def test_name_from_h1(self):
        self.assertEqual(self.model["name"], "Widget factory")

    def test_steps(self):
        steps = self.model["steps"]
        self.assertEqual([s["num"] for s in steps], ["1", "2", "3"])
        self.assertEqual(steps[0]["skill"], "brief-widget")
        self.assertEqual(steps[0]["title"], "Brief the widget")
        self.assertEqual(steps[0]["scope"], "once per widget")
        self.assertIsNone(steps[1]["skill"])          # human-led step, no backticked skill
        self.assertEqual(steps[1]["title"], "Assemble by hand")

    def test_gates(self):
        gates = self.model["gates"]
        self.assertEqual([(g["from"], g["to"]) for g in gates], [("1", "2"), ("2", "3"), ("3", "done")])
        self.assertEqual(gates[0]["kind"], "validator")
        self.assertEqual(gates[0]["names"], ["brief-linter"])
        self.assertTrue(gates[0]["human"])
        self.assertEqual(gates[0]["status"], "built")
        self.assertEqual(gates[1]["kind"], "human")
        self.assertEqual(gates[2]["status"], "planned")


class Inventory(unittest.TestCase):
    def test_load_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "skills" / "brief-widget").mkdir(parents=True)
            (root / "skills" / "scripts").mkdir(parents=True)
            (root / "skills" / "scripts" / "ship_linter.py").write_text("")
            (root / "agents").mkdir()
            (root / "agents" / "widget-auditor.md").write_text("")
            engines = root / "engines"
            engines.mkdir()
            (engines / "ship_engine.py").write_text("")
            inv = mp.load_inventory(root, engines)
            self.assertIn("brief-widget", inv["skills"])
            self.assertNotIn("scripts", inv["skills"])       # scripts/ dir is excluded from skills
            self.assertIn("ship_linter", inv["scripts"])
            self.assertIn("widget-auditor", inv["agents"])
            self.assertIn("ship_engine", inv["engines"])


class Resolve(unittest.TestCase):
    INV = {"skills": {"brief-linter"}, "scripts": {"ship_linter"},
           "agents": {"widget-auditor"}, "engines": {"kangan_deck"}}

    def test_kebab_skill(self):
        self.assertEqual(mp.resolve("brief-linter", self.INV), ("skill", "brief-linter"))

    def test_snake_script_from_kebab(self):
        self.assertEqual(mp.resolve("ship-linter", self.INV), ("script", "ship_linter"))

    def test_agent_suffix(self):
        self.assertEqual(mp.resolve("widget-auditor agent", self.INV), ("agent", "widget-auditor"))

    def test_engine(self):
        self.assertEqual(mp.resolve("kangan-deck", self.INV), ("engine", "kangan_deck"))

    def test_mcp(self):
        self.assertEqual(mp.resolve("mcp__slack__send", self.INV), ("mcp", "mcp__slack__send"))

    def test_unresolved(self):
        self.assertIsNone(mp.resolve("nope-nothing", self.INV))


class AuditGate(unittest.TestCase):
    INV = {"skills": {"brief-linter"}, "scripts": set(), "agents": set(), "engines": set()}

    def test_resolvable_validator_is_built(self):
        g = {"from": "1", "to": "2", "label": None, "kind": "validator",
             "names": ["brief-linter"], "human": True, "status": "built"}
        a = mp.audit_gate(g, self.INV)
        self.assertTrue(a["implemented"])
        self.assertEqual(a["flags"], [])
        self.assertEqual(a["cls"], "built")

    def test_unresolvable_validator_flags(self):
        g = {"from": "1", "to": "2", "label": None, "kind": "validator",
             "names": ["validate-missing"], "human": False, "status": None}
        a = mp.audit_gate(g, self.INV)
        self.assertFalse(a["implemented"])
        self.assertEqual(a["cls"], "flag")
        self.assertTrue(any("no skill/script" in f for f in a["flags"]))

    def test_human_gate_is_candidate(self):
        g = {"from": "2", "to": "3", "label": None, "kind": "human",
             "names": [], "human": True, "status": None}
        a = mp.audit_gate(g, self.INV)
        self.assertEqual(a["cls"], "human")
        self.assertTrue(any("candidate for tooling" in f for f in a["flags"]))

    def test_stale_doc_flag(self):
        g = {"from": "3", "to": "4", "label": None, "kind": "validator",
             "names": ["brief-linter"], "human": False, "status": "planned"}
        a = mp.audit_gate(g, self.INV)
        self.assertTrue(any("stale doc" in f for f in a["flags"]))
        self.assertEqual(a["cls"], "flag")


class HarvestData(unittest.TestCase):
    def test_locus_tagging_and_skips(self):
        inv = {"skills": set(), "scripts": set(), "agents": set(), "engines": set()}
        text = "draws on `spec.md`, `page.astro`, `build.py`, and a bare `.docx`"
        data = mp.harvest_data(text, inv)
        by = {d["name"]: d["locus"] for d in data}
        self.assertEqual(by.get("spec.md"), "subrepo")
        self.assertEqual(by.get("page.astro"), "website")
        self.assertNotIn("build.py", by)          # .py is tooling, not data
        self.assertNotIn(".docx", by)             # bare extension, not a concrete artefact


class Slugify(unittest.TestCase):
    def test_strips_process_prefix(self):
        self.assertEqual(mp.slugify(Path("docs/process-delivery.md")), "delivery")
        self.assertEqual(mp.slugify(Path("run-sheet.md")), "run-sheet")


class EndToEnd(unittest.TestCase):
    def test_render_and_model(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            rs = write_runsheet(d)
            # inventory that resolves the first gate's validator but not the last
            (d / "skills" / "brief-linter").mkdir(parents=True)
            (d / "skills" / "scripts").mkdir(parents=True)
            (d / "agents").mkdir()
            inv = mp.load_inventory(d, d / "engines")

            model = mp.parse_runsheet(rs)
            model["gates"] = [mp.audit_gate(g, inv) for g in model["gates"]]
            mp.attach_tools(model, inv)
            model.pop("_details", None)

            md = mp.render_md(model)
            self.assertIn("```mermaid", md)
            self.assertIn("Cross-check / audit table", md)
            self.assertIn("Factory tooling", md)          # genericised label
            # JSON model must be serialisable and carry the audited gates
            blob = json.loads(json.dumps(model))
            self.assertEqual(len(blob["steps"]), 3)
            self.assertEqual(blob["gates"][0]["cls"], "built")
            self.assertEqual(blob["gates"][2]["cls"], "flag")   # validate-ship named but unresolved


if __name__ == "__main__":
    unittest.main(verbosity=2)
