#!/usr/bin/env python3
"""Offline tests for draw-diagram — run with the skill's venv python:

  .claude/skills/draw-diagram/.venv/Scripts/python .claude/skills/draw-diagram/tests.py   (Windows)
  .claude/skills/draw-diagram/.venv/bin/python     .claude/skills/draw-diagram/tests.py   (macOS/Linux)

Covers the stdlib build/parse/geometry helpers and a real Pillow render round-trip. No network.
"""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import draw_diagram as dd

SPEC = {
    "title": "Test net",
    "nodes": [
        {"id": "fw", "label": "Firewall", "row": 1, "col": 1, "fill": "red"},
        {"id": "sw", "label": "Switch", "row": 2, "col": 1, "fill": "blue"},
        {"id": "pc", "label": "PC-1\n10.0.0.11", "row": 3, "col": 0, "fill": "green"},
    ],
    "edges": [
        {"from": "fw", "to": "sw", "label": "LAN"},
        {"from": "sw", "to": "pc", "label": ""},
    ],
}


class TestBuild(unittest.TestCase):
    def test_wellformed_and_counts(self):
        xml = dd.build_drawio(SPEC)
        root = ET.fromstring(xml)  # raises if malformed
        verts = [c for c in root.iter("mxCell") if c.get("vertex") == "1"]
        edges = [c for c in root.iter("mxCell") if c.get("edge") == "1"]
        self.assertEqual(len(verts), 3)
        self.assertEqual(len(edges), 2)

    def test_geometry_from_row_col(self):
        nodes, _ = dd.parse_drawio(dd.build_drawio(SPEC))
        # fw at row 1, col 1
        self.assertEqual(nodes["fw"]["x"], dd.MARGIN + 1 * (dd.W + dd.GX))
        self.assertEqual(nodes["fw"]["y"], dd.MARGIN + 1 * (dd.H + dd.GY))

    def test_auto_stack(self):
        spec = {"nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}], "edges": []}
        nodes, _ = dd.parse_drawio(dd.build_drawio(spec))
        self.assertEqual(nodes["a"]["y"], dd.MARGIN)               # row 0
        self.assertEqual(nodes["b"]["y"], dd.MARGIN + (dd.H + dd.GY))  # row 1


class TestParseRoundTrip(unittest.TestCase):
    def test_nodes_and_edges(self):
        nodes, edges = dd.parse_drawio(dd.build_drawio(SPEC))
        self.assertEqual(set(nodes), {"fw", "sw", "pc"})
        self.assertEqual(nodes["pc"]["label"], "PC-1\n10.0.0.11")   # \n preserved
        e = next(e for e in edges if e["source"] == "fw" and e["target"] == "sw")
        self.assertEqual(e["label"], "LAN")

    def test_fill_resolves(self):
        nodes, _ = dd.parse_drawio(dd.build_drawio(SPEC))
        self.assertEqual(nodes["fw"]["fill"], dd.PALETTE["red"][0])


class TestAnchors(unittest.TestCase):
    def test_build_authors_exit_entry(self):
        # vertical edge fw(row1)->sw(row2): exit bottom-centre, entry top-centre
        xml = dd.build_drawio(SPEC)
        _, edges = dd.parse_drawio(xml)
        e = next(e for e in edges if e["source"] == "fw" and e["target"] == "sw")
        self.assertEqual(e["exit"], (0.5, 1.0, 0.0, 0.0))
        self.assertEqual(e["entry"], (0.5, 0.0, 0.0, 0.0))

    def test_side_dir(self):
        self.assertEqual(dd._side_dir(0.5, 1), "down")
        self.assertEqual(dd._side_dir(0.5, 0), "up")
        self.assertEqual(dd._side_dir(1, 0.5), "right")
        self.assertEqual(dd._side_dir(0, 0.5), "left")

    def test_route_honours_fixed_anchor(self):
        # source above-left of target; force entry on the target's TOP -> last segment travels down
        a = {"x": 0, "y": 0, "w": 200, "h": 70}
        b = {"x": 300, "y": 300, "w": 200, "h": 70}
        edge = {"exit": (0.5, 1.0, 0.0, 0.0), "entry": (0.5, 0.0, 0.0, 0.0), "waypoints": []}
        pts, arrow = dd._edge_route(a, b, edge)
        self.assertEqual(arrow, "down")                     # enters the top, pointing down
        self.assertEqual(pts[0], (100.0, 70.0))             # exit bottom-centre of a
        self.assertEqual(pts[-1], (400.0, 300.0))           # entry top-centre of b

    def test_route_side_entry(self):
        # entry on the target's LEFT -> last segment travels right into it
        a = {"x": 0, "y": 0, "w": 200, "h": 70}
        b = {"x": 300, "y": 0, "w": 200, "h": 70}
        edge = {"exit": (1.0, 0.5, 0.0, 0.0), "entry": (0.0, 0.5, 0.0, 0.0), "waypoints": []}
        pts, arrow = dd._edge_route(a, b, edge)
        self.assertEqual(arrow, "right")
        self.assertEqual(pts[-1], (300.0, 35.0))            # left-centre of b

    def test_route_honours_waypoints(self):
        a = {"x": 0, "y": 0, "w": 200, "h": 70}
        b = {"x": 0, "y": 300, "w": 200, "h": 70}
        edge = {"exit": (0.5, 1.0, 0.0, 0.0), "entry": (0.5, 0.0, 0.0, 0.0),
                "waypoints": [(100.0, 150.0)]}
        pts, _ = dd._edge_route(a, b, edge)
        self.assertIn((100.0, 150.0), pts)

    def test_floating_fallback_when_no_anchor(self):
        # no anchors -> dominant-direction floating: vertical pair feeds bottom->top
        a = {"x": 0, "y": 0, "w": 200, "h": 70}
        b = {"x": 0, "y": 300, "w": 200, "h": 70}
        edge = {"exit": None, "entry": None, "waypoints": []}
        pts, arrow = dd._edge_route(a, b, edge)
        self.assertEqual(arrow, "down")
        self.assertEqual(pts[0], (100.0, 70.0))


class TestShapes(unittest.TestCase):
    def test_shape_round_trip(self):
        spec = {"nodes": [
            {"id": "s", "label": "Start", "row": 0, "col": 0, "shape": "stadium"},
            {"id": "d", "label": "OK?",   "row": 1, "col": 0, "shape": "diamond"},
            {"id": "p", "label": "Do it", "row": 2, "col": 0, "shape": "rect"},
            {"id": "e", "label": "Entity\nid\nname", "row": 0, "col": 1, "shape": "entity",
             "w": 200, "h": 120},
        ], "edges": [{"from": "s", "to": "d"}, {"from": "d", "to": "p", "label": "yes"}]}
        nodes, _ = dd.parse_drawio(dd.build_drawio(spec))
        self.assertEqual(nodes["s"]["shape"], "stadium")
        self.assertEqual(nodes["d"]["shape"], "diamond")
        self.assertEqual(nodes["p"]["shape"], "rect")
        self.assertEqual(nodes["e"]["shape"], "entity")
        self.assertEqual(nodes["e"]["h"], 120.0)          # per-node size honoured

    def test_default_shape_is_rounded(self):
        nodes, _ = dd.parse_drawio(dd.build_drawio(SPEC))
        self.assertEqual(nodes["fw"]["shape"], "rounded")


class TestCrowsFoot(unittest.TestCase):
    def test_er_markers_round_trip(self):
        spec = {"nodes": [{"id": "a", "label": "A", "row": 0, "col": 0, "shape": "entity"},
                          {"id": "b", "label": "B", "row": 0, "col": 1, "shape": "entity"}],
                "edges": [{"from": "a", "to": "b", "start": "one", "end": "many"}]}
        xml = dd.build_drawio(spec)
        self.assertIn("startArrow=ERone", xml)
        self.assertIn("endArrow=ERmany", xml)
        _, edges = dd.parse_drawio(xml)
        self.assertEqual(edges[0]["start_marker"], "one")
        self.assertEqual(edges[0]["end_marker"], "many")

    def test_plain_edge_has_no_er_markers(self):
        _, edges = dd.parse_drawio(dd.build_drawio(SPEC))
        self.assertIsNone(edges[0]["start_marker"])
        self.assertIsNone(edges[0]["end_marker"])


class TestRender(unittest.TestCase):
    def test_render_produces_png(self):
        nodes, edges = dd.parse_drawio(dd.build_drawio(SPEC))
        img = dd.render(nodes, edges, scale=2)
        w = int(max(n["x"] + n["w"] for n in nodes.values()) + dd.MARGIN) * 2
        h = int(max(n["y"] + n["h"] for n in nodes.values()) + dd.MARGIN) * 2
        self.assertEqual(img.size, (w, h))

    def test_render_drawio_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            drawio = dd.save_drawio(dd.build_drawio(SPEC), Path(d) / "t.drawio")
            png = dd.render_drawio(drawio)
            self.assertTrue(png.is_file())
            from PIL import Image
            with Image.open(png) as im:
                self.assertGreater(im.size[0], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
