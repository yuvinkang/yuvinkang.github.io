"""
Accessible Shower Chair — powered bath transfer system.

The frame straddles the tub wall: the outboard pair of legs stands on the
bathroom floor, the inboard pair stands inside the tub. The user boards
outside, and a gearmotor and cable loop draw the seat carriage along the
rails and into the shower while a powered leg lift swings the calf support
up and over the tub wall.

Features
  1. Rotating transfer seat with a positive mechanical lock (8 x 45 deg notches)
  2. Flip-up armrests
  3. Adjustable seat height - telescoping pin-locked legs, which is also what
     lets the inboard pair stand on the tub floor
  4. Contoured drainage seat
  5. Removable leg support, powered to lift the legs clear of the tub wall
  6. Adjustable backrest with a detent recline plate
  7. Foldable aluminium frame
  8. Replaceable rubber feet (non-slip cups inside the tub)
  9. Gearmotor + cable-drum drive, idler pulley, carriage on rollers

Units: millimetres. Origin: on the bathroom floor, in the plane of the tub
wall. Tub side is +X. Run:  python3 shower_chair.py
"""
import os
import math
import cadquery as cq
from cadquery import exporters

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

# ── the bathroom it has to fit ────────────────────────────────────────────
WALL_T    = 110.0     # tub wall thickness
RIM_Z     = 560.0     # top of the tub wall
TUB_FLOOR = 130.0     # inner floor of the tub

# ── frame ─────────────────────────────────────────────────────────────────
RAIL_Z    = 470.0
RAIL_Y    = 205.0
RAIL_X    = 770.0
LEG_X     = 630.0
SPLAY     = 46.0
TUBE_OD   = 26.0
TUBE_WALL = 2.0
LOWER_OD  = 33.0
PIN_D     = 10.0
HOLE_P    = 26.0

CAR_X     = -60.0     # carriage shown mid-travel, over the wall

# ── seat ──────────────────────────────────────────────────────────────────
SEAT_W   = 420.0
SEAT_D   = 400.0
SEAT_T   = 26.0
CAR_TOP  = RAIL_Z + 62
SEAT_Z   = CAR_TOP + 20
SEAT_TOP = SEAT_Z + SEAT_T


def tube_between(p1, p2, od=TUBE_OD, wall=TUBE_WALL):
    a, b = cq.Vector(*p1), cq.Vector(*p2)
    v = b - a
    wp = cq.Workplane(cq.Plane(origin=a, normal=v.normalized()))
    return wp.circle(od / 2).circle(od / 2 - wall).extrude(v.Length)


def rod(p1, p2, d):
    a, b = cq.Vector(*p1), cq.Vector(*p2)
    v = b - a
    wp = cq.Workplane(cq.Plane(origin=a, normal=v.normalized()))
    return wp.circle(d / 2).extrude(v.Length)


def solidify(wp):
    """A Workplane holding a compound can't be the left side of a union."""
    return cq.Workplane().newObject(wp.solids().vals())


# ═══════════════════════════════════════════════════════════════════════════
# 7 — rails and foldable frame
# ═══════════════════════════════════════════════════════════════════════════
rails = None
for sy in (-1, 1):
    r = tube_between((-RAIL_X, sy * RAIL_Y, RAIL_Z), (RAIL_X, sy * RAIL_Y, RAIL_Z), od=34, wall=2.6)
    rails = r if rails is None else rails.union(r)
for sx in (-1, 1):
    rails = rails.union(tube_between((sx * (RAIL_X - 40), -RAIL_Y, RAIL_Z),
                                     (sx * (RAIL_X - 40), RAIL_Y, RAIL_Z), od=26))

# ═══════════════════════════════════════════════════════════════════════════
# 3 + 8 — telescoping legs, pins, rubber feet
# ═══════════════════════════════════════════════════════════════════════════
legs = None
pins = None
feet = None
FOOT_H = 58.0

for sx in (-1, 1):
    ground = 0.0 if sx < 0 else TUB_FLOOR      # inboard legs stand in the tub
    for sy in (-1, 1):
        top = (sx * LEG_X, sy * RAIL_Y, RAIL_Z)
        bot = (sx * (LEG_X + SPLAY), sy * (RAIL_Y + SPLAY * 0.5), ground + FOOT_H)
        dv = (cq.Vector(*top) - cq.Vector(*bot)).normalized()
        d = (dv.x, dv.y, dv.z)
        L = (cq.Vector(*top) - cq.Vector(*bot)).Length

        lower = tube_between(bot, tuple(bot[i] + d[i] * (L * 0.62) for i in range(3)),
                             od=LOWER_OD, wall=2.4)
        n_holes = 4 if sx > 0 else 6
        for i in range(n_holes):
            c = tuple(bot[j] + d[j] * (74 + i * HOLE_P) for j in range(3))
            lower = lower.cut(rod((c[0] - 40, c[1], c[2]), (c[0] + 40, c[1], c[2]), PIN_D))
        upper = tube_between(tuple(bot[i] + d[i] * (L * 0.44) for i in range(3)), top)
        legs = lower.union(upper) if legs is None else legs.union(lower).union(upper)

        pc = tuple(bot[j] + d[j] * (74 + (1 if sx > 0 else 2) * HOLE_P) for j in range(3))
        pin = (rod((pc[0] - 26, pc[1], pc[2]), (pc[0] + 26, pc[1], pc[2]), PIN_D)
               .union(cq.Workplane("YZ", origin=(pc[0] + 26, pc[1], pc[2])).circle(9).extrude(7)))
        pins = pin if pins is None else pins.union(pin)

        f = (cq.Workplane("XY", origin=(bot[0], bot[1], ground))
             .circle(22).extrude(FOOT_H)
             .edges(">Z").fillet(3).edges("<Z").fillet(5)
             .cut(cq.Workplane("XY", origin=(bot[0], bot[1], ground + FOOT_H - 36))
                  .circle(LOWER_OD / 2 + 0.3).extrude(42)))
        for k in range(3):
            f = f.cut(cq.Workplane("XY", origin=(bot[0], bot[1], ground + 11 + k * 11))
                      .circle(22.5).circle(20.6).extrude(3))
        feet = f if feet is None else feet.union(f)

    # folding cross-brace in each leg plane, with a pivot boss at the crossing
    a = (sx * LEG_X, -RAIL_Y, RAIL_Z - 30)
    b = (sx * (LEG_X + SPLAY), RAIL_Y + SPLAY * 0.5, ground + 170)
    c = (sx * LEG_X, RAIL_Y, RAIL_Z - 30)
    e = (sx * (LEG_X + SPLAY), -(RAIL_Y + SPLAY * 0.5), ground + 170)
    legs = legs.union(tube_between(a, b, od=20, wall=1.8)).union(tube_between(c, e, od=20, wall=1.8))
    mid = tuple((a[i] + b[i] + c[i] + e[i]) / 4 for i in range(3))
    legs = legs.union(cq.Workplane("YZ", origin=(mid[0] - 8, mid[1], mid[2])).circle(16).extrude(16)
                      .cut(cq.Workplane("YZ", origin=(mid[0] - 10, mid[1], mid[2])).circle(5).extrude(22)))

# ═══════════════════════════════════════════════════════════════════════════
# 9 — gearmotor, cable drum, idler pulley, cable loop
# ═══════════════════════════════════════════════════════════════════════════
MOT_X = -(RAIL_X - 110)
MOT_Z = RAIL_Z - 96

drive = cq.Workplane("YZ", origin=(MOT_X - 96, 0, MOT_Z)).circle(56).extrude(150)
drive = drive.union(cq.Workplane("XY", origin=(MOT_X + 32, 0, MOT_Z - 48))
                    .rect(72, 132).extrude(96).edges("|X").fillet(8))
drum = (cq.Workplane("YZ", origin=(MOT_X + 72, 0, MOT_Z)).circle(38).extrude(96)
        .union(cq.Workplane("YZ", origin=(MOT_X + 70, 0, MOT_Z)).circle(50).extrude(8))
        .union(cq.Workplane("YZ", origin=(MOT_X + 160, 0, MOT_Z)).circle(50).extrude(8)))
for i in range(9):
    drum = drum.union(cq.Workplane("YZ", origin=(MOT_X + 82 + i * 8, 0, MOT_Z))
                      .circle(41).circle(38).extrude(4))
drive = drive.union(drum)
drive = drive.union(rod((MOT_X + 168, 0, MOT_Z), (MOT_X + 198, 0, MOT_Z), 16))
drive = drive.union(cq.Workplane("XY", origin=(MOT_X + 208, 0, MOT_Z - 30))
                    .rect(26, 72).extrude(60).edges("|X").fillet(6))
mounts = None
for sy in (-1, 1):
    m = (cq.Workplane("XZ", origin=(MOT_X + 40, sy * RAIL_Y, RAIL_Z - 46))
         .rect(330, 116).extrude(10 * sy).edges("|Y").fillet(10))
    mounts = m if mounts is None else mounts.union(m)

IDL_X = RAIL_X - 110
idler = (cq.Workplane("YZ", origin=(IDL_X, -28, MOT_Z)).circle(46).extrude(56)
         .cut(cq.Workplane("YZ", origin=(IDL_X, -29, MOT_Z)).circle(38).extrude(19))
         .cut(cq.Workplane("YZ", origin=(IDL_X, 9, MOT_Z)).circle(38).extrude(19)))
idler = idler.union(rod((IDL_X, -58, MOT_Z), (IDL_X, 58, MOT_Z), 14))
for sy in (-1, 1):
    mounts = mounts.union(cq.Workplane("XZ", origin=(IDL_X, sy * RAIL_Y, RAIL_Z - 46))
                          .rect(120, 116).extrude(10 * sy).edges("|Y").fillet(10))

CAB = 7.0
cable = (rod((MOT_X + 120, -24, MOT_Z + 40), (CAR_X - 148, -24, MOT_Z + 40), CAB)
         .union(rod((CAR_X + 148, -24, MOT_Z + 40), (IDL_X, -24, MOT_Z + 40), CAB))
         .union(rod((MOT_X + 120, 24, MOT_Z - 44), (IDL_X, 24, MOT_Z - 44), CAB))
         .union(cq.Workplane("YZ", origin=(IDL_X, -24, MOT_Z)).circle(44).circle(37).extrude(48)))

# ═══════════════════════════════════════════════════════════════════════════
# carriage — rollers on the rails, turntable ring on top
# ═══════════════════════════════════════════════════════════════════════════
carriage = (cq.Workplane("XY", origin=(CAR_X, 0, RAIL_Z + 24))
            .rect(300, 2 * RAIL_Y + 44).extrude(38).edges("|Z").fillet(18))
carriage = carriage.cut(cq.Workplane("XY", origin=(CAR_X, 0, RAIL_Z + 23)).circle(104).extrude(42))
for sx in (-1, 1):
    for sy in (-1, 1):
        carriage = carriage.union(
            cq.Workplane("YZ", origin=(CAR_X + sx * 104, sy * RAIL_Y - 17, RAIL_Z)).circle(26).extrude(34)
            .cut(cq.Workplane("YZ", origin=(CAR_X + sx * 104, sy * RAIL_Y - 18, RAIL_Z)).circle(19).extrude(36)))
        carriage = carriage.union(
            cq.Workplane("XZ", origin=(CAR_X + sx * 104, sy * (RAIL_Y + 26), RAIL_Z + 14))
            .rect(70, 60).extrude(9 * sy).edges("|Y").fillet(6))
for sx in (-1, 1):
    carriage = carriage.union(cq.Workplane("XY", origin=(CAR_X + sx * 130, -24, MOT_Z + 27))
                              .rect(62, 36).extrude(26).edges("|X").fillet(7))
carriage = carriage.union(cq.Workplane("XY", origin=(CAR_X, 0, RAIL_Z + 56))
                          .circle(150).circle(128).extrude(16).edges(">Z").fillet(2))

# ═══════════════════════════════════════════════════════════════════════════
# 1 + 4 — rotating transfer seat, contoured, with drainage slots
# ═══════════════════════════════════════════════════════════════════════════
seat = (cq.Workplane("XY", origin=(0, 0, SEAT_Z)).rect(SEAT_W, SEAT_D).extrude(SEAT_T)
        .edges("|Z").fillet(70))
seat = seat.cut(cq.Workplane("XY", origin=(0, -10, SEAT_TOP + 150)).sphere(162))
seat = seat.cut(cq.Workplane("XZ", origin=(0, -SEAT_D / 2 - 1, SEAT_TOP))
                .moveTo(-SEAT_W / 2, 0).lineTo(SEAT_W / 2, 0)
                .lineTo(SEAT_W / 2, -9).lineTo(-SEAT_W / 2, -9).close().extrude(60))
seat = seat.cut(cq.Workplane("XY", origin=(0, -SEAT_D / 2 + 95, SEAT_Z - 1))
                .moveTo(-55, -95).lineTo(55, -95).lineTo(48, 40)
                .threePointArc((0, 72), (-48, 40)).close().extrude(SEAT_T + 2))
for y in (-110, -60, 60, 110, 155):
    n = 5 if abs(y) > 100 else 4
    for i in range(n):
        x = (i - (n - 1) / 2) * 62
        if abs(y) < 120 and abs(x) < 70:
            continue
        seat = seat.cut(cq.Workplane("XY", origin=(x, y, SEAT_Z - 1))
                        .slot2D(46, 11, 0).extrude(SEAT_T + 60))

hub = (cq.Workplane("XY", origin=(0, 0, SEAT_Z - 22)).circle(146).extrude(22)
       .cut(cq.Workplane("XY", origin=(0, 0, SEAT_Z - 23)).circle(120).extrude(20)))
for i in range(8):
    a = math.radians(i * 45)
    hub = hub.cut(cq.Workplane("XY", origin=(133 * math.cos(a), 133 * math.sin(a), SEAT_Z - 23))
                  .circle(7).extrude(16))
seat = seat.union(hub)

lock = (cq.Workplane("XY", origin=(0, SEAT_D / 2 - 26, SEAT_Z - 18)).rect(26, 86).extrude(12)
        .edges("|Z").fillet(6)
        .union(cq.Workplane("XY", origin=(0, SEAT_D / 2 - 62, SEAT_Z - 20)).circle(6.4).extrude(14))
        .union(cq.Workplane("XY", origin=(0, SEAT_D / 2 + 6, SEAT_Z - 16)).rect(44, 16).extrude(16)
               .edges("|Z").fillet(5)))

# ═══════════════════════════════════════════════════════════════════════════
# 6 — adjustable backrest
# ═══════════════════════════════════════════════════════════════════════════
BACK_Y = SEAT_D / 2 - 18
backrest = None
for sx in (-1, 1):
    p = tube_between((sx * 160, BACK_Y, SEAT_Z - 10), (sx * 160, BACK_Y + 70, SEAT_Z + 360), od=26)
    backrest = p if backrest is None else backrest.union(p)
    pl = cq.Workplane("YZ", origin=(sx * 160, BACK_Y - 4, SEAT_Z + 6)).circle(32).extrude(10 * sx)
    for k in range(5):
        a = math.radians(-40 + k * 20)
        pl = pl.cut(cq.Workplane("YZ", origin=(sx * 160 + 11 * sx, BACK_Y - 4 + 22 * math.cos(a),
                                               SEAT_Z + 6 + 22 * math.sin(a)))
                    .circle(4).extrude(-26 * sx))
    backrest = backrest.union(pl)

back_pad = (cq.Workplane("XZ", origin=(0, BACK_Y + 56, SEAT_Z + 262)).rect(396, 196).extrude(30)
            .edges("|Y").fillet(28)
            .cut(cq.Workplane("XZ", origin=(0, BACK_Y + 212, SEAT_Z + 262)).sphere(160)))
for i in range(3):
    back_pad = back_pad.cut(cq.Workplane("XZ", origin=(0, BACK_Y + 86, SEAT_Z + 212 + i * 50))
                            .slot2D(190, 13, 0).extrude(70))
backrest = backrest.union(back_pad)

# ═══════════════════════════════════════════════════════════════════════════
# 2 — flip-up armrests
# ═══════════════════════════════════════════════════════════════════════════
ARM_Z = SEAT_Z + 165
arms = None
for sx in (-1, 1):
    hinge = (cq.Workplane("YZ", origin=(sx * 232, BACK_Y - 10, SEAT_Z + 30)).circle(17).extrude(22 * sx)
             .cut(cq.Workplane("YZ", origin=(sx * 232, BACK_Y - 10, SEAT_Z + 30)).circle(5).extrude(30 * sx)))
    upright = tube_between((sx * 243, BACK_Y - 10, SEAT_Z + 30), (sx * 243, BACK_Y - 10, ARM_Z), od=24)
    pad = (cq.Workplane("XY", origin=(sx * 243, 10, ARM_Z - 13)).rect(54, 320).extrude(28)
           .edges("|Z").fillet(24).edges("|X").fillet(8))
    pad = pad.cut(cq.Workplane("XY", origin=(sx * 243, -128, ARM_Z - 14)).rect(34, 76).extrude(10)
                  .edges("|Z").fillet(14))
    front_leg = tube_between((sx * 243, -128, ARM_Z - 13), (sx * 243, -128, SEAT_Z - 30), od=22)
    a = hinge.union(upright).union(pad).union(front_leg)
    arms = a if arms is None else arms.union(a)

# ═══════════════════════════════════════════════════════════════════════════
# 5 — leg support, shown part-way through its powered lift
# ═══════════════════════════════════════════════════════════════════════════
LIFT = math.radians(44)
PIV = (0.0, -SEAT_D / 2 + 10, SEAT_Z - 34)


def lift_at(x, fwd, up):
    """Point `fwd` ahead of the pivot and `up` above it, swung by LIFT."""
    return (x,
            PIV[1] - fwd * math.cos(LIFT) + up * math.sin(LIFT),
            PIV[2] + fwd * math.sin(LIFT) + up * math.cos(LIFT))


socket = (cq.Workplane("XY", origin=(0, PIV[1] + 8, PIV[2] - 12)).rect(150, 54).extrude(38)
          .edges("|Z").fillet(10)
          .cut(cq.Workplane("XY", origin=(0, PIV[1] + 8, PIV[2] - 10)).rect(118, 32).extrude(38)))
socket = solidify(socket)

ls_arm = (tube_between(lift_at(-46, 8, 0), lift_at(-46, 252, 0), od=24)
          .union(tube_between(lift_at(46, 8, 0), lift_at(46, 252, 0), od=24))
          .union(tube_between(lift_at(-46, 252, 0), lift_at(46, 252, 0), od=24)))

cp = lift_at(0, 208, 26)
calf = (cq.Workplane("XY", origin=(0, cp[1], cp[2])).rect(190, 150).extrude(26)
        .edges("|Z").fillet(34))
calf = calf.cut(cq.Workplane("XY", origin=(0, cp[1], cp[2] + 160)).sphere(166))
for i in range(2):
    calf = calf.cut(cq.Workplane("XY", origin=(0, cp[1] - 32 + i * 62, cp[2] - 2))
                    .slot2D(106, 12, 0).extrude(44))

act_a = (0.0, PIV[1] + 52, PIV[2] + 92)
act_b = lift_at(0, 132, 56)
actuator = tube_between(act_a, act_b, od=34, wall=4).union(rod(act_a, act_b, 15))
for p in (act_a, act_b):
    actuator = actuator.union(cq.Workplane("XY", origin=(0, p[1], p[2] - 11)).circle(17).extrude(22))
for sx in (-1, 1):
    actuator = actuator.union(
        cq.Workplane("YZ", origin=(sx * 46, PIV[1], PIV[2])).circle(20).extrude(16 * sx)
        .cut(cq.Workplane("YZ", origin=(sx * 46, PIV[1], PIV[2])).circle(6).extrude(22 * sx)))

qr = (rod((-92, PIV[1], PIV[2] + 2), (92, PIV[1], PIV[2] + 2), 10)
      .union(cq.Workplane("YZ", origin=(92, PIV[1], PIV[2] + 2)).circle(11).extrude(9)))

leg_support = ls_arm.union(socket).union(calf).union(qr)

# ═══════════════════════════════════════════════════════════════════════════
# move the seat group onto the carriage
# ═══════════════════════════════════════════════════════════════════════════
# The user faces the tub, so the leg lift swings out over the wall ahead of
# them: turn the seat group 90 deg (its front, -Y, becomes +X) and set it on
# the carriage.
SHIFT = (CAR_X, 0, 0)


def onto_carriage(part):
    return part.rotate((0, 0, 0), (0, 0, 1), 90).translate(SHIFT)


seat = onto_carriage(seat)
lock = onto_carriage(lock)
backrest = onto_carriage(backrest)
arms = onto_carriage(arms)
leg_support = onto_carriage(leg_support)
actuator = onto_carriage(actuator)

# ═══════════════════════════════════════════════════════════════════════════
# context only: the tub wall. Not part of the product.
# ═══════════════════════════════════════════════════════════════════════════
tub = (cq.Workplane("XY", origin=(0, 0, 0)).rect(WALL_T, 950).extrude(RIM_Z)
       .edges("|Y").fillet(26)
       .union(cq.Workplane("XY", origin=(820, 0, 0)).rect(1520, 950).extrude(TUB_FLOOR)))

# ═══════════════════════════════════════════════════════════════════════════
# export
# ═══════════════════════════════════════════════════════════════════════════
frame = rails.union(legs).union(mounts)

asm = (cq.Assembly(name="accessible_shower_chair_transfer_system")
       .add(frame,       name="frame_aluminium",   color=cq.Color(0.72, 0.74, 0.77))
       .add(carriage,    name="carriage",          color=cq.Color(0.80, 0.82, 0.85))
       .add(drive,       name="gearmotor_drive",   color=cq.Color(0.30, 0.33, 0.37))
       .add(idler,       name="idler_pulley",      color=cq.Color(0.80, 0.82, 0.85))
       .add(cable,       name="drive_cable",       color=cq.Color(0.20, 0.22, 0.26))
       .add(seat,        name="seat_rotating",     color=cq.Color(0.93, 0.94, 0.95))
       .add(lock,        name="seat_lock",         color=cq.Color(0.00, 0.47, 0.42))
       .add(backrest,    name="backrest",          color=cq.Color(0.93, 0.94, 0.95))
       .add(arms,        name="armrests_flip_up",  color=cq.Color(0.90, 0.91, 0.93))
       .add(leg_support, name="leg_lift_support",  color=cq.Color(0.90, 0.91, 0.93))
       .add(actuator,    name="leg_lift_actuator", color=cq.Color(0.30, 0.33, 0.37))
       .add(feet,        name="feet_rubber",       color=cq.Color(0.16, 0.18, 0.22))
       .add(pins,        name="height_pins",       color=cq.Color(0.00, 0.47, 0.42)))
asm.save(os.path.join(OUT, "accessible-shower-chair.step"))
print("STEP written")

parts = {
    "frame": frame, "carriage": carriage, "drive": drive, "idler": idler,
    "cable": cable, "seat": seat, "lock": lock, "backrest": backrest,
    "arms": arms, "legsupport": leg_support, "actuator": actuator,
    "feet": feet, "pins": pins, "tub": tub,
}
for name, part in parts.items():
    exporters.export(part, os.path.join(OUT, f"{name}.stl"),
                     tolerance=0.08, angularTolerance=0.15)
    print("STL", name)
