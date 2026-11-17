"""
Exploded-view sequence for the shower chair.

Renders FRAMES stills from assembled to fully exploded. Each part slides out
along the line from the assembly's centre to its own centre, with a vertical
bias so the stack reads top to bottom; the frame itself stays put as the
datum. Output: renders/explode-00.png … , one per step.

Usage: python3 explode.py [frames]
"""
import sys, os, math, bpy, mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "renders")
os.makedirs(OUT, exist_ok=True)

FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
SAMPLES = 60
RES = (1200, 980)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = RES
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "Medium High Contrast"


def mat(name, base, rough, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    return m


MATS = {
    "frame":      mat("anodised_aluminium", (0.52, 0.55, 0.59), 0.26, 1.0),
    "carriage":   mat("carriage_alu",       (0.60, 0.63, 0.66), 0.30, 1.0),
    "idler":      mat("pulley_alu",         (0.58, 0.61, 0.64), 0.28, 1.0),
    "drive":      mat("motor_housing",      (0.12, 0.135, 0.155), 0.45),
    "cable":      mat("steel_cable",        (0.30, 0.31, 0.33), 0.38, 1.0),
    "seat":       mat("seat_polymer",       (0.88, 0.90, 0.91), 0.40, 0.0, 0.3),
    "backrest":   mat("back_polymer",       (0.88, 0.90, 0.91), 0.40, 0.0, 0.3),
    "arms":       mat("arm_polymer",        (0.82, 0.845, 0.87), 0.36, 0.0, 0.25),
    "legsupport": mat("ls_polymer",         (0.82, 0.845, 0.87), 0.38, 0.0, 0.25),
    "actuator":   mat("actuator",           (0.14, 0.155, 0.175), 0.40),
    "lock":       mat("accent_turquoise",   (0.00, 0.26, 0.23), 0.33),
    "pins":       mat("accent_pin",         (0.00, 0.26, 0.23), 0.33),
    "feet":       mat("rubber",             (0.035, 0.04, 0.05), 0.80),
}

# how far out each part travels, as a multiple of the base distance, and how
# much vertical bias it gets. The frame is the datum and never moves.
PULL = {
    "frame":      (0.00, 0.0),
    "carriage":   (0.45, 0.7),
    "seat":       (0.55, 1.5),
    "lock":       (0.85, 1.1),
    "backrest":   (0.75, 1.9),
    "arms":       (0.95, 1.2),
    "legsupport": (0.90, 0.8),
    "actuator":   (1.10, 0.5),
    "drive":      (0.90, -0.3),
    "idler":      (0.90, -0.3),
    "cable":      (0.70, -0.6),
    "feet":       (0.50, -0.9),
    "pins":       (1.00, 0.0),
}

objs = {}
for name, m in MATS.items():
    path = os.path.join(HERE, "out", f"{name}.stl")
    if not os.path.exists(path):
        continue
    try:
        bpy.ops.wm.stl_import(filepath=path)
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=path)
    o = bpy.context.selected_objects[0]
    o.name = name
    o.data.materials.clear()
    o.data.materials.append(m)
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(32))
    except Exception:
        bpy.ops.object.shade_flat()
    mod = o.modifiers.new("bevel", "BEVEL")
    mod.width = 0.55
    mod.segments = 2
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(35)
    objs[name] = o


def bounds(obs):
    mn = mathutils.Vector((1e9, 1e9, 1e9))
    mx = mathutils.Vector((-1e9, -1e9, -1e9))
    for o in obs:
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            mn = mathutils.Vector((min(mn[i], w[i]) for i in range(3)))
            mx = mathutils.Vector((max(mx[i], w[i]) for i in range(3)))
    return mn, mx


mn, mx = bounds(objs.values())
H = mx.z - mn.z
W = mx.x - mn.x
ctr = (mn + mx) / 2
BASE = H * 0.30          # how far a pull of 1.0 travels

# each part's own centre, and the direction it leaves along
home = {}
dirs = {}
for name, o in objs.items():
    pmn, pmx = bounds([o])
    c = (pmn + pmx) / 2
    d = mathutils.Vector((c.x - ctr.x, c.y - ctr.y, 0.0))
    if d.length < 1e-6:
        d = mathutils.Vector((1.0, 0.0, 0.0))
    d.normalize()
    pull, lift = PULL.get(name, (1.0, 0.5))
    home[name] = o.location.copy()
    dirs[name] = mathutils.Vector((d.x * pull, d.y * pull, lift)) * BASE

# floor, lights, camera
bpy.ops.mesh.primitive_plane_add(size=H * 22, location=(0, 0, mn.z - H * 0.9))
bpy.context.object.data.materials.append(mat("floor", (0.93, 0.94, 0.95), 0.5))

w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.88, 0.91, 0.93, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0


def area(loc, rot, size, energy):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    L = bpy.context.object
    L.data.size = size
    L.data.energy = energy


area((-H * 1.2, -H * 1.8, H * 2.6), (math.radians(38), 0, math.radians(-32)), H * 1.6, H * H * 5.0)
area((H * 2.0, -H * 1.2, H * 1.6), (math.radians(64), 0, math.radians(56)), H * 1.4, H * H * 1.6)
area((0, H * 2.2, H * 1.8), (math.radians(-54), 0, 0), H * 1.6, H * H * 1.2)

bpy.ops.object.camera_add()
cam = bpy.context.object
sc.camera = cam
cam.data.lens = 60
cam.data.clip_start = 1.0
cam.data.clip_end = 1e6

AZ, EL, DIST = math.radians(-60), math.radians(19), W * 2.62
target = mathutils.Vector((0, 0, ctr.z + H * 0.56))
cam.location = target + mathutils.Vector((DIST * math.cos(AZ) * math.cos(EL),
                                          DIST * math.sin(AZ) * math.cos(EL),
                                          DIST * math.sin(EL)))
d = target - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

for f in range(FRAMES):
    t = f / (FRAMES - 1)
    e = t * t * (3 - 2 * t)          # ease, so the ends settle
    for name, o in objs.items():
        o.location = home[name] + dirs[name] * e
    sc.render.filepath = os.path.join(OUT, f"explode-{f:02d}.png")
    bpy.ops.render.render(write_still=True)
    print("frame", f, flush=True)
