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


def sfx(x, y, word, cls, scale=1.0, rot=-8, color="var(--pop)"):
    """Comic sound-effect starburst (e.g. POW!) that pops on a keyframe schedule set via CSS class `cls`."""
    pts = []
    for k in range(24):
        a = math.radians(k * 15 - 90); r = 40 if k % 2 == 0 else 27
        pts.append(f"{r * math.cos(a) * 1.35:.1f},{r * math.sin(a):.1f}")
    tl = min(78, 14 * len(word) + 6)
    return (f'<g class="sfx-pop {cls}" style="transform-origin:{x:g}px {y:g}px"><g transform="translate({x:g} {y:g}) rotate({rot}) scale({scale})">'
            f'<polygon class="sfx-burst" points="{" ".join(pts)}" style="fill:{color}"/>'
            f'<text class="sfx-text" x="0" y="7" text-anchor="middle" textLength="{tl}" lengthAdjust="spacingAndGlyphs">{word}</text></g></g>')

def pop_css(cls, start, end, period):
    """Keyframes: hidden → pop in at start% → hold → out by end%."""
    CSS.append(f"@keyframes {cls}{{0%,{start:g}%{{opacity:0;transform:scale(.2) rotate(-20deg)}}{start+3:g}%{{opacity:1;transform:scale(1.15) rotate(4deg)}}{start+6:g}%{{transform:scale(1) rotate(0)}}{end-3:g}%{{opacity:1;transform:scale(1)}}{end:g}%,100%{{opacity:0;transform:scale(.6)}}}}"
               f".scene .{cls}{{animation:{cls} {period}s infinite}}")

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
    ex = dict(front='<g class="jbx"><g class="jby"><g class="spinner">' + ball() + '</g></g></g>' + sfx(30, -62, 'OOPS!', 'oops', .5, 6, 'var(--pop-2)'))
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
    pop_css("oops", 72, 90, T)
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
    body = fig("kicker", x, y, s, STANCE, dict(behind=frame, front=bag + burst(29, -2) + sfx(52, -58, 'POW!', 'pow-bag', .55), back=belt))
    kick_css("kicker")
    kf("bagSwing", [(0, 0), (40, 0, "ease-out"), (48, -14, "ease-in-out"), (58, 7, "ease-in-out"), (68, -3, "ease-in-out"), (78, 1), (86, 0), (100, 0)])
    pop_css("pow-bag", 40, 62, 3)
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
    kicker = fig("kicker2", x, y, s, STANCE, dict(back=belt, front=board + chips + sfx(40, -46, 'CRACK!', 'crack', .62)))
    kick_css("kicker2")
    pop_css("crack", 40, 66, 3)
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
    for cx, t in [(118, "01 — Research"), (330, "02 — Soccer"), (520, "03 — Double Bassist"), (730, "04 — Taekwondo")]:
        b += CAP(cx, G + 20, t)
    write("hero", svg("hero", "0 0 840 180", b, "Animated stick figures: one doing lab research, one juggling a soccer ball, one playing double bass, one practicing taekwondo"))

def biolistics():
    G = 180; s = 1.3; y = G - 29 * s; x = 58
    gun = ('<rect class="fill" x="-1.8" y="-4" width="3.6" height="14" rx="1"/>'
           '<rect class="fill" x="-7" y="-3" width="6" height="3" rx="1"/>'
           '<rect class="gold-fill" x="1.8" y="-1" width="3" height="7" rx="1.2"/>')
    aL = arm((20, -27))
    puff = '<circle class="puff" cx="37" cy="-28" r="3"/>'
    body = fig("gunner", x, y, s, dict(aR=-90, fR=0, aL=aL[0], fL=aL[1], lL=16, lR=-14), dict(hR=gun, front=puff + sfx(44, -52, 'ZAP!', 'zap', .5, -10)))
    mx, my = x + 37 * s, y - 28 * s
    px = 252
    plant = (f'<path class="pot" d="M{px-17} {G-22} L{px+17} {G-22} L{px+13} {G} L{px-13} {G} Z"/>'
             f'<path class="st" d="M{px} {G-22} C{px} {G-40} {px-3} {G-55} {px} {G-80}"/>')
    leaves = [(px - 14, G - 46, 12, 5, -25), (px + 14, G - 54, 12, 5, 25), (px - 11, G - 66, 10, 4.2, -35), (px + 10, G - 74, 9, 4, 35), (px + 1, G - 84, 7, 3.6, -80)]
    for cls in ("leaf", "leaf-glow"):
        for (cx, cy, rx, ry, a) in leaves:
            plant += f'<ellipse class="{cls}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" transform="rotate({a} {cx} {cy})"/>'
    plant += f'<text class="cap gfp" x="{px+20}" y="{G-92}">GFP⁺</text>'
    parts = ""
    for i, (tx, ty) in enumerate([(-14, -46), (14, -54), (-11, -66), (10, -74), (1, -82), (-4, -50), (8, -62)]):
        dx, dy = px + tx - mx, G + ty - my
        parts += (f'<circle class="au p{i}" cx="{mx:.1f}" cy="{my:.1f}" r="2" '
                  f'style="--dx:{dx:.0f}px;--dy:{dy:.0f}px;animation-delay:{i * 0.045:.2f}s"/>')
    b = GROUND(10, 310, G) + plant + parts + body + CAP(14, 22, "Au → Nicotiana / Allium", "start")
    pop_css("zap", 0, 22, 2.8)
    CSS.append("@keyframes recoil{0%{transform:rotate(-90deg)}4%{transform:rotate(-99deg)}18%,100%{transform:rotate(-90deg)}}"
               ".gunner .aR{animation:recoil 1.4s infinite ease-out}"
               "@keyframes puff{0%{opacity:.55;transform:scale(.4)}30%,100%{opacity:0;transform:scale(2.4)}}"
               ".gunner .puff{animation:puff 1.4s infinite ease-out;transform-box:fill-box;transform-origin:center}"
               "@keyframes au{0%{opacity:1;transform:translate(0,0)}36%{opacity:1;transform:translate(var(--dx),var(--dy))}42%,100%{opacity:0;transform:translate(var(--dx),var(--dy))}}"
               ".scene .au{animation:au 1.4s infinite cubic-bezier(.3,.6,.4,1) both}"
               "@keyframes glow{0%{opacity:0}12%{opacity:.25}35%{opacity:.25}45%{opacity:.55}68%{opacity:.55}78%{opacity:.9}94%{opacity:.9}100%{opacity:0}}"
               ".scene .leaf-glow{animation:glow 4.2s infinite;animation-delay:.35s}"
               "@keyframes gfp{0%,70%{opacity:0}80%,94%{opacity:1}100%{opacity:0}}.scene .gfp{animation:gfp 4.2s infinite .35s;fill:var(--bio)}")
    write("biolistics", svg("biolistics", "0 0 320 200", b, "Stick figure firing gold microcarriers from a gene gun at a plant, which glows green"))

def bioscaffold():
    G = 150; s = 1.2; y = G - 29 * s; x = 70; T = 7
    t1, t2 = (28, -30), (30, -14)
    a1, a2 = arm(t1), arm(t2)
    tot2 = a2[0] + a2[1]
    sx0, sw, sh = 151, 41, 22
    top_final = 152
    hand2 = (x + t2[0] * s, y + t2[1] * s)
    tip = (sx0 + sw / 2, top_final)
    v = ((tip[0] - hand2[0]) / s, (tip[1] - hand2[1]) / s)       # hand → tip, figure-local units
    lw, lh = sw / s, sh / s
    tipL = (v[0], v[1] - 3)
    carry = (f'<g class="carry"><rect class="scaf-carry" x="{tipL[0]-lw/2:.2f}" y="{tipL[1]:.2f}" width="{lw:.2f}" height="{lh:.2f}" rx="1.6"/>'
             + "".join(L(round(tipL[0] - lw / 2 + k * lw / 6, 2), round(tipL[1], 2), round(tipL[0] - lw / 2 + k * lw / 6, 2), round(tipL[1] + lh, 2), "mesh") for k in range(1, 6))
             + "".join(L(round(tipL[0] - lw / 2, 2), round(tipL[1] + k * lh / 4, 2), round(tipL[0] + lw / 2, 2), round(tipL[1] + k * lh / 4, 2), "mesh") for k in range(1, 4))
             + '</g>')
    forceps = upright(L(0, -3, tipL[0] - 1, tipL[1], "thin") + L(0, -3, tipL[0] + 1, tipL[1], "thin") + carry, tot2)
    body = fig("surgeon", x, y, s, dict(aR=a1[0], fR=a1[1], aL=12, fL=-10, lL=8, lR=-6),
               dict(hR=forceps, back='<path class="coat" d="M-5 -30 L5 -30 L8 -1 L-8 -1 Z"/>'))
    skin = (f'<rect class="dermis" x="10" y="{G+25}" width="300" height="30"/>'
            f'<rect class="dermis" x="10" y="{G+6}" width="141" height="20"/><rect class="dermis" x="192" y="{G+6}" width="118" height="20"/>'
            f'<rect class="epi" x="10" y="{G}" width="141" height="6"/><rect class="epi" x="192" y="{G}" width="118" height="6"/>'
            f'<rect class="wound" x="151" y="{G}" width="41" height="25"/>')
    mesh = "".join(L(sx0 + k * 6.8, top_final, sx0 + k * 6.8, top_final + sh, "mesh") for k in range(1, 6))
    mesh += "".join(L(sx0, top_final + k * 5.5, sx0 + sw, top_final + k * 5.5, "mesh") for k in range(1, 4))
    placed = f'<g class="placed"><rect class="scaf" x="{sx0}" y="{top_final}" width="{sw}" height="{sh}" rx="2"/>{mesh}</g>'
    cells = ""
    starts = [(128, 170, "c-teal"), (138, 182, "c-gold"), (122, 160, "c-coral"), (206, 168, "c-teal"), (214, 182, "c-coral"), (200, 160, "c-gold")]
    ends = [(158, 160), (166, 168), (162, 156), (184, 160), (178, 168), (172, 156)]
    for i, ((cx, cy, c), (ex_, ey)) in enumerate(zip(starts, ends)):
        cells += f'<circle class="cell {c}" cx="{cx}" cy="{cy}" r="3" style="--dx:{ex_-cx}px;--dy:{ey-cy}px;animation-delay:{i*0.12:.2f}s"/>'
    stain = f'<rect class="stain" x="10" y="{G}" width="300" height="55"/>'
    labels = (CAP(14, 22, "porcine ECM bioscaffold → wound bed", "start")
              + f'<text class="cap he" x="306" y="{G-8}" text-anchor="end">H&amp;E · day 14</text>')
    b = skin + placed + cells + stain + body + labels
    kf("placeArm", [(0, a1[0], "ease-in-out"), (22, a2[0]), (30, a2[0], "ease-in-out"), (40, a1[0]), (100, a1[0])])
    kf("placeFore", [(0, a1[1], "ease-in-out"), (22, a2[1]), (30, a2[1], "ease-in-out"), (40, a1[1]), (100, a1[1])])
    CSS.append(f".surgeon .aR{{animation:placeArm {T}s infinite}}.surgeon .fR{{animation:placeFore {T}s infinite}}"
               f"@keyframes carry{{0%,22%{{opacity:1}}22.5%,94%{{opacity:0}}98%,100%{{opacity:1}}}}.surgeon .carry{{animation:carry {T}s infinite}}"
               f"@keyframes placed{{0%,22%{{opacity:0}}22.5%,92%{{opacity:1}}96%,100%{{opacity:0}}}}.scene .placed{{animation:placed {T}s infinite}}"
               f"@keyframes scafFill{{0%,40%{{fill:var(--tint-soft)}}70%,92%{{fill:#f6c9d6}}100%{{fill:var(--tint-soft)}}}}"
               f".scene .scaf{{animation:scafFill {T}s infinite}}"
               f"@keyframes cell{{0%,32%{{opacity:0;transform:none}}36%{{opacity:1;transform:none}}64%,90%{{opacity:1;transform:translate(var(--dx),var(--dy))}}95%,100%{{opacity:0;transform:translate(var(--dx),var(--dy))}}}}"
               f".scene .cell{{animation:cell {T}s infinite ease-in-out}}"
               f"@keyframes stain{{0%,72%{{opacity:0}}78%,90%{{opacity:.35}}96%,100%{{opacity:0}}}}"
               f".scene .stain{{fill:#b06ab3;animation:stain {T}s infinite}}"
               f"@keyframes he{{0%,72%{{opacity:0}}78%,90%{{opacity:1}}96%,100%{{opacity:0}}}}.scene .he{{fill:#8e3b91;animation:he {T}s infinite}}")
    write("bioscaffold", svg("bioscaffold", "0 0 320 210", b, "Stick figure placing a porous bioscaffold into a skin wound; cells migrate in and the tissue integrates"))

def rover():
    G = 160; T = 9
    plants = [80, 165, 250]
    pl = ""
    for i, px in enumerate(plants):
        pl += (f'<g transform="translate({px} {G}) scale(1.6) translate({-px} {-G})"><g class="sprout sp{i}">' + L(px, G, px, G - 16)
               + f'<ellipse class="sleaf" cx="{px-5}" cy="{G-11}" rx="5" ry="2.4" transform="rotate(-30 {px-5} {G-11})"/>'
               + f'<ellipse class="sleaf" cx="{px+5}" cy="{G-15}" rx="5" ry="2.4" transform="rotate(30 {px+5} {G-15})"/></g></g>'
               + f'<circle class="ping pg{i}" cx="{px}" cy="{G-14}" r="5"/>')
    wheel = lambda cx: (f'<g class="wheel" style="transform-origin:{cx}px -6px"><circle class="head" cx="{cx}" cy="-6" r="6"/>'
                        + L(cx - 6, -6, cx + 6, -6, "thin") + L(cx, -12, cx, 0, "thin") + '</g>')
    rov = ('<g class="rover">' + '<rect class="tintbox" x="-22" y="-26" width="44" height="15" rx="3"/>'
           + L(-20, -30, 6, -30) + L(-7, -30, -7, -26, "thin") + L(16, -26, 16, -40) + '<circle class="gold-fill" cx="16" cy="-42" r="2.6"/>'
           + L(22, -18, 30, -18) + '<g class="probe">' + L(30, -18, 30, -6) + '<circle class="fill" cx="30" cy="-5" r="1.6"/></g>'
           + wheel(-13) + wheel(13) + '<text class="cap" x="-17" y="-15.5" text-anchor="start" style="font-size:6px">PRARI</text></g>')
    S = 1.5
    rv = f'<g class="rover-move"><g transform="translate(0 {G}) scale({S})">{rov}</g></g>'
    xs, probe, pings, wheels = [], [], {}, []
    start = -90
    xs.append((0, start, "ease-in-out")); wheels.append((0, 0))
    t = 0
    for i, px in enumerate(plants):
        rx = px - 30 * S
        arrive = (t + 1.3) / T * 100; leave = (t + 2.1) / T * 100
        xs += [(arrive, rx), (leave, rx, "ease-in-out")]
        ang = (rx - start) / (6 * S) * 57.3
        wheels += [(arrive, ang), (leave, ang)]
        probe += [((t + 1.4) / T * 100, 0, "ease-in"), ((t + 1.6) / T * 100, 1), ((t + 1.85) / T * 100, 1, "ease-out"), ((t + 2.0) / T * 100, 0)]
        pings[i] = (t + 1.6) / T * 100
        t += 2.1
    end = 400
    xs += [(100 * (t + 1.6) / T, end), (100, end)]
    wa = (end - start) / (6 * S) * 57.3
    wheels += [(100 * (t + 1.6) / T, wa), (100, wa)]
    kf("roverX", xs, "tx"); kf("wheel", wheels)
    pf = [(0, 0)] + probe + [(100, 0)]
    CSS.append("@keyframes probe{" + "".join(f"{p:.2f}%{{transform:scaleY({1 if v else .25})}}" for p, v, *_ in pf) + "}")
    for i, p in pings.items():
        CSS.append(f"@keyframes ping{i}{{0%,{p:.2f}%{{opacity:0;transform:scale(.5)}}{p+.3:.2f}%{{opacity:.8;transform:scale(.6)}}{p+8:.2f}%,100%{{opacity:0;transform:scale(3.2)}}}}"
                   f".scene .pg{i}{{animation:ping{i} {T}s infinite ease-out}}"
                   f"@keyframes leaf{i}{{0%,{p:.2f}%{{fill:var(--bg)}}{p+2:.2f}%,96%{{fill:var(--bio)}}100%{{fill:var(--bg)}}}}"
                   f".scene .sp{i} .sleaf{{animation:leaf{i} {T}s infinite}}")
    CSS.append(f".scene .rover-move{{animation:roverX {T}s infinite}}.scene .wheel{{animation:wheel {T}s infinite}}"
               f".scene .probe{{transform-origin:30px -18px;animation:probe {T}s infinite}}"
               ".scene .ping{fill:none;stroke:var(--bio);stroke-width:1;transform-box:fill-box;transform-origin:center}"
               "@keyframes sun{to{transform:rotate(360deg)}}.scene .sun{transform-box:fill-box;transform-origin:center;animation:sun 24s linear infinite}")
    soil = f'<rect class="soil" x="0" y="{G}" width="320" height="22"/>' + "".join(f'<circle class="pebble" cx="{18+k*37}" cy="{G+9+(k%3)*4}" r="1.6"/>' for k in range(9))
    sun = '<g class="sun"><circle class="sun-core" cx="286" cy="36" r="10"/>' + "".join(L(286 + 15 * math.cos(math.radians(a)), 36 + 15 * math.sin(math.radians(a)), 286 + 20 * math.cos(math.radians(a)), 36 + 20 * math.sin(math.radians(a)), "ray") for a in range(0, 360, 45)) + '</g>'
    b = sun + soil + pl + rv + CAP(14, 22, "meter-resolution soil & plant health", "start")
    write("rover", svg("rover", "0 0 320 190", b, "Rover driving along a crop row, probing each plant, which turns green once scanned"))

def clinic():
    G = 185; s = 1.45; y = G - 29 * s; x = 52
    clip = ('<rect class="paper" x="10" y="-25" width="12" height="16" rx="1.5" transform="rotate(8 16 -17)"/>'
            '<rect class="fill" x="13.5" y="-26.5" width="5" height="2.5" rx="1" transform="rotate(8 16 -17)"/>'
            + L(12.6, -20, 19.4, -19, "hair") + L(12.4, -17, 19, -16, "hair") + L(12.2, -14, 17, -13.3, "hair"))
    aL = arm((13, -12)); w1, w2 = arm((15, -20)), arm((18, -18))
    pen = L(0, -3, -1.5, 3, "thin")
    steth = '<path class="st hair" d="M-3 -33 C-6 -24 -1 -21 2 -22 M3 -33 C5 -28 4 -24 2 -22"/><circle class="fill" cx="2" cy="-22" r="1.2"/>'
    scrubs = '<path class="scrubs" d="M-5 -31 L5 -31 L6 -3 L-6 -3 Z"/>'
    f1 = fig("clinician", x, y, s, dict(aL=aL[0], fL=aL[1], aR=w1[0], fR=w1[1], lL=8, lR=-6), dict(front=clip, hR=pen, head=steth, back=scrubs))
    mon = ('<rect class="screen" x="118" y="44" width="186" height="96" rx="10"/>' + L(211, 140, 211, G) + L(186, G, 236, G)
           + '<path class="ekg" pathLength="100" d="M130 104 H160 L165 100 L170 104 H178 L182 110 L188 68 L194 120 L199 104 H212 L218 96 L226 104 H240 L245 100 L250 104 H292"/>'
           + '<text class="cap" x="132" y="62" text-anchor="start">HR 72 · SpO₂ 98%</text>'
           + '<path class="heart" d="M286 60 c-2-3-7-2-7 2 c0 3 4 5 7 8 c3-3 7-5 7-8 c0-4-5-5-7-2z"/>')
    b = GROUND(10, 310, G) + mon + f1 + CAP(14, 22, "vitals · EKG · EHR", "start")
    kf("writeArm", [(0, w1[0]), (100, w2[0])]); kf("writeFore", [(0, w1[1]), (100, w2[1])])
    CSS.append(".clinician .aR{animation:writeArm .45s infinite alternate ease-in-out}.clinician .fR{animation:writeFore .45s infinite alternate ease-in-out}"
               "@keyframes ekg{0%{stroke-dashoffset:100;opacity:1}70%{stroke-dashoffset:0;opacity:1}90%,100%{stroke-dashoffset:0;opacity:0}}"
               ".scene .ekg{fill:none;stroke:var(--tint-deep);stroke-width:1.8;stroke-linejoin:round;stroke-dasharray:100;animation:ekg 2.4s infinite linear}"
               "@keyframes beat{0%,100%{transform:scale(1)}12%{transform:scale(1.25)}24%{transform:scale(1)}36%{transform:scale(1.15)}}"
               ".scene .heart{fill:var(--coral);transform-box:fill-box;transform-origin:center;animation:beat 1.2s infinite}")
    write("clinic", svg("clinic", "0 0 320 205", b, "Stick figure medical assistant charting next to an EKG monitor"))

def design():
    G = 185; s = 1.45; y = G - 29 * s; x = 52
    sketch = ('<rect class="paper" x="9" y="-26" width="14" height="17" rx="1.5" transform="rotate(8 16 -17)"/>'
              '<path class="st hair" d="M12 -14 h8 M13 -14 v4 M19 -14 v4 M19 -14 v-7" transform="rotate(8 16 -17)"/>')
    aL = arm((13, -12)); w1, w2 = arm((15, -20)), arm((18, -18))
    pen = L(0, -3, -1.5, 3, "thin")
    d1 = fig("designer", x, y, s, dict(aL=aL[0], fL=aL[1], aR=w1[0], fR=w1[1], lL=8, lR=-6), dict(front=sketch, hR=pen))
    p1, p2 = 128, 304
    printer = (f'<rect class="frame" x="{p1}" y="44" width="{p2-p1}" height="{G-44}" rx="8"/>' + L(p1 + 10, 66, p2 - 10, 66)
               + L(p1 + 16, G - 12, p2 - 16, G - 12)
               + f'<g class="nozzle"><rect class="fill" x="{p1+16}" y="62" width="16" height="10" rx="2"/><path class="gold-fill" d="M{p1+21} 72 h6 l-3 5z"/></g>'
               + f'<g class="printed" style="transform-origin:216px {G-12}px">'
               + f'<rect class="print" x="186" y="{G-40}" width="60" height="6" rx="2"/>'
               + f'<rect class="print" x="191" y="{G-34}" width="5" height="22"/><rect class="print" x="236" y="{G-34}" width="5" height="22"/>'
               + f'<rect class="print" x="240" y="{G-76}" width="6" height="37" rx="2"/>'
               + "".join(f'<circle class="hole" cx="{196+k*10}" cy="{G-37}" r="1.1"/>' for k in range(4))
               + '</g>')
    b = printer + GROUND(10, 310, G) + d1 + CAP(14, 22, "sketch → CAD → 3D print → DFM", "start")
    CSS.append(".designer .aR{animation:writeArm .5s infinite alternate ease-in-out}.designer .fR{animation:writeFore .5s infinite alternate ease-in-out}"
               "@keyframes nozzle{0%{transform:translateX(0)}100%{transform:translateX(124px)}}"
               ".scene .nozzle{animation:nozzle 1.1s infinite alternate ease-in-out}"
               "@keyframes printed{0%{transform:scaleY(0);opacity:1}85%{transform:scaleY(1);opacity:1}96%,100%{transform:scaleY(1);opacity:0}}"
               ".scene .printed{animation:printed 8s infinite linear}")
    write("design", svg("design", "0 0 320 205", b, "Stick figure sketching while a 3D printer prints a shower chair layer by layer"))

def pushers():
    """Two stickmen who push the landing-page photo carousel."""
    G = 96; s = 1.3; y = G - 29 * s
    pose = dict(up=24, aL=-108, fL=-6, aR=-114, fR=-4, lL=22, sL=8, lR=-16, sR=10)
    left = fig("pusher pusher-l", 150, y, s, pose)
    right = fig("pusher pusher-r", 650, y, s, pose, flip=True)
    floor = '<ellipse class="turntable" cx="400" cy="40" rx="236" ry="20"/>'
    b = floor + GROUND(40, 760, G) + left + right
    kf("pushLeg", [(0, 26), (50, -22), (100, 26)]); kf("pushShin", [(0, 10), (25, 40), (50, 6), (75, 20), (100, 10)])
    kf("pushArm", [(0, -108), (50, -118), (100, -108)])
    CSS.append("@keyframes breathe{0%,100%{transform:rotate(24deg)}50%{transform:rotate(21deg)}}.pusher .up{animation:breathe 3s infinite ease-in-out}"
               ".carousel.pushing-prev .pusher-l .lL,.carousel.pushing-prev .pusher-l .lR,.carousel.pushing-next .pusher-r .lL,.carousel.pushing-next .pusher-r .lR{animation:pushLeg .55s infinite linear}"
               ".carousel.pushing-prev .pusher-l .sL,.carousel.pushing-prev .pusher-l .sR,.carousel.pushing-next .pusher-r .sL,.carousel.pushing-next .pusher-r .sR{animation:pushShin .55s infinite linear}"
               ".carousel.pushing-prev .pusher-l .lR,.carousel.pushing-prev .pusher-l .sR,.carousel.pushing-next .pusher-r .lR,.carousel.pushing-next .pusher-r .sR{animation-delay:-.275s}"
               "@keyframes lean{0%,100%{transform:rotate(31deg)}50%{transform:rotate(28deg)}}.carousel.pushing-prev .pusher-l .up,.carousel.pushing-next .pusher-r .up{animation:lean .55s infinite}"
               ".carousel.pushing-prev .pusher-l .aL,.carousel.pushing-prev .pusher-l .aR,.carousel.pushing-next .pusher-r .aL,.carousel.pushing-next .pusher-r .aR{animation:pushArm .55s infinite ease-in-out}")
    write("pushers", svg("pushers", "0 0 800 110", b, "Two stick figures pushing the photo carousel"))

def mini_svg(name, vb, body, label=""):
    aria = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    return f'<svg class="scene mini mini-{name}" viewBox="{vb}" {aria}>{body}</svg>\n'

SIT = dict(lL=-90, sL=90, lR=-84, sR=84)

def riders():
    """Six stickmen who ride the Ferris-wheel cabins."""
    out = {}
    # 0 — waving
    out[0] = fig("rd0", 0, 0, 1, dict(SIT, aR=-155, fR=-15, aL=30, fL=-30))
    kf("rdWave", [(0, -30), (100, 25)])
    CSS.append(".rd0 .fR{animation:rdWave .5s infinite alternate ease-in-out}")
    # 1 — swinging legs
    out[1] = fig("rd1", 0, 0, 1, dict(SIT, aR=30, fR=-40, aL=-20, fL=-30))
    kf("rdSwingA", [(0, 70), (100, 115)]); kf("rdSwingB", [(0, 115), (100, 70)])
    CSS.append(".rd1 .sL{animation:rdSwingA .7s infinite alternate ease-in-out}.rd1 .sR{animation:rdSwingB .7s infinite alternate ease-in-out}")
    # 2 — cheering, arms up
    out[2] = fig("rd2", 0, 0, 1, dict(SIT, aR=-160, fR=10, aL=160, fL=-10))
    kf("rdCheerR", [(0, -150), (100, -170)]); kf("rdCheerL", [(0, 150), (100, 170)])
    CSS.append(".rd2 .aR{animation:rdCheerR .35s infinite alternate}.rd2 .aL{animation:rdCheerL .35s infinite alternate}"
               "@keyframes rdBounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}.rd2{animation:rdBounce .7s infinite}")
    # 3 — photographer with flash
    cam = upright('<rect class="fill" x="-4" y="-7" width="8" height="5.5" rx="1"/><circle class="flash" cx="0" cy="-4.2" r="1.6"/>', -150 + -40)
    aC = arm((8, -40))
    out[3] = fig("rd3", 0, 0, 1, dict(SIT, aR=aC[0], fR=aC[1], aL=-120, fL=-60), dict(hR=cam))
    CSS.append("@keyframes flash{0%,86%{opacity:0}88%{opacity:1}96%,100%{opacity:0}}.rd3 .flash{fill:var(--gold);animation:flash 2.6s infinite}")
    # 4 — spinning a soccer ball on one finger
    bl = '<g transform="translate(0 -10)"><g class="spinner">' + ball(4.5) + '</g></g>'
    out[4] = fig("rd4", 0, 0, 1, dict(SIT, aR=-178, fR=0, aL=40, fL=-50), dict(hR=bl))
    CSS.append(".rd4 .spinner{animation:spin .5s linear infinite}")
    # 5 — hanging off the side by one hand, legs kicking
    out[5] = fig("rd5", 0, 0, 1, dict(aR=-180, fR=0, aL=-30, fL=-20, lL=20, sL=40, lR=-20, sR=30))
    kf("rdKickL", [(0, 25), (100, -25)]); kf("rdKickR", [(0, -25), (100, 25)])
    CSS.append(".rd5 .lL{animation:rdKickL .45s infinite alternate ease-in-out}.rd5 .lR{animation:rdKickR .45s infinite alternate ease-in-out}"
               "@keyframes rdSway5{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}.rd5{animation:rdSway5 1.8s infinite ease-in-out;transform-origin:0 -28px}")
    for k, body in out.items():
        vb = "-30 -66 64 84" if k in (2, 4) else ("-26 -54 56 72" if k != 5 else "-20 -58 40 92")
        write(f"rider-{k}", mini_svg(f"rider{k}", vb, body))
    # excited reaction while a cabin is hovered
    CSS.append("@keyframes rdHop{0%,100%{transform:translateY(0)}40%{transform:translateY(-5px)}}"
               ".gondola.is-active .rider svg{animation:rdHop .45s infinite}")

def wheel_frame():
    """Static frame + rotor of the Ferris wheel (viewBox 0 0 500 540, hub at 250,245)."""
    CX, CY, R = 250, 232, 158
    G = 522
    rotor = f'<g class="rotor" transform="rotate(0 {CX} {CY})">'
    rotor += f'<circle class="rim" cx="{CX}" cy="{CY}" r="{R}"/><circle class="rim rim-in" cx="{CX}" cy="{CY}" r="{R-16}"/>'
    for k in range(24):
        a = math.radians(k * 15); a2 = math.radians(k * 15 + 7.5)
        x1, y1 = CX + (R - 16) * math.cos(a), CY + (R - 16) * math.sin(a)
        x2, y2 = CX + R * math.cos(a2), CY + R * math.sin(a2)
        rotor += L(round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1), "truss")
        x3, y3 = CX + (R - 16) * math.cos(math.radians(k * 15 + 15)), CY + (R - 16) * math.sin(math.radians(k * 15 + 15))
        rotor += L(round(x2, 1), round(y2, 1), round(x3, 1), round(y3, 1), "truss")
    for k in range(12):
        a = math.radians(k * 30)
        rotor += L(CX, CY, round(CX + (R - 16) * math.cos(a), 1), round(CY + (R - 16) * math.sin(a), 1), "spoke")
    for k in range(24):
        a = math.radians(k * 15 + 7.5)
        rotor += f'<circle class="bulb b{k % 3}" cx="{CX + R * math.cos(a):.1f}" cy="{CY + R * math.sin(a):.1f}" r="3"/>'
    rotor += f'<circle class="hub" cx="{CX}" cy="{CY}" r="16"/><circle class="hub-in" cx="{CX}" cy="{CY}" r="6"/></g>'
    legs = (L(CX, CY, CX - 105, G, "leg") + L(CX, CY, CX + 105, G, "leg")
            + L(CX - 60, CY + 140, CX + 60, CY + 140, "brace") + L(CX - 82, CY + 200, CX + 82, CY + 200, "brace"))
    base = f'<rect class="platform" x="{CX-64}" y="{G-14}" width="128" height="14" rx="3"/>' + L(20, G, 480, G, "ground")
    booth = (f'<rect class="booth" x="392" y="{G-56}" width="58" height="56" rx="4"/><rect class="booth-win" x="402" y="{G-46}" width="38" height="18" rx="2"/>'
             f'<path class="booth-roof" d="M386 {G-56} L421 {G-74} L456 {G-56} Z"/><text class="cap" x="421" y="{G-8}" text-anchor="middle" style="font-size:8px">RIDES</text>')
    lever = (f'<g class="lever" style="transform-origin:372px {G-20}px">' + L(372, G - 20, 372, G - 44, "lever-stick")
             + f'<circle class="lever-knob" cx="372" cy="{G-46}" r="4"/></g><rect class="fill" x="364" y="{G-22}" width="16" height="8" rx="2"/>')
    s = 1.15; oy = G - 29 * s
    hand = ((372 - 345) / s, (G - 44 - oy) / s)
    la = arm(hand)
    operator = fig("operator", 345, oy, s, dict(aR=la[0], fR=la[1], aL=20, fL=-30, lL=6, lR=-6),
                   dict(head='<path class="cap-hat" d="M-7 -44 Q0 -52 7 -44 Z"/>'))
    ticket = upright('<rect class="ticket" x="-2" y="-7" width="9" height="6" rx="1"/>', -100)
    q1 = fig("queue1", 70, oy, s, dict(aR=-100, fR=-20, aL=10, fL=-10, lL=6, lR=-6), dict(hR=ticket))
    q2 = fig("queue2", 108, oy, s * 0.85, dict(aR=-20, fR=-60, aL=20, fL=-40, lL=5, lR=-5), ex=None)
    q2 = q2.replace(f'translate(108 {oy:g})', f'translate(108 {G - 29 * s * .85:g})')
    sign = f'<g class="queue-sign"><rect class="paper" x="132" y="{G-62}" width="60" height="22" rx="4"/><text class="cap" x="162" y="{G-47}" text-anchor="middle" style="font-size:8px">drag to spin</text>' + L(162, G - 40, 162, G, "thin") + '</g>'
    body = legs + rotor + base + booth + lever + operator + q1 + q2 + sign
    kf("leverPull", [(0, 0), (100, -38)])
    CSS.append(".scene .rim{fill:none;stroke:var(--ink);stroke-width:2.2}.scene .rim-in{stroke-width:1.2}"
               ".scene line.truss{stroke:var(--accent);stroke-width:.9;opacity:.55}.scene line.spoke{stroke:var(--ink);stroke-width:1.1;opacity:.75}"
               ".scene .hub{fill:var(--accent)}.scene .hub-in{fill:var(--bg)}"
               ".scene line.leg{stroke:var(--ink);stroke-width:3}.scene line.brace{stroke:var(--ink);stroke-width:1.4}"
               ".scene .platform{fill:var(--tint)}.scene .booth{fill:var(--bg);stroke:var(--ink);stroke-width:1.4}.scene .booth-win{fill:var(--tint-soft);stroke:var(--ink);stroke-width:1}"
               ".scene .booth-roof{fill:var(--coral)}.scene line.lever-stick{stroke:var(--ink);stroke-width:2.4}.scene .lever-knob{fill:var(--coral)}"
               ".scene .cap-hat{fill:var(--accent)}.scene .ticket{fill:var(--gold)}"
               ".scene .bulb{fill:var(--gold)}"
               "@keyframes bulb{0%,100%{opacity:1}50%{opacity:.25}}.scene .b0{animation:bulb 1.2s infinite}.scene .b1{animation:bulb 1.2s infinite .4s}.scene .b2{animation:bulb 1.2s infinite .8s}"
               ".wheel .lever{transition:transform .5s var(--ease)}.wheel.is-fast .lever{transform:rotate(-38deg)}"
               ".wheel .operator .up{transition:transform .5s var(--ease)}.wheel.is-fast .operator .up{transform:rotate(-8deg)}"
               "@keyframes q1{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.5px)}}.queue1{animation:q1 1.6s infinite ease-in-out}"
               "@keyframes q2tap{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(-20deg)}}.queue2 .lR{animation:q2tap .4s infinite}"
               "@keyframes cheerQ{0%,100%{transform:rotate(-150deg)}50%{transform:rotate(-175deg)}}.wheel.is-fast .queue2 .aR{animation:cheerQ .3s infinite}"
               ".wheel.is-paused .queue1 .aR{animation:rdWave .5s infinite alternate}")
    write("wheel-frame", f'<svg class="scene wheel-frame" viewBox="0 0 500 540" aria-hidden="true">{body}</svg>\n')

def jogger():
    body = fig("jogger", 0, 0, 1, dict(up=10, aL=-45, fL=-80, aR=40, fR=-80, lL=35, sL=75, lR=-45, sR=25))
    dust = '<circle class="dust d0" cx="-8" cy="28" r="2"/><circle class="dust d1" cx="-12" cy="27" r="1.5"/>'
    CSS.append(".jogger .lL,.jogger .lR{animation:runLeg .55s infinite linear}.jogger .sL,.jogger .sR{animation:runShin .55s infinite linear}"
               ".jogger .lR,.jogger .sR{animation-delay:-.275s}.jogger .aL,.jogger .aR{animation:runArm .55s infinite ease-in-out}.jogger .aL{animation-delay:-.275s}"
               ".jogger{animation:bob .55s infinite}"
               "@keyframes dust{0%{opacity:.6;transform:none}100%{opacity:0;transform:translate(-10px,-4px) scale(1.8)}}"
               ".scene .dust{fill:var(--faint,#b9c4d6);transform-box:fill-box;transform-origin:center;animation:dust .55s infinite}.scene .d1{animation-delay:.27s}")
    write("jogger", mini_svg("jogger", "-24 -52 52 84", body + dust, "Stick figure running"))

def pizza():
    G = 70; s = 1.15
    slice_ = ('<path class="slice" d="M0 -3 L-9 -22 Q0 -26 9 -22 Z"/><path class="crust" d="M-9 -22 Q0 -26 9 -22"/>'
              '<circle class="pep" cx="-2" cy="-16" r="1.6"/><circle class="pep" cx="3" cy="-12" r="1.3"/>'
              '<circle class="bite k1" cx="0" cy="-3" r="3.2"/><circle class="bite k2" cx="-1" cy="-7" r="3.4"/><circle class="bite k3" cx="1" cy="-11" r="3.6"/>')
    mouth_t, low_t = (6, -38), (14, -20)
    m, lo = arm(mouth_t), arm(low_t)
    held = upright(f'<g transform="rotate(-160 0 -3)">{slice_}</g>', lo[0] + lo[1])
    body = fig("eater", 60, G - 14 * s - 0, s, dict(SIT, aR=lo[0], fR=lo[1], aL=20, fL=-50), dict(hR=held))
    box = ('<g class="pizza-box"><path class="box" d="M110 70 L170 70 L166 60 L114 60 Z"/>'
           '<circle class="pie" cx="140" cy="64" r="9"/><path class="cut" d="M140 64 L149 64 M140 64 L135 57 M140 64 L135 71"/>'
           '<circle class="pep" cx="143" cy="61" r="1.4"/><circle class="pep" cx="137" cy="67" r="1.4"/></g>')
    crumbs = "".join(f'<circle class="crumb cr{i}" cx="{66+i*3}" cy="{G-46+i}" r="1"/>' for i in range(3))
    ledge = L(0, G, 210, G, "ground") + f'<rect class="crate" x="46" y="{G-16}" width="22" height="16" rx="2"/>' + L(46, G - 8, 68, G - 8, "hair")
    T = 6
    kf("eatArm", [(0, lo[0]), (14, lo[0], "ease-in-out"), (22, m[0]), (30, m[0], "ease-in-out"), (38, lo[0]), (44, lo[0], "ease-in-out"),
                  (52, m[0]), (60, m[0], "ease-in-out"), (68, lo[0]), (74, lo[0], "ease-in-out"), (82, m[0]), (88, m[0], "ease-in-out"), (96, lo[0]), (100, lo[0])])
    kf("eatFore", [(0, lo[1]), (14, lo[1], "ease-in-out"), (22, m[1]), (30, m[1], "ease-in-out"), (38, lo[1]), (44, lo[1], "ease-in-out"),
                   (52, m[1]), (60, m[1], "ease-in-out"), (68, lo[1]), (74, lo[1], "ease-in-out"), (82, m[1]), (88, m[1], "ease-in-out"), (96, lo[1]), (100, lo[1])])
    CSS.append(f".eater .aR{{animation:eatArm {T}s infinite}}.eater .fR{{animation:eatFore {T}s infinite}}"
               f"@keyframes chew{{0%,24%,32%,54%,62%,84%,92%,100%{{transform:rotate(0)}}27%,57%,87%{{transform:rotate(-6deg)}}}}.eater .up{{animation:chew {T}s infinite}}"
               f"@keyframes bite1{{0%,25%{{opacity:0}}26%,97%{{opacity:1}}100%{{opacity:0}}}}@keyframes bite2{{0%,55%{{opacity:0}}56%,97%{{opacity:1}}100%{{opacity:0}}}}@keyframes bite3{{0%,85%{{opacity:0}}86%,97%{{opacity:1}}100%{{opacity:0}}}}"
               f".scene .bite{{fill:var(--bg);opacity:0}}.scene .k1{{animation:bite1 {T}s infinite}}.scene .k2{{animation:bite2 {T}s infinite}}.scene .k3{{animation:bite3 {T}s infinite}}"
               f"@keyframes crumb{{0%,26%{{opacity:0;transform:none}}28%{{opacity:1}}45%,100%{{opacity:0;transform:translateY(40px)}}}}"
               f".scene .crumb{{fill:#d9a441;animation:crumb {T/3:.1f}s infinite}}.scene .cr1{{animation-delay:.15s}}.scene .cr2{{animation-delay:.3s}}"
               ".scene .slice{fill:#ffd36b;stroke:var(--ink);stroke-width:.8}.scene .crust{fill:none;stroke:#c98b3c;stroke-width:2.4;stroke-linecap:round}"
               ".scene .pep{fill:#e0533d}.scene .crate{fill:#e9d5b5;stroke:var(--ink);stroke-width:1}.scene .box{fill:#e9d5b5;stroke:var(--ink);stroke-width:1}.scene .pie{fill:#ffd36b;stroke:#c98b3c;stroke-width:2}.scene .cut{stroke:#c98b3c;stroke-width:.8;fill:none}")
    pop_css("chomp", 24, 36, T / 3)
    write("pizza", mini_svg("pizza", "0 0 210 82", ledge + box + body + crumbs + sfx(96, 18, 'CHOMP!', 'chomp', .42, 8), "Stick figure eating pizza"))

def climber():
    body = fig("climber", 0, 0, 1, dict(aL=-170, fL=10, aR=-150, fR=-20, lL=-40, sL=70, lR=-10, sR=30))
    kf("clA", [(0, -175), (100, -140)]); kf("clB", [(0, -140), (100, -175)])
    kf("clLa", [(0, -50), (100, -10)]); kf("clLb", [(0, -10), (100, -50)])
    CSS.append(".climber .aL{animation:clA .35s infinite alternate paused}.climber .aR{animation:clB .35s infinite alternate paused}"
               ".climber .lL{animation:clLa .35s infinite alternate paused}.climber .lR{animation:clLb .35s infinite alternate paused}"
               ".sidenav.is-climbing .climber .aL,.sidenav.is-climbing .climber .aR,.sidenav.is-climbing .climber .lL,.sidenav.is-climbing .climber .lR{animation-play-state:running}")
    write("climber", mini_svg("climber", "-20 -64 40 96", body))

def peeker():
    body = fig("peeker", 0, 0, 1, dict(aR=-160, fR=-20, aL=160, fL=20))
    CSS.append(".card:hover .peeker .fR{animation:rdWave .4s infinite alternate ease-in-out}")
    write("peeker", mini_svg("peeker", "-24 -52 48 52", body))

def dispenser():
    G = 185; s = 1.45; y = G - 29 * s; x = 70
    press1, press2 = arm((24, -20)), arm((24, -15))
    body = fig("presser", x, y, s, dict(aR=press1[0], fR=press1[1], aL=10, fL=-20, lL=8, lR=-6))
    bx = x + 24 * s
    dev = (f'<rect class="tintbox" x="{bx-2}" y="{y-14*s}" width="54" height="66" rx="10"/>'
           f'<rect class="device-btn" x="{bx-6}" y="{y-22*s}" width="18" height="6" rx="3"/>'
           f'<rect class="paper" x="{bx+8}" y="{y-6*s}" width="34" height="22" rx="3"/>')
    bars = "".join(f'<rect class="dose dz{i}" x="{bx+12+i*7}" y="{y-6*s+4}" width="5" height="14" rx="1"/>' for i in range(4))
    cal = ('<rect class="paper" x="210" y="70" width="90" height="84" rx="8"/>' + L(210, 88, 300, 88)
           + '<text class="cap" x="255" y="82" text-anchor="middle" style="font-size:8px">TAPER PLAN</text>'
           + "".join(f'<rect class="cal-bar cb{i}" x="{222+i*19}" y="{148-(4-i)*13}" width="12" height="{(4-i)*13}" rx="2"/>' for i in range(4)))
    b = GROUND(10, 310, G) + cal + dev + bars + body + CAP(14, 22, "dose 4 → 3 → 2 → 1", "start")
    T = 6
    kf("pressArm", [(0, press1[0]), (8, press2[0]), (14, press1[0]), (100, press1[0])])
    kf("pressFore", [(0, press1[1]), (8, press2[1]), (14, press1[1]), (100, press1[1])])
    steps = ""
    for i in range(4):
        steps += (f"@keyframes dz{i}{{0%,{i*25+12}%{{opacity:1}}{i*25+14}%,96%{{opacity:.12}}100%{{opacity:1}}}}"
                  f".scene .dz{3-i}{{animation:dz{i} {T}s infinite}}"
                  f"@keyframes cb{i}{{0%,{i*25}%,{i*25+20}%,100%{{fill:var(--tint)}}{i*25+4}%,{i*25+16}%{{fill:var(--accent)}}}}"
                  f".scene .cb{i}{{animation:cb{i} {T}s infinite}}")
    CSS.append(f".presser .aR{{animation:pressArm {T/4}s infinite}}.presser .fR{{animation:pressFore {T/4}s infinite}}"
               ".scene .device-btn{fill:var(--coral)}.scene .dose{fill:var(--accent)}" + steps)
    write("dispenser", svg("dispenser", "0 0 320 205", b, "Stick figure pressing a dispenser that steps its dose down over time"))

def soccer():
    G = 140; s = 1.2; y = G - 29 * s; T = 6
    runner = fig("runner", 0, y, s, dict(up=12, aL=-45, fL=-80, aR=40, fR=-80, lL=35, sL=75, lR=-45, sR=25), move="run-move")
    striker = fig("striker", 300, y, s, dict(aL=25, aR=-25, fL=-20, fR=-20, lR=30, sR=60, lL=-5), move="striker-move")
    goal = ('<path class="st" d="M405 140 V86 H446 L466 140"/>'
            '<g class="net" style="transform-origin:405px 113px">'
            + "".join(L(405 + k * 8, 86, 405 + k * 8 + (k * 8) * 20 / 41, 140, "hair") for k in range(1, 6))
            + "".join(L(405, 86 + k * 9, 446 + (k * 9) * 20 / 54, 86 + k * 9, "hair") for k in range(1, 6)) + '</g>')
    bl = f'<g class="sball-x"><g class="sball-y"><g class="spinner">{ball(5)}</g></g></g>'
    goaltxt = sfx(424, 62, 'GOAL!', 'goal-pop', .9, -6, 'var(--pop)')
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
               "")
    pop_css("goal-pop", 68, 90, T)
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
.scene{display:block;width:100%;height:auto;overflow:hidden;--ink:var(--ink-strong,#12312d)}
.scene line,.scene .st{stroke:var(--ink);stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;fill:none}
.scene .thin{stroke-width:1.1}.scene .hair{stroke-width:.7}.scene .thick{stroke-width:3.2}
.scene .head{fill:var(--bg);stroke:var(--ink);stroke-width:1.7}
.scene .fill{fill:var(--ink);stroke:none}
.scene .ground{stroke:var(--tint);stroke-width:1.2}
.scene .staff{stroke:var(--tint);stroke-width:1}
.scene .cap{font-family:var(--font-mono);font-size:10px;fill:var(--muted);letter-spacing:.06em}
.scene .ball{fill:var(--bg);stroke:var(--ink);stroke-width:1.3}
.scene .scrubs{fill:var(--tint);stroke:var(--ink);stroke-width:.8}
.scene .tintbox{fill:var(--tint);stroke:var(--ink);stroke-width:1.3}
.scene .frame{fill:var(--bg);stroke:var(--ink);stroke-width:1.5}
.scene .print{fill:var(--tint)}.scene .hole{fill:var(--bg)}
.scene .soil{fill:#efe6da}.scene .pebble{fill:#d8c8b2}
.scene .sun-core{fill:var(--gold);opacity:.85}.scene line.ray{stroke:var(--gold);stroke-width:1.4}
.scene .epi{fill:#f2b8c6}.scene .dermis{fill:#fbe3e8}.scene .wound{fill:#c96b7e;opacity:.55}
.scene .scaf,.scene .scaf-carry{fill:var(--tint-soft);stroke:var(--tint-deep);stroke-width:1.2}.scene line.mesh{stroke:var(--tint-deep);stroke-width:.6}
.scene .cell{opacity:0}.scene .c-teal{fill:var(--tint-deep)}.scene .c-gold{fill:var(--gold)}.scene .c-coral{fill:var(--coral)}
.scene .stain{opacity:0}
.scene .turntable{fill:var(--tint-soft);stroke:var(--tint);stroke-width:1.5}
.scene .coat{fill:var(--tint-soft);stroke:var(--ink);stroke-width:1}
.scene .tube{fill:var(--tint-soft);stroke:var(--ink);stroke-width:.8}
.scene .liquid{fill:var(--tint-deep);opacity:.45}
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
.scene .sfx-pop{opacity:0}.scene .sfx-burst{stroke:var(--ink);stroke-width:2.6;stroke-linejoin:round}
.scene .sfx-text{font-family:var(--font-comic,Bangers),Impact,sans-serif;font-size:24px;fill:var(--ink);letter-spacing:1px}
@keyframes spin{to{transform:rotate(360deg)}}
.scene .spinner{transform-box:fill-box;transform-origin:center}
.scene:not(.in-view) *{animation-play-state:paused!important}
"""

if __name__ == "__main__":
    hero(); biolistics(); bioscaffold(); rover(); clinic(); design(); dispenser(); riders(); wheel_frame(); jogger(); pizza(); climber(); peeker(); soccer(); bass_scene(); tkd_scene(); blog(); profile()
    with open(os.path.join(ROOT, "assets", "css", "scenes.css"), "w") as f:
        f.write(BASE + "\n".join(CSS) + "\n")
    print("scenes written:", sorted(os.listdir(INC)))
