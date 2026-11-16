"""
Stickman scene generator.

Run from the site root:  python3 _tools/scenes.py
Writes  _includes/scenes/*.html  (inline SVG)  and  assets/css/scenes.css  (animations).

Figure model (local units, hip at 0,0, y down, facing right):
  head (0,-40) r7 · torso (0,-33)->(0,0) · shoulder (0,-28)
  upper arm 13 · forearm 12 · thigh 15 · shin 14 · ground at y=29
Angles: 0 = limb pointing straight down; negative = swings forward (to the right).
Child joints (fL, fR, sL, sR) are relative to their parent.
"""
import math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INC = os.path.join(ROOT, "_includes", "scenes")
os.makedirs(INC, exist_ok=True)
CSS = []

# ───────────────────────── geometry helpers ─────────────────────────
def ang_of(dx, dy):
    return math.degrees(math.atan2(-dx, dy))

def norm(a):
    while a > 180: a -= 360
    while a < -180: a += 360
    return a

def rot(p, deg, c=(0, 0)):
    t = math.radians(deg); x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(t) - y * math.sin(t), c[1] + x * math.sin(t) + y * math.cos(t))

def ik(S, T, L1=13, L2=12, elbow="down"):
    """Two-bone IK → (parent abs angle, child relative angle)."""
    dx, dy = T[0] - S[0], T[1] - S[1]
    D = max(min(math.hypot(dx, dy), L1 + L2 - 0.01), abs(L1 - L2) + 0.01)
    base = math.atan2(dy, dx)
    a = math.acos((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D))
    cands = [(S[0] + L1 * math.cos(base + s * a), S[1] + L1 * math.sin(base + s * a)) for s in (1, -1)]
    key = {"down": lambda e: e[1], "up": lambda e: -e[1], "front": lambda e: e[0], "back": lambda e: -e[0]}[elbow]
    E = max(cands, key=key)
    Tp = (S[0] + D * math.cos(base), S[1] + D * math.sin(base))
    a1 = ang_of(E[0] - S[0], E[1] - S[1]); a2 = ang_of(Tp[0] - E[0], Tp[1] - E[1])
    return round(a1, 1), round(norm(a2 - a1), 1)

def arm(T, up=0, elbow="down"):
    return ik((0, -28), rot(T, -up), 13, 12, elbow)

def leg(T, elbow="front"):
    return ik((0, 0), T, 15, 14, elbow)

# ───────────────────────── SVG helpers ─────────────────────────
def L(x1, y1, x2, y2, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<line{c} x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}"/>'

def J(cls, px, py, a, inner):
    return f'<g class="{cls}" style="transform-origin:{px:g}px {py:g}px;transform:rotate({a:g}deg)">{inner}</g>'

def fig(name, x, y, s=1.0, pose=None, ex=None, flip=False, move=None):
    p = dict(up=0, aL=0, fL=0, aR=0, fR=0, lL=0, sL=0, lR=0, sR=0); p.update(pose or {})
    e = ex or {}
    legL = J("lL", 0, 0, p["lL"], L(0, 0, 0, 15) + J("sL", 0, 15, p["sL"], L(0, 15, 0, 29) + e.get("footL", "")))
    legR = J("lR", 0, 0, p["lR"], L(0, 0, 0, 15) + J("sR", 0, 15, p["sR"], L(0, 15, 0, 29) + e.get("footR", "")))
    armL = J("aL", 0, -28, p["aL"], L(0, -28, 0, -15) + J("fL", 0, -15, p["fL"], L(0, -15, 0, -3) + e.get("hL", "")))
    armR = J("aR", 0, -28, p["aR"], L(0, -28, 0, -15) + J("fR", 0, -15, p["fR"], L(0, -15, 0, -3) + e.get("hR", "")))
    upper = J("up", 0, 0, p["up"], e.get("back", "") + armL + L(0, -33, 0, 0) +
              '<circle class="head" cx="0" cy="-40" r="7"/>' + e.get("head", "") + armR)
    body = e.get("behind", "") + legL + legR + upper + e.get("front", "")
    sx = -s if flip else s
    out = f'<g transform="translate({x:g} {y:g}) scale({sx:g} {s:g})"><g class="fig {name}">{body}</g></g>'
    return f'<g class="{move}">{out}</g>' if move else out

def upright(markup, total, at=(0, -3)):
    """Counter-rotate something held in a hand so it stays level."""
    return f'<g transform="rotate({-total:g} {at[0]:g} {at[1]:g})">{markup}</g>'

def note(x, y, cls):
    return (f'<g class="note {cls}" style="transform-origin:{x:g}px {y:g}px">'
            f'<g transform="translate({x:g} {y:g})"><ellipse class="fill" cx="0" cy="0" rx="3.2" ry="2.3" transform="rotate(-20)"/>'
            f'<line x1="2.9" y1="-0.8" x2="2.9" y2="-12"/><path class="st" d="M2.9 -12 q4 2 4 6"/></g></g>')

def ball(r=4.5):
    return (f'<circle class="ball" r="{r}"/><path class="fill" d="M0 -1.9 L1.8 -0.6 L1.1 1.5 L-1.1 1.5 L-1.8 -0.6 Z"/>')

def svg(name, vb, body, label):
    return (f'<svg class="scene scene-{name}" viewBox="{vb}" role="img" aria-label="{label}" '
            f'preserveAspectRatio="xMidYMax meet">{body}</svg>\n')

def kf(name, frames, prop="rotate", unit="deg"):
    """frames: list of (percent, value[, timing])"""
    out = [f"@keyframes {name}{{"]
    for f in frames:
        pct, val = f[0], f[1]
        tf = f";animation-timing-function:{f[2]}" if len(f) > 2 else ""
        if prop == "rotate":
            v = f"transform:rotate({val:g}deg)"
        elif prop == "tx":
            v = f"transform:translateX({val:g}px)"
        elif prop == "ty":
            v = f"transform:translateY({val:g}px)"
        elif prop == "txy":
            v = f"transform:translate({val[0]:g}px,{val[1]:g}px)"
        else:
            v = f"{prop}:{val}"
        out.append(f"{pct:g}%{{{v}{tf}}}")
    out.append("}")
    CSS.append("".join(out))

def write(name, content):
    with open(os.path.join(INC, name + ".html"), "w") as f:
        f.write(content)

GROUND = lambda x1, x2, y: L(x1, y, x2, y, "ground")
CAP = lambda x, y, t, anchor="middle": f'<text class="cap" x="{x:g}" y="{y:g}" text-anchor="{anchor}">{t}</text>'

# ═════════════════════════ COMPONENTS ═════════════════════════

# ── Scientist pipetting at a bench ──
def scientist(x, y, s):
    up_pos, down_pos = (19, -25), (19, -20)
    a_up, a_dn = arm(up_pos), arm(down_pos)
    tot = a_dn[0] + a_dn[1]
    pip = upright(L(0, -3, 0, 6) + '<rect class="fill" x="-1.6" y="-6" width="3.2" height="3" rx="1"/>'
                  + L(0, 6, 0, 9, "thin"), tot)
    aL = arm((6, -6))
    coat = '<path class="coat" d="M-5 -30 L5 -30 L8 -1 L-8 -1 Z"/>'
    goggles = L(2, -42, 7, -42, "thin")
    bench = ('<rect class="fill" x="8" y="-2.2" width="74" height="2.2" rx="1"/>' + L(12, 0, 12, 29, "thin") + L(78, 0, 78, 29, "thin"))
    rack = "".join(f'<rect class="tube" x="{tx}" y="-10" width="3.2" height="7.8" rx="1.4"/>' for tx in (13.4, 17.4, 21.4))
    rack += '<rect class="fill" x="11.5" y="-5" width="15" height="1.2"/>'
    flask = ('<path class="liquid" d="M37.5 -8 L34 -2.4 L52 -2.4 L48.5 -8 Z"/>'
             '<path class="st" d="M40.5 -16 L40.5 -11 L34 -2.4 L52 -2.4 L45.5 -11 L45.5 -16"/>' + L(39.5, -16, 46.5, -16))
    bubbles = "".join(f'<circle class="bubble b{i}" cx="{cx}" cy="-12" r="{r}"/>' for i, (cx, r) in enumerate([(42, 1.3), (44.5, 1), (43, .8)]))
    scope = ('<rect class="fill" x="60" y="-4.4" width="14" height="2.2" rx="1"/>'
             '<path class="st" d="M71 -4 L71 -14 Q71 -20 66 -21"/>' + L(62, -9, 72, -9)
             + '<line class="thick" x1="64" y1="-25" x2="67" y2="-13"/>')
    drop = '<circle class="drop" cx="19" cy="-11" r="1.2"/>'
    body = fig("sci", x, y, s, dict(aR=a_up[0], fR=a_up[1], aL=aL[0], fL=aL[1]),
               dict(hR=pip, back=coat, head=goggles, behind=bench + rack + flask + bubbles + scope, front=drop))
    kf("sciArm", [(0, a_up[0], "ease-in-out"), (30, a_dn[0]), (55, a_dn[0], "ease-in-out"), (75, a_up[0]), (100, a_up[0])])
    kf("sciFore", [(0, a_up[1], "ease-in-out"), (30, a_dn[1]), (40, a_dn[1] - 4), (50, a_dn[1]), (55, a_dn[1], "ease-in-out"), (75, a_up[1]), (100, a_up[1])])
    CSS.append(".sci .aR{animation:sciArm 2.6s infinite}.sci .fR{animation:sciFore 2.6s infinite}"
               "@keyframes sciDrop{0%,38%{opacity:0;transform:none}42%{opacity:1;transform:none}60%{opacity:0;transform:translateY(7px)}100%{opacity:0}}"
               ".sci .drop{animation:sciDrop 2.6s infinite ease-in}"
               "@keyframes bubble{0%{opacity:0;transform:none}20%{opacity:.9}100%{opacity:0;transform:translate(1px,-14px)}}"
               ".sci .bubble{animation:bubble 2.2s infinite ease-out}.sci .b1{animation-delay:-.75s}.sci .b2{animation-delay:-1.5s}"
               "@keyframes sciHead{0%,60%{transform:rotate(0)}70%,90%{transform:rotate(8deg)}100%{transform:rotate(0)}}"
               ".sci .up{animation:sciHead 7.8s infinite ease-in-out}")
    return body

# ── Juggler (keeps it up 5 times, drops it, restarts) ──
def juggler(x, y, s):
    ex = dict(front='<g class="jbx"><g class="jby"><g class="spinner">' + ball() + '</g></g></g>')
    body = fig("juggler", x, y, s, dict(aL=50, aR=-50, lR=-60, sR=60), ex)
    T = 7
    contacts = [0, 1.2, 2.4, 3.6]
    leg_frames, ball_y = [], []
    for c in contacts:
        p0, pa = c / T * 100, (c + .6) / T * 100
        leg_frames += [(p0, -60, "ease-in-out"), (pa, -15)]
        ball_y += [(p0, 16.5, "cubic-bezier(.2,.6,.4,1)"), (pa, -45, "cubic-bezier(.6,0,.8,.4)")]
    leg_frames += [(66, -15, "ease-out"), (68.6, -32, "ease-in"), (72, -15), (92, -15, "ease-in-out"), (100, -60)]
    ball_y += [(70.4, 24.5, "ease-out"), (73.5, 18, "ease-in"), (76.5, 24.5), (90, 24.5), (90.4, -70, "cubic-bezier(.6,0,.8,.4)"), (100, 16.5)]
    kf("jugLeg", leg_frames)
    kf("jugShin", [(f[0], -f[1]) + tuple(f[2:]) for f in leg_frames])
    kf("jugBy", ball_y, "ty")
    kf("jugBx", [(0, 12), (70.4, 12, "ease-out"), (90, 68), (90.3, 12), (100, 12)], "tx")
    kf("jugArmL", [(0, 50), (70, 50, "ease-out"), (74, 155), (86, 155, "ease-in-out"), (92, 50), (100, 50)])
    kf("jugArmR", [(0, -50), (70, -50, "ease-out"), (74, -155), (86, -155, "ease-in-out"), (92, -50), (100, -50)])
    CSS.append(f".juggler .lR{{animation:jugLeg {T}s infinite}}.juggler .sR{{animation:jugShin {T}s infinite}}"
               f".juggler .aL{{animation:jugArmL {T}s infinite}}.juggler .aR{{animation:jugArmR {T}s infinite}}"
               f".juggler .jby{{animation:jugBy {T}s infinite}}"
               f"@keyframes jugFade{{0%,80%{{opacity:1}}89%,91%{{opacity:0}}94%,100%{{opacity:1}}}}"
               f".juggler .jbx{{animation:jugBx {T}s infinite,jugFade {T}s infinite}}"
               f".juggler .spinner{{animation:spin 1.2s linear infinite}}")
    return body

# ── Double bassist with floating notes ──
def bassist(x, y, s, cls="bassist", notes=3):
    tilt = -8
    bass_body = ('<path class="wood" d="M12 -22 C18 -22 20 -16 20 -10 C20 -4 17 -1 17 2 C17 6 22 9 22 15 C22 22 17 25 12 25 '
                 'C7 25 2 22 2 15 C2 9 7 6 7 2 C7 -1 4 -4 4 -10 C4 -16 6 -22 12 -22 Z"/>'
                 '<path class="st thin" d="M8.5 -2 q-1 3 0 6 M15.5 -2 q1 3 0 6"/>'
                 '<rect class="fill" x="10.9" y="-56" width="2.2" height="36" rx="1"/>'
                 '<circle class="st" cx="12" cy="-58.5" r="2.4"/>' + L(11.3, -54, 11.3, 17, "hair") + L(12.7, -54, 12.7, 17, "hair")
                 + L(9, 10, 15, 10) + L(12, 25, 12, 29))
    bass = f'<g transform="rotate({tilt} 12 29)">{bass_body}</g>'
    neck = rot((12, -40), tilt, (12, 29))
    aL = arm((neck[0] - 1, neck[1]), elbow="down")
    t1, t2 = (-1, -8), (9, -5)
    a1, a2 = arm(t1), arm(t2)
    tot = a1[0] + a1[1]
    bow = upright('<path class="st" d="M-3 -3 L25 -6"/><path class="st hair" d="M-2 -1.6 L24 -4.4"/>'
                  '<rect class="fill" x="-4" y="-4.6" width="3.4" height="3" rx="0.8"/>', tot)
    ns = "".join(note(18 + i * 3, -30 - i * 4, f"n{i}") for i in range(notes))
    body = fig(cls, x, y, s, dict(aR=a1[0], fR=a1[1], aL=aL[0], fL=aL[1], lL=8, lR=-6),
               dict(behind=bass, hR=bow, front=ns))
    kf("bowArm", [(0, a1[0]), (100, a2[0])]); kf("bowFore", [(0, a1[1]), (100, a2[1])])
    kf("bassSway", [(0, -2), (100, 3)])
    kf("vib", [(0, aL[1] - 3), (100, aL[1] + 3)])
    CSS.append(f".{cls} .aR{{animation:bowArm 1.6s infinite alternate ease-in-out}}.{cls} .fR{{animation:bowFore 1.6s infinite alternate ease-in-out}}"
               f".{cls} .up{{animation:bassSway 1.6s infinite alternate ease-in-out}}.{cls} .fL{{animation:vib .18s infinite alternate}}"
               "@keyframes noteFloat{0%{opacity:0;transform:translate(0,0) rotate(0)}15%{opacity:1}100%{opacity:0;transform:translate(26px,-34px) rotate(14deg)}}"
               f".{cls} .note{{animation:noteFloat 3s infinite ease-out}}"
               + "".join(f".{cls} .n{i}{{animation-delay:{-i * 3 / notes:.2f}s}}" for i in range(notes)))
    return body

# ── Taekwondo kick (shared by heavy-bag and board-break variants) ──
STANCE = dict(lL=25, sL=0, lR=-12, sR=0, aL=-30, fL=-110, aR=-50, fR=-100, up=0)
def kick_css(cls, T=3.0):
    kf("tkdLegR", [(0, -12), (20, -12, "ease-in"), (32, -95, "ease-out"), (40, -90), (48, -90, "ease-in"), (56, -95, "ease-out"), (66, -12), (100, -12)])
    kf("tkdShinR", [(0, 0), (20, 0, "ease-in"), (32, 105, "ease-out"), (40, 0), (48, 0, "ease-in"), (56, 105, "ease-out"), (66, 0), (100, 0)])
    kf("tkdLegL", [(0, 25), (20, 25), (32, 12), (40, 10), (56, 12), (66, 25), (100, 25)])
    kf("tkdUp", [(0, 0), (20, 0), (32, -8), (40, -20), (48, -20), (56, -8), (66, 0), (100, 0)])
    CSS.append(f".{cls} .lR{{animation:tkdLegR {T}s infinite}}.{cls} .sR{{animation:tkdShinR {T}s infinite}}"
               f".{cls} .lL{{animation:tkdLegL {T}s infinite ease-in-out}}.{cls} .up{{animation:tkdUp {T}s infinite ease-in-out}}")

def burst(x, y, cls="burst"):
    return (f'<g class="{cls}" style="transform-origin:{x:g}px {y:g}px">' + L(x + 3, y - 6, x + 6, y - 10) + L(x + 4, y, x + 9, y)
            + L(x + 3, y + 6, x + 6, y + 10) + '</g>')

def kicker_bag(x, y, s):
    frame = L(20, -80, 56, -80) + L(56, -80, 56, 29)
    bag = ('<g class="bag" style="transform-origin:36px -80px">' + L(36, -80, 36, -64, "thin")
           + '<rect class="fill" x="30" y="-64" width="12" height="54" rx="4"/></g>')
    belt = '<rect class="fill" x="-4" y="-3.5" width="8" height="2.2"/>'
    body = fig("kicker", x, y, s, STANCE, dict(behind=frame, front=bag + burst(29, -2), back=belt))
    kick_css("kicker")
    kf("bagSwing", [(0, 0), (40, 0, "ease-out"), (48, -14, "ease-in-out"), (58, 7, "ease-in-out"), (68, -3, "ease-in-out"), (78, 1), (86, 0), (100, 0)])
    CSS.append(".kicker .bag{animation:bagSwing 3s infinite}"
               "@keyframes burst{0%,38%{opacity:0;transform:scale(.6)}42%{opacity:1;transform:scale(1)}52%,100%{opacity:0;transform:scale(1.3)}}"
               ".scene .burst{animation:burst 3s infinite}")
    return body

def kicker_board(x, y, s):
    # holder stands 50 units in front, facing back toward the kicker
    hx = x + 50 * s
    hA = arm((18.5, -11)); hB = arm((18.5, 1))
    holder = fig("holder", hx, y, s, dict(aR=hA[0], fR=hA[1], aL=hB[0], fL=hB[1], lL=-14, lR=12), flip=True)
    board = ('<g class="board-top" style="transform-origin:33px -3px"><rect class="woodboard" x="30.5" y="-13" width="3.2" height="10"/></g>'
             '<g class="board-bot" style="transform-origin:33px -3px"><rect class="woodboard" x="30.5" y="-3" width="3.2" height="10"/></g>')
    chips = "".join(f'<rect class="chip c{i}" x="31" y="-4" width="1.6" height="1.6"/>' for i in range(4))
    belt = '<rect class="fill" x="-4" y="-3.5" width="8" height="2.2"/>'
    kicker = fig("kicker2", x, y, s, STANCE, dict(back=belt, front=board + chips))
    kick_css("kicker2")
    CSS.append("@keyframes boardTop{0%,40%{transform:none;opacity:1}55%{transform:translate(7px,-9px) rotate(-40deg);opacity:1}"
               "75%{transform:translate(12px,18px) rotate(-70deg);opacity:0}92%{transform:none;opacity:0}100%{opacity:1}}"
               "@keyframes boardBot{0%,40%{transform:none;opacity:1}55%{transform:translate(8px,6px) rotate(40deg);opacity:1}"
               "75%{transform:translate(12px,26px) rotate(80deg);opacity:0}92%{transform:none;opacity:0}100%{opacity:1}}"
               ".kicker2 .board-top{animation:boardTop 3s infinite ease-out}.kicker2 .board-bot{animation:boardBot 3s infinite ease-out}"
               "@keyframes chip{0%,40%{opacity:0;transform:none}44%{opacity:1}70%,100%{opacity:0;transform:translate(var(--cx),var(--cy)) rotate(180deg)}}"
               ".kicker2 .chip{animation:chip 3s infinite ease-out;transform-box:fill-box;transform-origin:center}"
               ".kicker2 .c0{--cx:14px;--cy:-14px}.kicker2 .c1{--cx:18px;--cy:4px}.kicker2 .c2{--cx:10px;--cy:16px}.kicker2 .c3{--cx:20px;--cy:-4px}"
               "@keyframes holderFlinch{0%,40%{transform:rotate(0)}46%{transform:rotate(-7deg)}60%,100%{transform:rotate(0)}}"
               ".holder .up{animation:holderFlinch 3s infinite ease-out}")
    return holder + kicker

# ═════════════════════════ SCENES ═════════════════════════
def hero():
    G = 150; s = 1.25; y = G - 29 * s
    b = GROUND(20, 820, G)
    b += scientist(60, y, s) + juggler(315, y, s) + bassist(505, y, s) + kicker_bag(690, y, s)
    for cx, t in [(118, "01 — wet lab"), (330, "02 — juggling"), (520, "03 — principal bass"), (730, "04 — taekwondo")]:
        b += CAP(cx, G + 20, t)
    write("hero", svg("hero", "0 0 840 180", b, "Animated stick figures working in a lab, juggling a soccer ball, playing double bass, and kicking a heavy bag"))

def research():
    G = 150; s = 1.25; y = G - 29 * s; x = 100
    gun = ('<rect class="fill" x="-1.8" y="-4" width="3.6" height="14" rx="1"/>'
           '<rect class="fill" x="-7" y="-3" width="6" height="3" rx="1"/>'
           '<rect class="gold-fill" x="1.8" y="-1" width="3" height="7" rx="1.2"/>')
    aL = arm((20, -27))
    puff = '<circle class="puff" cx="37" cy="-28" r="3"/>'
    body = fig("gunner", x, y, s, dict(aR=-90, fR=0, aL=aL[0], fL=aL[1], lL=16, lR=-14), dict(hR=gun, front=puff))
    mx, my = x + 37 * s, y - 28 * s
    # plant
    px = 470
    plant = (f'<path class="pot" d="M{px-17} 128 L{px+17} 128 L{px+13} {G} L{px-13} {G} Z"/>'
             f'<path class="st" d="M{px} 128 C{px} 110 {px-3} 95 {px} 70"/>')
    leaves = [(px - 14, 104, 12, 5, -25), (px + 14, 96, 12, 5, 25), (px - 11, 84, 10, 4.2, -35), (px + 10, 76, 9, 4, 35), (px + 1, 66, 7, 3.6, -80)]
    for i, (cx, cy, rx, ry, a) in enumerate(leaves):
        plant += f'<ellipse class="leaf" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" transform="rotate({a} {cx} {cy})"/>'
    for i, (cx, cy, rx, ry, a) in enumerate(leaves):
        plant += f'<ellipse class="leaf-glow" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" transform="rotate({a} {cx} {cy})"/>'
    plant += f'<text class="cap gfp" x="{px+24}" y="62">GFP⁺</text>'
    parts = ""
    targets = [(-14, 104), (14, 96), (-11, 84), (10, 76), (1, 68), (-4, 100), (8, 88)]
    for i, (tx, ty) in enumerate(targets):
        dx, dy = px + tx - mx, ty - my
        parts += (f'<circle class="au p{i}" cx="{mx:.1f}" cy="{my:.1f}" r="2" '
                  f'style="--dx:{dx:.0f}px;--dy:{dy:.0f}px;animation-delay:{i * 0.045:.2f}s"/>')
    b = GROUND(20, 620, G) + plant + parts + body
    b += CAP(150, G + 20, "biolistics — gold microcarriers → plant cells") + CAP(470, G + 20, "transient GFP expression")
    CSS.append("@keyframes recoil{0%{transform:rotate(-90deg)}4%{transform:rotate(-99deg)}18%,100%{transform:rotate(-90deg)}}"
               ".gunner .aR{animation:recoil 1.4s infinite ease-out}"
               "@keyframes puff{0%{opacity:.55;transform:scale(.4)}30%,100%{opacity:0;transform:scale(2.4)}}"
               ".gunner .puff{animation:puff 1.4s infinite ease-out;transform-box:fill-box;transform-origin:center}"
               "@keyframes au{0%{opacity:1;transform:translate(0,0)}36%{opacity:1;transform:translate(var(--dx),var(--dy))}42%,100%{opacity:0;transform:translate(var(--dx),var(--dy))}}"
               ".scene .au{animation:au 1.4s infinite cubic-bezier(.3,.6,.4,1) both}"
               "@keyframes glow{0%{opacity:0}12%{opacity:.25}35%{opacity:.25}45%{opacity:.55}68%{opacity:.55}78%{opacity:.9}94%{opacity:.9}100%{opacity:0}}"
               ".scene .leaf-glow{animation:glow 4.2s infinite;animation-delay:.35s}"
               "@keyframes gfp{0%,70%{opacity:0}80%,94%{opacity:1}100%{opacity:0}}.scene .gfp{animation:gfp 4.2s infinite .35s;fill:var(--bio)}")
    write("research", svg("research", "0 0 640 180", b, "Animated stick figure firing gold particles from a gene gun at a plant, which glows green"))

def experience():
    G = 150; s = 1.65; y = G - 29 * s; x = 110
    clip = ('<rect class="paper" x="10" y="-25" width="12" height="16" rx="1.5" transform="rotate(8 16 -17)"/>'
            '<rect class="fill" x="13.5" y="-26.5" width="5" height="2.5" rx="1" transform="rotate(8 16 -17)"/>'
            + L(12.6, -20, 19.4, -19, "hair") + L(12.4, -17, 19, -16, "hair") + L(12.2, -14, 17, -13.3, "hair"))
    aL = arm((13, -12)); w1, w2 = arm((15, -20)), arm((18, -18))
    pen = L(0, -3, -1.5, 3, "thin")
    steth = '<path class="st hair" d="M-3 -33 C-6 -24 -1 -21 2 -22 M3 -33 C5 -28 4 -24 2 -22"/><circle class="fill" cx="2" cy="-22" r="1.2"/>'
    fig1 = fig("clinician", x, y, s, dict(aL=aL[0], fL=aL[1], aR=w1[0], fR=w1[1], lL=8, lR=-6), dict(front=clip, hR=pen, head=steth))
    kf("writeArm", [(0, w1[0]), (100, w2[0])]); kf("writeFore", [(0, w1[1]), (100, w2[1])])
    mon = ('<rect class="screen" x="210" y="34" width="170" height="80" rx="8"/>' + L(295, 114, 295, G) + L(272, G, 318, G)
           + '<path class="ekg" pathLength="100" d="M222 84 H252 L257 80 L262 84 H270 L274 90 L280 52 L286 100 L291 84 H302 L308 76 L316 84 H332 L337 80 L342 84 H368"/>'
           + '<text class="cap" x="224" y="52" text-anchor="start">HR 72 BPM</text>'
           + '<path class="heart" d="M362 48 c-2-3-7-2-7 2 c0 3 4 5 7 8 c3-3 7-5 7-8 c0-4-5-5-7-2z"/>')
    px1, px2 = 440, 590
    printer = (f'<rect class="st" x="{px1}" y="40" width="{px2-px1}" height="110" rx="6"/>' + L(px1 + 8, 62, px2 - 8, 62)
               + L(px1 + 14, 140, px2 - 14, 140)
               + f'<g class="nozzle"><rect class="fill" x="{px1+14}" y="58" width="16" height="10" rx="2"/><path class="fill" d="M{px1+19} 68 h6 l-3 5z"/></g>'
               + f'<g class="printed" style="transform-origin:515px 140px"><rect class="paper" x="490" y="104" width="50" height="36" rx="2"/>'
               + "".join(L(492, 108 + k * 5, 538, 108 + k * 5, "hair") for k in range(7)) + '</g>')
    b = GROUND(20, 620, G) + mon + printer + fig1
    b += CAP(150, G + 20, "clinical — vitals & EKG") + CAP(515, G + 20, "design — rapid prototyping")
    CSS.append(".clinician .aR{animation:writeArm .45s infinite alternate ease-in-out}.clinician .fR{animation:writeFore .45s infinite alternate ease-in-out}"
               "@keyframes ekg{0%{stroke-dashoffset:100;opacity:1}70%{stroke-dashoffset:0;opacity:1}90%,100%{stroke-dashoffset:0;opacity:0}}"
               ".scene .ekg{fill:none;stroke:var(--bio);stroke-width:1.8;stroke-linejoin:round;stroke-dasharray:100;animation:ekg 2.4s infinite linear}"
               "@keyframes beat{0%,100%{transform:scale(1)}12%{transform:scale(1.25)}24%{transform:scale(1)}36%{transform:scale(1.15)}}"
               ".scene .heart{fill:var(--bio);transform-box:fill-box;transform-origin:center;animation:beat 1.2s infinite}"
               "@keyframes nozzle{0%{transform:translateX(0)}100%{transform:translateX(116px)}}"
               ".scene .nozzle{animation:nozzle 1.1s infinite alternate ease-in-out}"
               "@keyframes printed{0%{transform:scaleY(0);opacity:1}85%{transform:scaleY(1);opacity:1}96%,100%{transform:scaleY(1);opacity:0}}"
               ".scene .printed{animation:printed 9s infinite linear}")
    write("experience", svg("experience", "0 0 640 180", b, "Animated stick figure writing on a clipboard next to an EKG monitor and a 3D printer"))

def projects():
    G = 115; T = 14
    plants = [90 + 100 * i for i in range(6)]
    pl = ""
    for i, px in enumerate(plants):
        pl += (f'<g transform="translate({px} {G}) scale(1.5) translate({-px} {-G})"><g class="sprout sp{i}">' + L(px, G, px, G - 16)
               + f'<ellipse class="sleaf" cx="{px-5}" cy="{G-11}" rx="5" ry="2.4" transform="rotate(-30 {px-5} {G-11})"/>'
               + f'<ellipse class="sleaf" cx="{px+5}" cy="{G-15}" rx="5" ry="2.4" transform="rotate(30 {px+5} {G-15})"/></g></g>'
               + f'<circle class="ping pg{i}" cx="{px}" cy="{G-12}" r="5"/>')
    wheel = lambda cx: (f'<g class="wheel" style="transform-origin:{cx}px -6px"><circle class="head" cx="{cx}" cy="-6" r="6"/>'
                        + L(cx - 6, -6, cx + 6, -6, "thin") + L(cx, -12, cx, 0, "thin") + '</g>')
    rover = ('<g class="rover">' + '<rect class="paper" x="-22" y="-26" width="44" height="15" rx="3"/>'
             + L(-20, -30, 6, -30) + L(-7, -30, -7, -26, "thin") + L(16, -26, 16, -40) + '<circle class="fill" cx="16" cy="-42" r="2.6"/>'
             + L(22, -18, 30, -18) + '<g class="probe">' + L(30, -18, 30, -6) + '<circle class="fill" cx="30" cy="-5" r="1.6"/></g>'
             + wheel(-13) + wheel(13) + f'<text class="cap" x="-17" y="-15.5" text-anchor="start" style="font-size:6px">PRAIRI</text></g>')
    rv = f'<g class="rover-move"><g transform="translate(0 {G}) scale(1.5)">{rover}</g></g>'
    # rover keyframes: drive, stop, probe, drive...
    xs, probe, pings, leaves, wheels = [], [], {}, {}, []
    start = -90
    xs.append((0, start, "ease-in-out")); wheels.append((0, 0))
    t = 0
    prev = start
    for i, px in enumerate(plants):
        rx = px - 45
        arrive = (t + 1.3) / T * 100; leave = (t + 2.1) / T * 100
        xs += [(arrive, rx), (leave, rx, "ease-in-out")]
        ang = (rx - start) / 9 * 57.3
        wheels += [(arrive, ang), (leave, ang)]
        probe += [((t + 1.4) / T * 100, 0, "ease-in"), ((t + 1.6) / T * 100, 1), ((t + 1.85) / T * 100, 1, "ease-out"), ((t + 2.0) / T * 100, 0)]
        pings[i] = (t + 1.6) / T * 100
        t += 2.1
    end = 740
    xs += [(100 * (t + 1.6) / T, end), (100, end)]
    wheels += [(100 * (t + 1.6) / T, (end - start) / 9 * 57.3), (100, (end - start) / 9 * 57.3)]
    kf("roverX", [xs[0]] + xs[1:], "tx")
    kf("wheel", wheels)
    pf = [(0, 0)] + probe + [(100, 0)]
    CSS.append("@keyframes probe{" + "".join(f"{p:.2f}%{{transform:scaleY({1 if v else .25})}}" for p, v, *_ in pf) + "}")
    for i, p in pings.items():
        CSS.append(f"@keyframes ping{i}{{0%,{p:.2f}%{{opacity:0;transform:scale(.5)}}{p+.3:.2f}%{{opacity:.8;transform:scale(.6)}}{p+6:.2f}%,100%{{opacity:0;transform:scale(3.2)}}}}"
                   f".scene .pg{i}{{animation:ping{i} {T}s infinite ease-out}}"
                   f"@keyframes leaf{i}{{0%,{p:.2f}%{{fill:var(--bg)}}{p+1.5:.2f}%,96%{{fill:var(--bio)}}100%{{fill:var(--bg)}}}}"
                   f".scene .sp{i} .sleaf{{animation:leaf{i} {T}s infinite}}")
    CSS.append(f".scene .rover-move{{animation:roverX {T}s infinite}}.scene .wheel{{animation:wheel {T}s infinite}}"
               f".scene .probe{{transform-origin:30px -18px;animation:probe {T}s infinite}}"
               ".scene .ping{fill:none;stroke:var(--bio);stroke-width:1;transform-box:fill-box;transform-origin:center}")
    b = GROUND(0, 640, G) + pl + rv + CAP(320, G + 22, "prairi — autonomous soil & plant health mapping")
    write("projects", svg("projects", "0 0 640 150", b, "Animated rover driving along a crop row, probing each plant"))

def soccer():
    G = 140; s = 1.2; y = G - 29 * s; T = 6
    runner = fig("runner", 0, y, s, dict(up=12, aL=-45, fL=-80, aR=40, fR=-80, lL=35, sL=75, lR=-45, sR=25), move="run-move")
    striker = fig("striker", 300, y, s, dict(aL=25, aR=-25, fL=-20, fR=-20, lR=30, sR=60, lL=-5), move="striker-move")
    goal = ('<path class="st" d="M405 140 V86 H446 L466 140"/>'
            '<g class="net" style="transform-origin:405px 113px">'
            + "".join(L(405 + k * 8, 86, 405 + k * 8 + (k * 8) * 20 / 41, 140, "hair") for k in range(1, 6))
            + "".join(L(405, 86 + k * 9, 446 + (k * 9) * 20 / 54, 86 + k * 9, "hair") for k in range(1, 6)) + '</g>')
    bl = f'<g class="sball-x"><g class="sball-y"><g class="spinner">{ball(5)}</g></g></g>'
    goaltxt = '<text class="goal-txt" x="425" y="72" text-anchor="middle">GOAL!</text>'
    b = GROUND(0, 480, G) + goal + runner + striker + bl + goaltxt
    kf("runLeg", [(0, 35), (50, -45), (100, 35)]); kf("runShin", [(0, 80), (30, 60), (50, 20), (75, 50), (100, 80)])
    kf("runArm", [(0, -45), (50, 40), (100, -45)])
    kf("runX", [(0, -30), (55, 296), (100, 296)], "tx")
    kf("strLeg", [(0, 30), (55, 30, "ease-in"), (57.5, 50, "ease-in"), (59, -25), (61, -70, "ease-out"), (65, -5), (100, -5)])
    kf("strShin", [(0, 60), (55, 60), (57.5, 95), (59, 15), (61, 0), (65, 0), (100, 0)])
    kf("strArmL", [(0, 25), (64, 25, "ease-out"), (69, 165), (88, 165), (92, 25), (100, 25)])
    kf("strArmR", [(0, -25), (64, -25, "ease-out"), (69, -165), (88, -165), (92, -25), (100, -25)])
    kf("strY", [(0, 0), (70, 0, "ease-out"), (73.5, -14, "ease-in"), (77, 0, "ease-out"), (80.5, -14, "ease-in"), (84, 0), (100, 0)], "ty")
    kf("sbx", [(0, -8, "linear"), (55, 318, "linear"), (59, 318, "cubic-bezier(.2,.7,.4,1)"), (67, 432), (90, 432), (100, 432)], "tx")
    kf("sby", [(0, 135), (59, 135, "cubic-bezier(.2,.8,.5,1)"), (62.5, 98, "cubic-bezier(.5,0,.8,.6)"), (67, 122, "ease-in"), (70, 135, "ease-out"), (72, 130, "ease-in"), (74, 135), (100, 135)], "ty")
    CSS.append(f".runner .lL,.runner .lR{{animation:runLeg .5s infinite linear}}.runner .sL,.runner .sR{{animation:runShin .5s infinite linear}}"
               f".runner .lR,.runner .sR{{animation-delay:-.25s}}"
               f".runner .aL,.runner .aR{{animation:runArm .5s infinite ease-in-out}}.runner .aL{{animation-delay:-.25s}}"
               "@keyframes bob{0%,50%,100%{transform:translateY(0)}25%,75%{transform:translateY(-2.5px)}}.runner{animation:bob .5s infinite}"
               f"@keyframes runVis{{0%{{opacity:0}}3%,54.8%{{opacity:1}}55%,100%{{opacity:0}}}}"
               f".scene .run-move{{animation:runX {T}s infinite linear,runVis {T}s infinite}}"
               f"@keyframes strVis{{0%,54.8%{{opacity:0}}55%,90%{{opacity:1}}95%,100%{{opacity:0}}}}"
               f".scene .striker-move{{animation:strVis {T}s infinite,strY {T}s infinite}}"
               f".striker .lR{{animation:strLeg {T}s infinite}}.striker .sR{{animation:strShin {T}s infinite}}"
               f".striker .aL{{animation:strArmL {T}s infinite}}.striker .aR{{animation:strArmR {T}s infinite}}"
               f"@keyframes sVis{{0%{{opacity:0}}3%,90%{{opacity:1}}95%,100%{{opacity:0}}}}"
               f".scene .sball-x{{animation:sbx {T}s infinite,sVis {T}s infinite}}.scene .sball-y{{animation:sby {T}s infinite}}"
               ".scene .spinner{animation:spin .6s linear infinite}"
               f"@keyframes net{{0%,66%{{transform:none}}70%{{transform:translateX(5px) scaleX(1.12)}}78%,100%{{transform:none}}}}"
               f".scene .net{{animation:net {T}s infinite ease-out}}"
               f"@keyframes goalTxt{{0%,67%{{opacity:0;transform:translateY(6px)}}71%,88%{{opacity:1;transform:none}}93%,100%{{opacity:0}}}}"
               f".scene .goal-txt{{animation:goalTxt {T}s infinite ease-out}}")
    write("soccer", svg("soccer", "0 0 480 165", b, "Animated stick figure dribbling a soccer ball across the page and scoring a goal"))

def bass_scene():
    G = 140; s = 1.45; y = G - 29 * s
    staff = "".join(L(215, 44 + k * 7, 465, 44 + k * 7, "staff") for k in range(5))
    b = GROUND(0, 480, G) + staff + bassist(150, y, s, cls="bassist2", notes=5)
    CSS.append("@keyframes noteFloat2{0%{opacity:0;transform:translate(0,0) rotate(0)}12%{opacity:1}80%{opacity:1}100%{opacity:0;transform:translate(170px,-6px) rotate(8deg)}}"
               ".bassist2 .note{animation:noteFloat2 5s infinite ease-out}"
               + "".join(f".bassist2 .n{i}{{animation-delay:{-i:.2f}s}}" for i in range(5)))
    write("bass", svg("bass", "0 0 480 165", b, "Animated stick figure playing the double bass with music notes floating off"))

def tkd_scene():
    G = 140; s = 1.3; y = G - 29 * s
    b = GROUND(0, 480, G) + kicker_board(160, y, s)
    write("taekwondo", svg("taekwondo", "0 0 480 165", b, "Animated stick figure breaking a board with a taekwondo kick"))

def blog():
    G = 135; s = 1.2; y = G - 14 * s; up = 15
    kL, kR = arm((19, -9), up), arm((24, -8), up)
    chair = L(-9, 1.5, 6, 1.5) + L(-9, 1.5, -9, -24) + L(-7, 1.5, -7, 14, "thin") + L(4, 1.5, 4, 14, "thin")
    desk = ('<rect class="fill" x="14" y="-8.6" width="52" height="2" rx="1"/>' + L(18, -7, 18, 14, "thin") + L(62, -7, 62, 14, "thin")
            + L(17, -10, 33, -10) + L(33, -10, 37, -27)
            + '<rect class="paper" x="50" y="-15" width="6" height="6.5" rx="1"/><path class="st hair steam" d="M52 -17 q-1.5 -2 0 -4 q1.5 -2 0 -4"/>')
    body = fig("typist", 160, y, s, dict(up=up, aL=kL[0], fL=kL[1], aR=kR[0], fR=kR[1], lL=-90, sL=90, lR=-86, sR=86), dict(behind=chair + desk))
    page = ('<rect class="paper" x="300" y="22" width="110" height="92" rx="6"/>'
            + "".join(f'<rect class="line ln{k}" x="314" y="{40 + k * 12}" width="{w}" height="3" rx="1.5"/>' for k, w in enumerate([80, 70, 82, 54, 66]))
            + '<rect class="cursor" x="314" y="88" width="2" height="9"/>')
    b = GROUND(60, 460, G) + page + body + CAP(250, G + 20, "drafting the next post")
    kf("typeL", [(0, kL[1] - 6), (100, kL[1] + 6)]); kf("typeR", [(0, kR[1] + 6), (100, kR[1] - 6)])
    CSS.append(".typist .fL{animation:typeL .22s infinite alternate}.typist .fR{animation:typeR .19s infinite alternate}"
               "@keyframes steam{0%{opacity:0;transform:translateY(2px)}50%{opacity:.8}100%{opacity:0;transform:translateY(-4px)}}"
               ".typist .steam{animation:steam 2s infinite}"
               ".scene .line{fill:var(--line);transform-box:fill-box;transform-origin:left center}"
               + "".join(f"@keyframes ln{k}{{0%,{k*15}%{{transform:scaleX(0)}}{k*15+13}%,92%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}.scene .ln{k}{{animation:ln{k} 7s infinite linear}}" for k in range(5))
               + "@keyframes blink{50%{opacity:0}}.scene .cursor{fill:var(--text);animation:blink 1s steps(1) infinite}")
    write("blog", svg("blog", "0 0 480 160", b, "Animated stick figure typing at a laptop while lines of a blog post appear"))

def profile():
    G = 120; s = 1.2; y = G - 29 * s
    body = fig("waver", 60, y, s, dict(aR=-150, fR=-20, aL=12, fL=-8, lL=7, lR=-7))
    bubble = ('<g class="bubble-say"><rect class="paper" x="86" y="22" width="108" height="26" rx="13"/>'
              '<path class="paper" d="M98 46 l-6 10 l14 -9z"/>'
              '<text class="cap" x="140" y="39" text-anchor="middle" style="fill:var(--text)">hi, I\'m Yuvin</text></g>')
    b = GROUND(20, 180, G) + bubble + body
    kf("wave", [(0, -25), (100, 25)])
    CSS.append(".waver .fR{animation:wave .45s infinite alternate ease-in-out}"
               "@keyframes say{0%{opacity:0;transform:translateY(4px)}10%,85%{opacity:1;transform:none}100%{opacity:0}}"
               ".scene .bubble-say{animation:say 5s infinite}")
    write("profile", svg("profile", "0 0 210 140", b, "Animated stick figure waving hello"))

# ═════════════════════════ BASE STYLES ═════════════════════════
BASE = """/* GENERATED by _tools/scenes.py — edit that file, then re-run it. */
.scene{display:block;width:100%;height:auto;overflow:hidden;--ink:var(--text)}
.scene line,.scene .st{stroke:var(--ink);stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;fill:none}
.scene .thin{stroke-width:1.1}.scene .hair{stroke-width:.7}.scene .thick{stroke-width:3.2}
.scene .head{fill:var(--bg);stroke:var(--ink);stroke-width:1.7}
.scene .fill{fill:var(--ink);stroke:none}
.scene .ground{stroke:var(--line);stroke-width:1}
.scene .staff{stroke:var(--line);stroke-width:1}
.scene .cap{font-family:var(--font-mono);font-size:10px;fill:var(--muted);letter-spacing:.06em}
.scene .ball{fill:var(--bg);stroke:var(--ink);stroke-width:1.3}
.scene .coat{fill:var(--bg);stroke:var(--ink);stroke-width:1}
.scene .tube{fill:#e9f8f0;stroke:var(--ink);stroke-width:.8}
.scene .liquid{fill:var(--bio);opacity:.35}
.scene .bubble{fill:var(--bio);opacity:0}
.scene .drop{fill:var(--bio)}
.scene .wood{fill:#f3ece4;stroke:var(--ink);stroke-width:1.3}
.scene .woodboard{fill:#efe2cf;stroke:var(--ink);stroke-width:1}
.scene .chip{fill:#c9ab83;opacity:0}
.scene .paper,.scene .screen{fill:var(--bg);stroke:var(--ink);stroke-width:1.3}
.scene .pot{fill:#f4f1ee;stroke:var(--ink);stroke-width:1.3}
.scene .leaf{fill:var(--bg);stroke:var(--ink);stroke-width:1.3}
.scene .leaf-glow{fill:var(--bio);opacity:0;filter:drop-shadow(0 0 4px var(--bio))}
.scene .au{fill:var(--gold);filter:drop-shadow(0 0 1.5px var(--gold));opacity:0}
.scene .gold-fill{fill:var(--gold)}
.scene .puff{fill:#cfd5db;opacity:0}
.scene .sleaf{fill:var(--bg);stroke:var(--ink);stroke-width:1.1}
.scene .note .fill{fill:var(--ink)}.scene .note{opacity:0}
.scene .burst line{stroke:var(--gold);stroke-width:1.6}.scene .burst{opacity:0}
.scene .goal-txt{font-family:var(--font-mono);font-size:12px;font-weight:500;letter-spacing:.12em;fill:var(--bio);opacity:0}
@keyframes spin{to{transform:rotate(360deg)}}
.scene .spinner{transform-box:fill-box;transform-origin:center}
.scene:not(.in-view) *{animation-play-state:paused!important}
"""

if __name__ == "__main__":
    hero(); research(); experience(); projects(); soccer(); bass_scene(); tkd_scene(); blog(); profile()
    with open(os.path.join(ROOT, "assets", "css", "scenes.css"), "w") as f:
        f.write(BASE + "\n".join(CSS) + "\n")
    print("scenes written:", sorted(os.listdir(INC)))
