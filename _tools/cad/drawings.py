"""
Compose orthographic drawing sheets for the dispenser from the CAD model.

Each view is projected out of the solid model (visible + hidden lines), then
the views are laid out on a sheet with a title block, view labels and a
section line. Writes SVG, so the drawings stay crisp on the website.
"""
import os
import re
import math
import cadquery as cq
from cadquery import exporters

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "drawings")
os.makedirs(OUT, exist_ok=True)

import dispenser as D  # builds the parts

INK = "#14213D"
HID = "#9FB0C6"
ACC = "#00796B"
LINE = "#C9D4E2"


def upright(shape):
    """cadquery's SVG export lays the model's Z across the sheet; turn it so
    the device stands up in the view, the way a drawing expects."""
    return shape.rotate((0, 0, 0), (0, 1, 0), -90)


PRE = {"front": None, "right": ((0, 0, 1), 90), "top": ((1, 0, 0), 90)}


def project(shape, view="front", px=560, hidden=True):
    """Export one orthographic view and return its inner <g> markup.

    Every view is the FRONT projection of the model turned into place first,
    which keeps the sheet's up direction consistent across the three views.
    """
    pre = PRE[view]
    if pre:
        shape = shape.rotate((0, 0, 0), pre[0], pre[1])
    shape = upright(shape)
    direction = (0, -1, 0)
    tmp = os.path.join(OUT, "_tmp.svg")
    exporters.export(shape, tmp, exportType="SVG", opt={
        "width": px, "height": px, "marginLeft": 12, "marginTop": 12,
        "projectionDir": direction, "showAxes": False,
        "strokeWidth": 0.30, "strokeColor": (20, 33, 61),
        "hiddenColor": (159, 176, 198), "showHidden": hidden,
    })
    svg = open(tmp).read()
    inner = svg[svg.index("<g "):svg.rindex("</g>") + 4]
    os.remove(tmp)
    return inner


def assembly(parts):
    s = None
    for p in parts:
        s = p if s is None else s.union(p)
    return s


FULL = assembly([D.shell_front, D.shell_back, D.carousel, D.ratchet, D.cam,
                 D.plunger, D.lever, D.pcb])
CUT = assembly([D.shell_front.cut(D.cutter), D.shell_back.cut(D.cutter),
                D.carousel, D.ratchet, D.cam, D.plunger, D.airway, D.lever, D.pcb])
MECH = assembly([D.carousel, D.ratchet, D.cam, D.plunger, D.airway])


def sheet(name, title, views=(), w=1500, h=760, notes=()):
    """views: list of (label, markup, x, y, scale)"""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" font-family="ui-monospace, Menlo, monospace">',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>',
        f'<rect x="14" y="14" width="{w-28}" height="{h-28}" fill="none" stroke="{LINE}" stroke-width="1.4"/>',
    ]
    for label, markup, x, y, sc in views:
        parts.append(f'<g transform="translate({x},{y}) scale({sc})">{markup}</g>')
        parts.append(f'<text x="{x}" y="{y - 14}" font-size="15" fill="{ACC}" '
                     f'letter-spacing="1.5">{label}</text>')
    # title block
    bx, by, bw, bh = w - 474, h - 136, 460, 122
    parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="none" '
                 f'stroke="{LINE}" stroke-width="1.4"/>')
    parts.append(f'<line x1="{bx}" y1="{by+46}" x2="{bx+bw}" y2="{by+46}" stroke="{LINE}" stroke-width="1"/>')
    parts.append(f'<line x1="{bx+300}" y1="{by}" x2="{bx+300}" y2="{by+bh}" stroke="{LINE}" stroke-width="1"/>')
    parts.append(f'<text x="{bx+16}" y="{by+30}" font-size="19" fill="{INK}">{title}</text>')
    parts.append(f'<text x="{bx+16}" y="{by+72}" font-size="12.5" fill="#64708A">'
                 f'Stepwise-Dosing Nicotine Dispenser</text>')
    parts.append(f'<text x="{bx+16}" y="{by+96}" font-size="12.5" fill="#64708A">'
                 f'Yuvin Kang · Product Quickstart · 2024</text>')
    parts.append(f'<text x="{bx+316}" y="{by+30}" font-size="12.5" fill="#64708A">SHEET</text>')
    parts.append(f'<text x="{bx+316}" y="{by+72}" font-size="12.5" fill="#64708A">UNITS  mm</text>')
    parts.append(f'<text x="{bx+316}" y="{by+96}" font-size="12.5" fill="#64708A">THIRD ANGLE</text>')
    for i, n in enumerate(notes):
        parts.append(f'<text x="34" y="{h - 40 - (len(notes) - 1 - i) * 20}" font-size="12.5" '
                     f'fill="#64708A">{n}</text>')
    parts.append("</svg>")
    svg = "".join(parts)
    # drop needless precision: the hidden-line views are thousands of segments
    svg = re.sub(r"-?\d+\.\d{3,}", lambda m: f"{float(m.group()):.2f}", svg)
    path = os.path.join(OUT, f"{name}.svg")
    open(path, "w").write(svg)
    print("sheet", path)


# ── sheet 1: general arrangement, three views, hidden detail shown ────────
front = project(FULL, "front")
side = project(FULL, "right")
top = project(FULL, "top")
sheet("ga", "GENERAL ARRANGEMENT",
      [("FRONT", front, 70, 110, 1.05),
       ("RIGHT", side, 470, 110, 1.05),
       ("TOP", top, 760, 150, 0.49)],
      notes=("Hidden detail shown dashed.",
             "Housing halves split on the centre plane; four M2 bosses.",))

# ── sheet 2: section through the mechanism ───────────────────────────────
sec = project(CUT, "front", hidden=False)
secside = project(CUT, "right", hidden=False)
sheet("section", "SECTION A-A", w=1080,
      views=[("SECTION A-A", sec, 90, 105, 1.25),
             ("SECTION B-B", secside, 520, 105, 1.25)],
      notes=("Front half of the housing removed.",
             "Carousel indexes one pocket per actuation; cam steps the plunger stroke weekly.",))

# ── sheet 3: the mechanism on its own ────────────────────────────────────
m1 = project(MECH, "front", hidden=False)
m2 = project(MECH, "right", hidden=False)
m3 = project(MECH, "top", hidden=False)
sheet("mechanism", "MECHANISM",
      [("FRONT", m1, 90, 105, 1.08),
       ("RIGHT", m2, 430, 105, 1.08),
       ("TOP", m3, 800, 150, 0.52)],
      notes=("Housing omitted.",
             "1 carousel · 2 ratchet + pawl · 3 taper cam · 4 metering plunger · 5 airway",))
