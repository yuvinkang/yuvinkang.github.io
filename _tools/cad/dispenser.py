"""
Stepwise-Dosing Nicotine Dispenser — mechanism model.

A handheld dispenser that steps the dose down over a tapering course. A
28-pocket carousel holds one pod per day; a ratchet and pawl index it one
pocket per actuation, and a spiral cam under the carousel shortens the
metering plunger's stroke each week, so the delivered dose falls on a
schedule the user cannot skip ahead of.

Parts
  shell_front / shell_back   housing halves, mouthpiece moulded into the front
  carousel                   28 dose pockets
  ratchet                    ratchet wheel + sprung pawl + index spring
  cam                        spiral taper cam, one step per week
  plunger                    metering plunger and its return spring
  lever                      side actuation lever
  pcb                        board, coin cell, dose window

Units: millimetres. Run:  python3 dispenser.py
"""
import os
import math
import cadquery as cq
from cadquery import exporters

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_disp")
os.makedirs(OUT, exist_ok=True)

W, D, Hh = 62.0, 24.0, 118.0      # housing envelope
R_OUT = 11.0                       # corner radius
WALL = 2.0
CAR_R = 21.0                       # carousel radius
CAR_Z = 42.0                       # carousel mid-height
POCKETS = 28


def shell_half(front: bool):
    """One housing half, split on the XZ plane."""
    y0 = 0 if front else -D / 2
    body = (cq.Workplane("XY", origin=(0, 0, 0))
            .rect(W, D).extrude(Hh).edges("|Z").fillet(R_OUT)
            .edges("|X").fillet(3.5))
    half = body.intersect(cq.Workplane("XY", origin=(0, y0 + D / 4, -5))
                          .rect(W + 10, D / 2).extrude(Hh + 10))
    cavity = (cq.Workplane("XY", origin=(0, 0, WALL))
              .rect(W - 2 * WALL, D - 2 * WALL).extrude(Hh - 2 * WALL)
              .edges("|Z").fillet(R_OUT - WALL))
    half = half.cut(cavity)
    if front:
        # mouthpiece
        mp = (cq.Workplane("XY", origin=(0, 0, Hh - 2)).rect(30, 15).extrude(16)
              .edges("|Z").fillet(6).edges(">Z").fillet(3))
        mp = mp.cut(cq.Workplane("XY", origin=(0, 0, Hh - 3)).rect(17, 7).extrude(22)
                    .edges("|Z").fillet(3))
        half = half.union(mp.intersect(cq.Workplane("XY", origin=(0, D / 4, Hh - 4))
                                       .rect(W, D / 2).extrude(24)))
        # dose window
        half = half.cut(cq.Workplane("XZ", origin=(0, -D, 88)).rect(34, 15).extrude(2 * D)
                        .edges("|Y").fillet(3))
        # thumb detent round the lever slot
        half = half.cut(cq.Workplane("XZ", origin=(W / 2 - 3, -D, CAR_Z)).rect(10, 34).extrude(2 * D))
    else:
        # cartridge door, screw bosses
        half = half.cut(cq.Workplane("XZ", origin=(0, 0, CAR_Z)).rect(44, 46).extrude(D)
                        .edges("|Y").fillet(6))
        for z in (12, Hh - 12):
            half = half.union(cq.Workplane("XY", origin=(0, -D / 4, z - 4)).circle(4).extrude(8)
                              .cut(cq.Workplane("XY", origin=(0, -D / 4, z - 5)).circle(1.6).extrude(10)))
    return half


shell_front = shell_half(True)
shell_back = shell_half(False)

# ── carousel: 28 dose pockets on a disc ───────────────────────────────────
carousel = (cq.Workplane("XZ", origin=(0, 0, CAR_Z)).circle(CAR_R).extrude(7)
            .union(cq.Workplane("XZ", origin=(0, 3.5, CAR_Z)).circle(5).extrude(10)))
for i in range(POCKETS):
    a = math.radians(i * 360.0 / POCKETS)
    carousel = carousel.cut(
        cq.Workplane("XZ", origin=(15 * math.cos(a), -1, CAR_Z + 15 * math.sin(a))).circle(2.1).extrude(9))
carousel = carousel.cut(cq.Workplane("XZ", origin=(0, -1, CAR_Z)).circle(2.6).extrude(12))

# ── ratchet wheel + sprung pawl ───────────────────────────────────────────
ratchet = cq.Workplane("XZ", origin=(0, 7, CAR_Z)).circle(13).extrude(4)
for i in range(POCKETS):
    a = math.radians(i * 360.0 / POCKETS)
    ratchet = ratchet.cut(cq.Workplane("XZ", origin=(13.4 * math.cos(a), 6, CAR_Z + 13.4 * math.sin(a)))
                          .circle(1.9).extrude(6))
ratchet = ratchet.union(cq.Workplane("XZ", origin=(0, 6, CAR_Z)).circle(4.4).extrude(7))
# pawl: a thin arm with a tooth, pivoted off to the side
pawl = (cq.Workplane("XZ", origin=(22, 7.5, CAR_Z + 2)).rect(22, 4.6).extrude(3)
        .edges("|Y").fillet(2))
pawl = pawl.union(cq.Workplane("XZ", origin=(12.6, 7.5, CAR_Z + 2)).rect(4, 6.4).extrude(3)
                  .edges("|Y").fillet(1.2))
pawl = pawl.union(cq.Workplane("XZ", origin=(31, 7.5, CAR_Z + 2)).circle(3.4).extrude(3)
                  .cut(cq.Workplane("XZ", origin=(31, 7, CAR_Z + 2)).circle(1.3).extrude(5)))
# index spring, drawn as a coil of rings
spring = None
for i in range(7):
    s = (cq.Workplane("XZ", origin=(26 + i * 1.1, 7.5, CAR_Z + 9 + i * 0.9))
         .circle(2.6).circle(1.9).extrude(1.0))
    spring = s if spring is None else spring.union(s)
ratchet = ratchet.union(pawl).union(spring)

# ── spiral taper cam: one step per week ───────────────────────────────────
cam = cq.Workplane("XZ", origin=(0, -6, CAR_Z)).circle(6).extrude(5)
for wk in range(4):
    lo = math.radians(wk * 90)
    r = 15.0 - wk * 2.4
    seg = (cq.Workplane("XZ", origin=(0, -6, CAR_Z))
           .moveTo(0, 0)
           .lineTo(r * math.cos(lo), r * math.sin(lo))
           .threePointArc((r * math.cos(lo + math.radians(45)), r * math.sin(lo + math.radians(45))),
                          (r * math.cos(lo + math.radians(90)), r * math.sin(lo + math.radians(90))))
           .close().extrude(5))
    cam = cam.union(seg)
cam = cam.cut(cq.Workplane("XZ", origin=(0, -7, CAR_Z)).circle(2.6).extrude(8))

# ── metering plunger and return spring ────────────────────────────────────
plunger = (cq.Workplane("XY", origin=(0, -6, CAR_Z - 30)).circle(4.6).extrude(24)
           .union(cq.Workplane("XY", origin=(0, -6, CAR_Z - 32)).circle(7).extrude(4))
           .union(cq.Workplane("XY", origin=(0, -6, CAR_Z - 7)).rect(10, 5).extrude(5)
                  .edges("|Z").fillet(2)))
for i in range(8):
    plunger = plunger.union(cq.Workplane("XY", origin=(0, -6, CAR_Z - 28 + i * 2.4))
                            .circle(7.2).circle(6.2).extrude(1.1))
# metering chamber + the airway up to the mouthpiece
airway = (cq.Workplane("XY", origin=(0, -6, CAR_Z + 8)).circle(3.4).extrude(Hh - CAR_Z - 12)
          .union(cq.Workplane("XY", origin=(0, -3, Hh - 6)).circle(3.4).extrude(6)))

# ── side actuation lever ──────────────────────────────────────────────────
lever = (cq.Workplane("XZ", origin=(W / 2 - 2, 2, CAR_Z)).rect(7, 30).extrude(7)
         .edges("|Y").fillet(3))
lever = lever.union(cq.Workplane("XZ", origin=(W / 2 - 12, 2, CAR_Z - 10)).rect(20, 5).extrude(5)
                    .edges("|Y").fillet(2))
for i in range(4):
    lever = lever.cut(cq.Workplane("XZ", origin=(W / 2 + 2, 2, CAR_Z - 9 + i * 6)).rect(4, 1.8).extrude(9))

# ── board, coin cell, display ─────────────────────────────────────────────
pcb = (cq.Workplane("XY", origin=(0, 2, 78)).rect(40, 1.6).extrude(26)
       .union(cq.Workplane("XZ", origin=(0, 1, 88)).rect(30, 12).extrude(2.4))
       .union(cq.Workplane("XZ", origin=(-13, 3, 70)).circle(9).extrude(4))
       .union(cq.Workplane("XZ", origin=(12, 1, 70)).rect(9, 5).extrude(2)))

# ═══════════════════════════════════════════════════════════════════════════
# export
# ═══════════════════════════════════════════════════════════════════════════
parts = {
    "shell_front": shell_front, "shell_back": shell_back, "carousel": carousel,
    "ratchet": ratchet, "cam": cam, "plunger": plunger, "airway": airway,
    "lever": lever, "pcb": pcb,
}

asm = cq.Assembly(name="stepwise_nicotine_dispenser")
COLS = {
    "shell_front": (0.90, 0.91, 0.93), "shell_back": (0.86, 0.87, 0.89),
    "carousel": (0.00, 0.47, 0.42), "ratchet": (0.62, 0.65, 0.69),
    "cam": (0.00, 0.47, 0.42), "plunger": (0.62, 0.65, 0.69),
    "airway": (0.80, 0.86, 0.88), "lever": (0.25, 0.27, 0.30),
    "pcb": (0.16, 0.34, 0.30),
}
for n, p in parts.items():
    asm.add(p, name=n, color=cq.Color(*COLS[n]))
asm.save(os.path.join(OUT, "nicotine-dispenser.step"))
print("STEP written")

for n, p in parts.items():
    exporters.export(p, os.path.join(OUT, f"{n}.stl"), tolerance=0.04, angularTolerance=0.12)
    print("STL", n)

# a cutaway copy of the housing, for the section render
cutter = cq.Workplane("XZ", origin=(0, -2, 0)).rect(W + 20, Hh + 20).extrude(D)
exporters.export(shell_front.cut(cutter), os.path.join(OUT, "shell_front_cut.stl"),
                 tolerance=0.04, angularTolerance=0.12)
exporters.export(shell_back.cut(cutter), os.path.join(OUT, "shell_back_cut.stl"),
                 tolerance=0.04, angularTolerance=0.12)
print("cutaway written")
