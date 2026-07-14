#!/usr/bin/env python3
"""draw-diagram — author an editable draw.io (.drawio) technical diagram from a simple spec, then
render it to PNG with Pillow (no draw.io app, no system binary; same input -> same pixels).

The .drawio is the single source of truth: anyone can open and edit it in draw.io (free), and a
re-render reflects light edits. The renderer understands the box / container / arrow / label subset
this skill authors — enough for a network / cloud-architecture diagram, a flowchart, or a simple ERD;
it is not a general draw.io renderer.

Spec (a dict / JSON):
  {
    "title": "Security-group chain",
    "nodes": [
      {"id": "alb", "label": "sg-alb\\n443 from staff CIDR", "row": 0, "col": 0, "fill": "blue"},
      {"id": "app", "label": "sg-app",                        "row": 1, "col": 0, "fill": "green"},
      {"id": "db",  "label": "sg-db",                         "row": 2, "col": 0, "fill": "amber"}
    ],
    "edges": [
      {"from": "alb", "to": "app", "label": "to sg-app"},
      {"from": "app", "to": "db",  "label": "SQL to sg-db"}
    ]
  }
Nodes lay out on a grid by (row, col); a node missing row/col auto-stacks. `fill` is a palette name
(blue/green/amber/grey/purple/red) or a #hex. Optional per-node `shape` (rounded [default] / rect /
ellipse / stadium / diamond / entity) and `w`/`h` size override let one spec express a network, a
flowchart (stadium terminators + decision diamonds), or a simple ERD (entity = name then attributes,
left/top-aligned). Edge geometry honours any fixed exit/entry ports and waypoints in the .drawio, so a
hand-edited diagram re-renders true to source; authored edges get explicit ports for draw.io<->Pillow
parity. Optional per-edge `start`/`end` crow's-foot endings (one/many/zero-one/zero-many/one-many) for
ERDs, authored as draw.io's native ER arrows and drawn as matching glyphs in the render.

CLI (run with the skill's venv python — see SKILL.md):
  python draw_diagram.py --spec spec.json --out diagram.drawio --png [diagram.png]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit(
        "ERROR: Pillow is required for the draw-diagram skill but is not installed.\n"
        "Set up the skill's virtualenv (see .claude/skills/draw-diagram/SKILL.md), then run via that python:\n"
        "  python -m venv .claude/skills/draw-diagram/.venv\n"
        "  .claude/skills/draw-diagram/.venv/Scripts/python -m pip install -r .claude/skills/draw-diagram/requirements.txt   (Windows)\n"
        "  .claude/skills/draw-diagram/.venv/bin/python   -m pip install -r .claude/skills/draw-diagram/requirements.txt   (macOS/Linux)"
    )

# box + grid geometry (draw.io points)
W, H, GX, GY, MARGIN = 200, 70, 80, 70, 40

PALETTE = {  # name -> (fill, stroke)
    "blue":   ("#dae8fc", "#6c8ebf"),
    "green":  ("#d5e8d4", "#82b366"),
    "amber":  ("#ffe6cc", "#d79b00"),
    "grey":   ("#f5f5f5", "#666666"),
    "purple": ("#e1d5e7", "#9673a6"),
    "red":    ("#f8cecc", "#b85450"),
}

# Crow's-foot (ER) edge endings: our kind -> draw.io's built-in ER arrow style (and back).
ER_ARROWS = {
    "one": "ERone", "many": "ERmany", "zero-one": "ERzeroToOne",
    "zero-many": "ERzeroToMany", "one-many": "ERoneToMany",
}
ER_FROM_STYLE = {v: k for k, v in ER_ARROWS.items()}


def _fill(name):
    if not name:
        return PALETTE["grey"]
    if str(name).startswith("#"):
        return (name, "#444444")
    return PALETTE.get(name, PALETTE["grey"])


# Shapes this skill authors. Each maps to a draw.io style and a Pillow draw path; both sides agree.
#   rounded (default) / rect — boxes        ellipse / stadium — flowchart terminators
#   diamond — flowchart decision            entity — ER entity (left/top-aligned: name then attrs)
def _node_style(shape, fill, stroke):
    base = f"whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize=14;"
    if shape == "diamond":
        return "rhombus;" + base + "align=center;verticalAlign=middle;"
    if shape == "ellipse":
        return "ellipse;" + base + "align=center;verticalAlign=middle;"
    if shape == "stadium":
        return "rounded=1;arcSize=50;" + base + "align=center;verticalAlign=middle;"
    if shape == "entity":
        return "rounded=0;" + base + "align=left;verticalAlign=top;spacingLeft=6;spacingTop=6;"
    if shape == "rect":
        return "rounded=0;" + base + "align=center;verticalAlign=middle;"
    return "rounded=1;" + base + "align=center;verticalAlign=middle;"   # rounded (default)


def _shape_from_style(style):
    style = style or ""
    if "rhombus" in style:
        return "diamond"
    if "ellipse" in style:
        return "ellipse"
    arc = _style_get(style, "arcSize")
    if _style_get(style, "rounded") == "1" and arc and float(arc) >= 40:
        return "stadium"
    if _style_get(style, "align") == "left" and _style_get(style, "verticalAlign") == "top":
        return "entity"
    if _style_get(style, "rounded") == "1":
        return "rounded"
    return "rect"


# --- author the .drawio (stdlib) ---------------------------------------------
def build_drawio(spec: dict) -> str:
    nodes = spec.get("nodes", [])
    edges = spec.get("edges", [])
    auto = 0
    for n in nodes:
        if "row" not in n or "col" not in n:
            n.setdefault("row", auto)
            n.setdefault("col", 0)
            auto += 1
    cells = []
    pos = {}                                  # id -> (x, y, w, h) for edge anchoring
    # Grid pitch fits the largest node so tall/wide nodes (e.g. ER entities) don't collide; for
    # uniform diagrams this is exactly (W+GX, H+GY), leaving network/flowchart layouts unchanged.
    pitch_x = max((n.get("w", W) for n in nodes), default=W) + GX
    pitch_y = max((n.get("h", H) for n in nodes), default=H) + GY
    for n in nodes:
        fill, stroke = _fill(n.get("fill"))
        w, h = n.get("w", W), n.get("h", H)
        x = MARGIN + n["col"] * pitch_x
        y = MARGIN + n["row"] * pitch_y
        pos[n["id"]] = (x, y, w, h)
        label = escape(str(n.get("label", n["id"]))).replace("\\n", "&#10;").replace("\n", "&#10;")
        style = _node_style(n.get("shape"), fill, stroke)
        cells.append(
            f'<mxCell id="{escape(str(n["id"]))}" value="{label}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
    for i, e in enumerate(edges):
        label = escape(str(e.get("label", "")))
        start, end = e.get("start"), e.get("end")
        if start or end:                          # crow's-foot (ER) endings
            style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;fontSize=12;"
                     f"startArrow={ER_ARROWS.get(start, 'none')};endArrow={ER_ARROWS.get(end, 'none')};"
                     "startFill=0;endFill=0;")
        else:
            style = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;fontSize=12;"
        # Author explicit exit/entry ports so the edge geometry is deterministic in BOTH draw.io and
        # the Pillow renderer (no reliance on either side's floating auto-router).
        src, tgt = pos.get(e["from"]), pos.get(e["to"])
        if src and tgt:
            a = {"x": src[0], "y": src[1], "w": src[2], "h": src[3]}
            b = {"x": tgt[0], "y": tgt[1], "w": tgt[2], "h": tgt[3]}
            (sx, sy), (tx, ty) = _float_anchors(a, b)
            style += (f"exitX={sx};exitY={sy};exitDx=0;exitDy=0;"
                      f"entryX={tx};entryY={ty};entryDx=0;entryDy=0;")
        cells.append(
            f'<mxCell id="e{i}" value="{label}" style="{style}" edge="1" parent="1" '
            f'source="{escape(str(e["from"]))}" target="{escape(str(e["to"]))}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    name = escape(str(spec.get("title", "Diagram")))
    body = "".join(cells)
    return (
        '<mxfile host="draw-diagram">'
        f'<diagram id="d1" name="{name}">'
        '<mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" '
        'connect="1" arrows="1" fold="1" page="1" pageScale="1" math="0" shadow="0">'
        f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root>'
        "</mxGraphModel></diagram></mxfile>"
    )


def save_drawio(xml: str, path: Path) -> Path:
    path = Path(path)
    path.write_text(xml, encoding="utf-8")
    ET.fromstring(xml)  # well-formedness guard
    return path


# --- parse the .drawio subset we author --------------------------------------
def _style_get(style: str, key: str, default=None):
    m = re.search(rf"{key}=([^;]+)", style or "")
    return m.group(1) if m else default


def _anchor_from_style(style: str, kind: str):
    """Read a fixed connection point from an edge style. kind is 'exit' or 'entry'.

    draw.io writes exitX/exitY (+exitDx/exitDy pixel offsets), normalized [0,1] on the source box,
    and entryX/entryY on the target, whenever an arrow is attached to a specific port. Returns
    (nx, ny, dx, dy) or None when the edge floats (no fixed point)."""
    x, y = _style_get(style, kind + "X"), _style_get(style, kind + "Y")
    if x is None or y is None:
        return None
    return (float(x), float(y),
            float(_style_get(style, kind + "Dx", "0")), float(_style_get(style, kind + "Dy", "0")))


def parse_drawio(xml: str):
    """Return (nodes, edges) for the box/edge subset. nodes: id->dict; edges: list of dicts.

    Each edge carries any fixed `exit`/`entry` anchors and explicit `waypoints` it was authored or
    hand-drawn with, so the renderer reproduces the geometry the .drawio actually specifies rather
    than re-guessing it from box centres."""
    root = ET.fromstring(xml)
    nodes, edges = {}, []
    for cell in root.iter("mxCell"):
        if cell.get("vertex") == "1":
            geo = cell.find("mxGeometry")
            nodes[cell.get("id")] = {
                "label": (cell.get("value") or "").replace("&#10;", "\n").replace("\\n", "\n"),
                "x": float(geo.get("x", 0)), "y": float(geo.get("y", 0)),
                "w": float(geo.get("width", W)), "h": float(geo.get("height", H)),
                "fill": _style_get(cell.get("style"), "fillColor", "#f5f5f5"),
                "stroke": _style_get(cell.get("style"), "strokeColor", "#444444"),
                "shape": _shape_from_style(cell.get("style")),
            }
        elif cell.get("edge") == "1":
            style = cell.get("style")
            waypoints = []
            geo = cell.find("mxGeometry")
            arr = geo.find("Array") if geo is not None else None
            if arr is not None:
                for p in arr.findall("mxPoint"):
                    waypoints.append((float(p.get("x", 0)), float(p.get("y", 0))))
            edges.append({"source": cell.get("source"), "target": cell.get("target"),
                          "label": cell.get("value") or "",
                          "exit": _anchor_from_style(style, "exit"),
                          "entry": _anchor_from_style(style, "entry"),
                          "start_marker": ER_FROM_STYLE.get(_style_get(style, "startArrow")),
                          "end_marker": ER_FROM_STYLE.get(_style_get(style, "endArrow")),
                          "waypoints": waypoints})
    return nodes, edges


# --- render with Pillow ------------------------------------------------------
def _font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)   # Pillow >= 10.1: scalable default
    except TypeError:
        return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    out = []
    for raw in text.split("\n"):
        words, line = raw.split(" "), ""
        for wd in words:
            trial = (line + " " + wd).strip()
            if draw.textlength(trial, font=font) <= max_w or not line:
                line = trial
            else:
                out.append(line)
                line = wd
        out.append(line)
    return out


def _float_anchors(a, b):
    """Floating fallback: normalized (exit, entry) ports for an edge a->b. Prefer top/bottom ports
    whenever the boxes sit on different levels (vertical centres more than half a box apart) — this
    feeds a hierarchy/tree from the top like draw.io's router and reads cleaner than side entry; fall
    back to left/right ports only for same-level (side-by-side) peers."""
    acy, bcy = a["y"] + a["h"] / 2, b["y"] + b["h"] / 2
    bcx = b["x"] + b["w"] / 2
    acx = a["x"] + a["w"] / 2
    if abs(bcy - acy) > a["h"] / 2:                      # different level -> vertical ports
        return ((0.5, 1), (0.5, 0)) if bcy >= acy else ((0.5, 0), (0.5, 1))
    return ((1, 0.5), (0, 0.5)) if bcx >= acx else ((0, 0.5), (1, 0.5))  # same level -> horizontal


def _side_dir(nx, ny):
    """Outward border direction for a normalized anchor (nearest border; handles interior points)."""
    return min((("left", nx), ("right", 1 - nx), ("up", ny), ("down", 1 - ny)),
               key=lambda c: c[1])[0]


def _pt(node, nx, ny, dx=0.0, dy=0.0):
    return (node["x"] + nx * node["w"] + dx, node["y"] + ny * node["h"] + dy)


def _arrow_dir(p_prev, p_end):
    (x0, y0), (x1, y1) = p_prev, p_end
    if abs(x1 - x0) >= abs(y1 - y0):
        return "right" if x1 >= x0 else "left"
    return "down" if y1 >= y0 else "up"


def _edge_route(a, b, edge):
    """Build the orthogonal polyline for an edge, honouring fixed exit/entry anchors and explicit
    waypoints from the .drawio; falls back to the floating heuristic only where an anchor is absent.
    Returns (points, arrow_dir)."""
    f_exit, f_entry = _float_anchors(a, b)
    ex = edge.get("exit") or (f_exit[0], f_exit[1], 0.0, 0.0)
    en = edge.get("entry") or (f_entry[0], f_entry[1], 0.0, 0.0)
    s = _pt(a, ex[0], ex[1], ex[2], ex[3])
    t = _pt(b, en[0], en[1], en[2], en[3])
    es, ee = _side_dir(ex[0], ex[1]), _side_dir(en[0], en[1])

    wpts = edge.get("waypoints") or []
    if wpts:
        pts = [s, *wpts, t]
    else:
        exit_v = es in ("up", "down")
        entry_v = ee in ("up", "down")
        if exit_v and entry_v:                       # opposing vertical sides -> Z through mid-y
            my = (s[1] + t[1]) / 2
            pts = [s, (s[0], my), (t[0], my), t]
        elif not exit_v and not entry_v:             # opposing horizontal sides -> Z through mid-x
            mx = (s[0] + t[0]) / 2
            pts = [s, (mx, s[1]), (mx, t[1]), t]
        elif exit_v:                                 # vertical out, horizontal in -> single corner
            pts = [s, (s[0], t[1]), t]
        else:                                        # horizontal out, vertical in -> single corner
            pts = [s, (t[0], s[1]), t]

    clean = [pts[0]]
    for p in pts[1:]:
        if p != clean[-1]:
            clean.append(p)
    arrow = _arrow_dir(clean[-2], clean[-1]) if len(clean) >= 2 else "down"
    return clean, arrow


def _unit(p_from, p_to):
    dx, dy = p_to[0] - p_from[0], p_to[1] - p_from[1]
    n = (dx * dx + dy * dy) ** 0.5 or 1.0
    return dx / n, dy / n


def _er_marker(d, p_box, p_in, kind, S, color):
    """Draw a crow's-foot ER ending at p_box. p_in is the next polyline point inward, used to orient
    the glyph. `back` points away from the box along the line; `perp` is across it."""
    bx, by = _unit(p_box, p_in)                       # away from box, along the line
    px, py = -by, bx
    P = (p_box[0] * S, p_box[1] * S)
    lw = max(2, S)
    FD, HS, BO, CR = 13 * S, 7 * S, 11 * S, 4 * S     # foot depth, half-spread, bar offset, circ radius

    def at(along, across):
        return (P[0] + bx * along + px * across, P[1] + by * along + py * across)

    def foot():                                       # two splayed tines -> "many"
        apex = at(FD, 0)
        d.line([apex, at(0, HS)], fill=color, width=lw)
        d.line([apex, at(0, -HS)], fill=color, width=lw)

    def bar(off):                                     # perpendicular tick -> "one"
        d.line([at(off, HS), at(off, -HS)], fill=color, width=lw)

    def circ(off):                                    # open circle -> "zero" (optional)
        c = at(off, 0)
        d.ellipse([c[0] - CR, c[1] - CR, c[0] + CR, c[1] + CR], outline=color, fill="white", width=lw)

    if kind == "one":
        bar(BO)
    elif kind == "many":
        foot()
    elif kind == "zero-one":
        bar(BO); circ(BO + 2 * CR + 3 * S)
    elif kind == "one-many":
        foot(); bar(FD + 5 * S)
    elif kind == "zero-many":
        foot(); circ(FD + 2 * CR + 5 * S)


def render(nodes: dict, edges: list, scale: int = 2) -> "Image.Image":
    width = int(max((n["x"] + n["w"] for n in nodes.values()), default=W) + MARGIN)
    height = int(max((n["y"] + n["h"] for n in nodes.values()), default=H) + MARGIN)
    img = Image.new("RGB", (width * scale, height * scale), "white")
    d = ImageDraw.Draw(img)
    S = scale
    body_font = _font(14 * S)
    edge_font = _font(12 * S)

    # edges first (behind boxes)
    for e in edges:
        a, b = nodes.get(e["source"]), nodes.get(e["target"])
        if not a or not b:
            continue
        pts, dirn = _edge_route(a, b, e)
        d.line([(p[0] * S, p[1] * S) for p in pts], fill="#444444", width=max(2, S))
        # endings: a crow's-foot ER marker (if set) replaces the block arrowhead at that end
        if e.get("end_marker"):
            _er_marker(d, pts[-1], pts[-2], e["end_marker"], S, "#444444")
        else:
            ex, ey = pts[-1]
            ah = 8 * S
            if dirn == "down":
                head = [(ex * S, ey * S), (ex * S - ah / 2, ey * S - ah), (ex * S + ah / 2, ey * S - ah)]
            elif dirn == "up":
                head = [(ex * S, ey * S), (ex * S - ah / 2, ey * S + ah), (ex * S + ah / 2, ey * S + ah)]
            elif dirn == "right":
                head = [(ex * S, ey * S), (ex * S - ah, ey * S - ah / 2), (ex * S - ah, ey * S + ah / 2)]
            else:
                head = [(ex * S, ey * S), (ex * S + ah, ey * S - ah / 2), (ex * S + ah, ey * S + ah / 2)]
            d.polygon(head, fill="#444444")
        if e.get("start_marker"):
            _er_marker(d, pts[0], pts[1], e["start_marker"], S, "#444444")
        if e["label"]:
            mid = pts[len(pts) // 2]
            d.text((mid[0] * S + 4 * S, mid[1] * S - 16 * S), e["label"], fill="#333333", font=edge_font)

    # boxes + labels on top
    for n in nodes.values():
        x0, y0 = n["x"] * S, n["y"] * S
        x1, y1 = (n["x"] + n["w"]) * S, (n["y"] + n["h"]) * S
        fill, stroke, shape = n["fill"], n["stroke"], n.get("shape", "rounded")
        lw = max(2, S)
        if shape == "diamond":
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            poly = [(mx, y0), (x1, my), (mx, y1), (x0, my)]
            d.polygon(poly, fill=fill)
            d.line(poly + [poly[0]], fill=stroke, width=lw)
        elif shape == "ellipse":
            d.ellipse([x0, y0, x1, y1], fill=fill, outline=stroke, width=lw)
        elif shape == "stadium":
            d.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) / 2, fill=fill, outline=stroke, width=lw)
        elif shape in ("rect", "entity"):
            d.rectangle([x0, y0, x1, y1], fill=fill, outline=stroke, width=lw)
        else:
            d.rounded_rectangle([x0, y0, x1, y1], radius=8 * S, fill=fill, outline=stroke, width=lw)

        lines = _wrap(d, n["label"], body_font, n["w"] * S - 12 * S)
        lh = (body_font.getbbox("Ay")[3] - body_font.getbbox("Ay")[1]) + 4 * S
        if shape == "entity":                            # name then attributes, left/top-aligned
            tx, ty = x0 + 6 * S, y0 + 6 * S
            for ln in lines:
                d.text((tx, ty), ln, fill="#222222", font=body_font)
                ty += lh
        else:
            ty = (y0 + y1) / 2 - (len(lines) * lh) / 2
            for ln in lines:
                tw = d.textlength(ln, font=body_font)
                d.text(((x0 + x1) / 2 - tw / 2, ty), ln, fill="#222222", font=body_font)
                ty += lh
    return img


def render_drawio(drawio_path, png_path=None, scale: int = 2) -> Path:
    drawio_path = Path(drawio_path)
    png_path = Path(png_path) if png_path else drawio_path.with_suffix(".png")
    nodes, edges = parse_drawio(drawio_path.read_text(encoding="utf-8"))
    img = render(nodes, edges, scale=scale)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(png_path, "PNG", dpi=(150 * scale, 150 * scale))
    return png_path


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Author a .drawio from a spec and render it to PNG (Pillow).")
    ap.add_argument("--spec", required=True, help="path to a JSON spec")
    ap.add_argument("--out", required=True, help="output .drawio path")
    ap.add_argument("--png", nargs="?", const=True, default=False,
                    help="also render a PNG (optional path; defaults next to the .drawio)")
    args = ap.parse_args(argv)

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    out = save_drawio(build_drawio(spec), Path(args.out))
    print(f"wrote {out}")
    if args.png:
        png = render_drawio(out, None if args.png is True else Path(args.png))
        print(f"rendered {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
