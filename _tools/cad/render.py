"""Render the shower-chair transfer system. Usage: python3 render.py [preview|final]"""
import sys, os, math, bpy, mathutils

MODE = sys.argv[1] if len(sys.argv) > 1 else "preview"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "renders")
os.makedirs(OUT, exist_ok=True)

SAMPLES = 24 if MODE == "preview" else 130
RES = (980, 760) if MODE == "preview" else (1700, 1320)

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
    "tub":        mat("tub_ceramic",        (0.93, 0.94, 0.945), 0.16, 0.0, 0.6),
}

objs = []
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
    objs.append(o)

# bounds of the product alone (the tub is context and runs off-frame)
mn = mathutils.Vector((1e9, 1e9, 1e9))
mx = mathutils.Vector((-1e9, -1e9, -1e9))
for o in objs:
    if o.name == "tub":
        continue
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mn = mathutils.Vector((min(mn[i], w[i]) for i in range(3)))
        mx = mathutils.Vector((max(mx[i], w[i]) for i in range(3)))
H = mx.z - mn.z
W = mx.x - mn.x

bpy.ops.mesh.primitive_plane_add(size=H * 20, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat("floor", (0.90, 0.91, 0.92), 0.45))

w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.86, 0.90, 0.92, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.9


def area(loc, rot, size, energy):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    L = bpy.context.object
    L.data.size = size
    L.data.energy = energy


area((-H * 1.0, -H * 1.5, H * 1.9), (math.radians(40), 0, math.radians(-34)), H * 1.3, H * H * 3.4)
area((H * 1.7, -H * 1.0, H * 1.1), (math.radians(66), 0, math.radians(58)), H * 1.2, H * H * 1.0)
area((0, H * 1.9, H * 1.4), (math.radians(-56), 0, 0), H * 1.4, H * H * 0.8)

bpy.ops.object.camera_add()
cam = bpy.context.object
sc.camera = cam
cam.data.clip_start = 1.0
cam.data.clip_end = 1e6


def look_at(obj, target):
    d = mathutils.Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def shoot(name, az, el, dist, target, lens=58):
    cam.data.lens = lens
    A, E = math.radians(az), math.radians(el)
    cam.location = mathutils.Vector(target) + mathutils.Vector(
        (dist * math.cos(A) * math.cos(E), dist * math.sin(A) * math.cos(E), dist * math.sin(E)))
    look_at(cam, target)
    sc.render.filepath = os.path.join(OUT, f"{MODE}-{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)


MIDZ = mn.z + H * 0.48
shoot("hero",     -62, 28, W * 1.55, (0, 0, mn.z + H * 0.56), lens=52)
shoot("section",  -90, 16, W * 1.45, (0, 0, mn.z + H * 0.54), lens=60)
shoot("drive",   -124, 24, W * 0.80, (-W * 0.30, 0, mn.z + H * 0.50), lens=72)
shoot("leglift",  -58, 18, W * 0.70, (W * 0.08, 0, mn.z + H * 0.68), lens=62)
shoot("intub",     34, 28, W * 1.15, (W * 0.14, 0, mn.z + H * 0.56), lens=58)
