"""Photoreal renders of the ECLIPSE lamp with Blender/Cycles (bpy module).

    python3 render_blender.py <shot> [--samples N] [--res WxH]

shots: hero, studio, detail, exploded, underside
Inputs: ../mechanical/out/*.stl + parts.json, ../electronics/*/eclipse-*.glb
"""
import argparse, json, math, os, sys
import bpy
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
MECH = os.path.join(HERE, "..", "mechanical", "out")
ELEC = os.path.join(HERE, "..", "electronics")
MM = 0.001
BACKDROP_ROT = 0.0


# ------------------------------------------------------------------ materials
def mat(name, color=(0.8, 0.8, 0.8), metallic=0.0, rough=0.5, emit=None, strength=0.0, transmission=0.0,
        coat=0.0, aniso=0.0, ior=1.45, alpha=1.0, subsurface=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Anisotropic"].default_value = aniso
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Subsurface Weight"].default_value = subsurface
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def wood_material():
    """Oak-ish desk top: long noise streaks along Y for grain + low-frequency colour drift."""
    m = bpy.data.materials.new("oak")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 0.04, 1.0)
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 90.0
    grain.inputs["Detail"].default_value = 8.0
    grain.inputs["Roughness"].default_value = 0.6
    drift = nt.nodes.new("ShaderNodeTexNoise")
    drift.inputs["Scale"].default_value = 3.0
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.35
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.20, 0.115, 0.06, 1)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (0.42, 0.27, 0.15, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], grain.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], drift.inputs["Vector"])
    nt.links.new(grain.outputs["Fac"], mix.inputs["A"])
    nt.links.new(drift.outputs["Fac"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.2
    return m


LEVEL = [1.0]


def build_materials(on=True, warmth=(1.0, 0.80, 0.60), level=1.0):
    LEVEL[0] = level
    M = {}
    M["graphite"] = mat("graphite", (0.030, 0.031, 0.034), 1.0, 0.30, aniso=0.2)
    M["brass"] = mat("brass", (0.80, 0.60, 0.34), 1.0, 0.20)
    M["steel"] = mat("steel", (0.55, 0.56, 0.58), 1.0, 0.35)
    M["alu"] = mat("alu", (0.70, 0.71, 0.72), 1.0, 0.45)
    M["cork"] = mat("cork", (0.42, 0.28, 0.16), 0.0, 0.85)
    M["glass"] = mat("smoked_glass", (0.006, 0.006, 0.008), 0.0, 0.06, coat=1.0, ior=1.52)
    M["etch"] = mat("etch", (0.55, 0.55, 0.56), 0.0, 0.7, emit=warmth if on else None, strength=0.25 * level if on else 0)
    if on:
        M["diffuser"] = mat("diffuser_on", (0.95, 0.94, 0.92), 0.0, 0.4, emit=warmth, strength=420.0 * level,
                            subsurface=0.2)
    else:
        M["diffuser"] = mat("diffuser_off", (0.92, 0.92, 0.90), 0.0, 0.35, transmission=0.15, subsurface=0.5)
    return M


PART_MAT = {"base_shell": "graphite", "base_weight": "steel", "bottom_cover": "alu", "base_foot": "cork",
            "touch_glass": "glass", "touch_etch": "etch", "stem": "brass", "hinge_yoke": "graphite",
            "hinge_knob": "brass", "halo_housing": "graphite", "halo_diffuser": "diffuser"}


# ------------------------------------------------------------------ scene helpers
def import_stl(name):
    path = os.path.join(MECH, name + ".stl")
    bpy.ops.wm.stl_import(filepath=path)
    ob = bpy.context.selected_objects[0]
    ob.name = name
    ob.scale = (MM, MM, MM)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(scale=True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception:
        bpy.ops.object.shade_smooth()
    return ob


def import_glb(path, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    return root, new


def add_plane(name, size, loc, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    return ob


def backdrop(material, width=4.0, depth=3.0, height=2.0, radius=0.6):
    """Seamless studio sweep."""
    import bmesh
    me = bpy.data.meshes.new("sweep")
    bm = bmesh.new()
    prof = []
    for i in range(0, 13):
        a = math.pi / 2 * i / 12
        prof.append((-depth / 2 + radius * (1 - math.sin(a)) * 0 + 0, 0))
    pts = [(y, 0.0) for y in (-depth / 2, depth / 2 - radius)]
    for i in range(1, 13):
        a = math.pi / 2 * i / 12
        pts.append((depth / 2 - radius + radius * math.sin(a), radius - radius * math.cos(a)))
    pts.append((depth / 2, height))
    rows = []
    for x in (-width / 2, width / 2):
        rows.append([bm.verts.new((x, y, z)) for y, z in pts])
    for k in range(len(pts) - 1):
        bm.faces.new((rows[0][k], rows[1][k], rows[1][k + 1], rows[0][k + 1]))
    bm.to_mesh(me)
    ob = bpy.data.objects.new("sweep", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = (0, 0, math.radians(BACKDROP_ROT))
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def area(name, loc, target, size, power, color=(1, 1, 1), shape="DISK"):
    l = bpy.data.lights.new(name, "AREA")
    l.shape = shape
    l.size = size
    l.energy = power
    l.color = color
    ob = bpy.data.objects.new(name, l)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def orbit(az, el, dist, target):
    a, e = math.radians(az), math.radians(el)
    return (target[0] + dist * math.cos(e) * math.cos(a), target[1] + dist * math.cos(e) * math.sin(a),
            target[2] + dist * math.sin(e))


def camera(loc, target, lens=70, dof=None, fstop=4.0):
    c = bpy.data.cameras.new("cam")
    c.lens = lens
    c.sensor_width = 36
    ob = bpy.data.objects.new("cam", c)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    bpy.context.scene.camera = ob
    if dof:
        c.dof.use_dof = True
        c.dof.focus_distance = dof
        c.dof.aperture_fstop = fstop
    return ob


def world(color=(0.05, 0.05, 0.055), strength=1.0, sky=False):
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength


def setup_render(samples, res, out):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    try:
        s.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    s.cycles.max_bounces = 8
    s.cycles.transparent_max_bounces = 8
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    s.render.image_settings.file_format = "PNG"
    s.render.filepath = out


# ------------------------------------------------------------------ lamp
def build_lamp(M, explode=False, with_pcbs=False):
    meta = json.load(open(os.path.join(MECH, "parts.json")))
    obs = {}
    for name in PART_MAT:
        ob = import_stl(name)
        ob.data.materials.append(M[PART_MAT[name]])
        obs[name] = ob
    if with_pcbs:
        hp = os.path.join(ELEC, "halo", "eclipse-halo.glb")
        cp = os.path.join(ELEC, "core", "eclipse-core.glb")
        rc = meta["ring_center"]
        if os.path.exists(hp):
            root, _ = import_glb(hp, "pcb_halo")
            root.rotation_euler = (0, math.pi, 0)
            root.location = (0, rc[1] * MM, (rc[2] + 14.0 - 2.5) * MM)
            obs["pcb_halo"] = root
        if os.path.exists(cp):
            root, _ = import_glb(cp, "pcb_core")
            root.location = (0, 0, (19.0 - 1.6) * MM)
            obs["pcb_core"] = root
    if M["diffuser"].name.startswith("diffuser_on"):
        # the LED ring as an actual light source (cleaner sampling than the emissive mesh alone)
        rc = meta["ring_center"]
        tilt = math.radians(meta.get("tilt", 0.0))
        for k in range(12):
            a = 2 * math.pi * k / 12
            l = bpy.data.lights.new(f"led{k}", "AREA")
            l.shape = "DISK"
            l.size = 0.045
            l.energy = 2.2 * LEVEL[0]
            l.color = (1.0, 0.82, 0.64)
            ob = bpy.data.objects.new(f"led{k}", l)
            bpy.context.scene.collection.objects.link(ob)
            ob.location = (0.090 * math.cos(a), rc[1] * MM + 0.090 * math.sin(a), (rc[2] + 0.2) * MM)
            ob.rotation_euler = (0, 0, 0)  # area lights point down -Z by default
    if explode:
        dz = {"halo_housing": 120, "pcb_halo": 60, "halo_diffuser": -10,
              "touch_glass": 150, "touch_etch": 150, "base_shell": 95, "pcb_core": 45,
              "base_weight": 0, "bottom_cover": -30, "base_foot": -55}
        dx = {"hinge_knob": 40}
        lift = 70  # keep the lowest exploded part above the floor
        for k, ob in obs.items():
            ob.location.z += (dz.get(k, 0) + lift) * MM
        for k, v in dx.items():
            if k in obs:
                obs[k].location.x += v * MM
    return obs, meta


def main():
    global BACKDROP_ROT
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--res", default="1920x1280")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    res = tuple(int(v) for v in args.res.split("x"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    out = args.out or os.path.join(HERE, f"eclipse_{args.shot}.png")
    shot = args.shot
    T = (0.0, -0.095, 0.225)

    if shot == "hero":
        # evening desk: oak top, dark wall, lamp on and lighting the desk
        M = build_materials(on=True, level=1.0)
        obs, meta = build_lamp(M)
        add_plane("desk", 3.0, (0, 0, 0), wood_material())
        wall = mat("wall", (0.30, 0.29, 0.27), 0.0, 0.95)
        add_plane("wall", 4.0, (0, 0.42, 1.0), wall, rot=(math.pi / 2, 0, 0))
        paper = mat("paper", (0.86, 0.84, 0.79), 0.0, 0.8)
        cover = mat("cover", (0.07, 0.11, 0.15), 0.0, 0.55)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.10, -0.17, 0.006))
        nb = bpy.context.active_object
        nb.scale = (0.15, 0.21, 0.012)
        nb.rotation_euler = (0, 0, math.radians(-14))
        nb.data.materials.append(cover)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.06, -0.20, 0.0012))
        sh = bpy.context.active_object
        sh.scale = (0.21, 0.297, 0.0024)
        sh.rotation_euler = (0, 0, math.radians(9))
        sh.data.materials.append(paper)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0035, depth=0.15, location=(-0.02, -0.26, 0.006),
                                            rotation=(0, math.pi / 2, math.radians(30)))
        bpy.context.active_object.data.materials.append(M["brass"])
        world((0.010, 0.012, 0.018), 1.0)
        area("fill", orbit(-150, 25, 1.6, T), T, 1.5, 6, (0.55, 0.65, 1.0))
        area("rim", orbit(60, 35, 1.2, T), T, 0.8, 10, (1.0, 0.9, 0.8))
        tgt = (0.0, -0.11, 0.235)
        camera(orbit(-62, 9, 1.32, tgt), tgt, lens=50, dof=1.32, fstop=4.0)
        bpy.context.scene.view_settings.exposure = -0.6
    elif shot == "studio":
        M = build_materials(on=True, level=0.45)
        obs, meta = build_lamp(M)
        BACKDROP_ROT = 125 - 90
        backdrop(mat("sweep", (0.80, 0.80, 0.80), 0.0, 0.6), width=9, depth=6, height=4, radius=1.0)
        world((0.6, 0.6, 0.62), 0.25)
        area("key", orbit(-125, 40, 1.8, T), T, 1.8, 260)
        area("fill", orbit(-20, 15, 1.8, T), T, 1.8, 90)
        area("top", (0, -0.1, 1.8), (0, -0.1, 0), 1.4, 120)
        camera(orbit(-55, 10, 1.55, T), T, lens=60)
    elif shot == "detail":
        M = build_materials(on=True, level=0.6)
        obs, meta = build_lamp(M)
        add_plane("desk", 3.0, (0, 0, 0), wood_material())
        world((0.02, 0.022, 0.03), 1.0)
        area("key", (-0.5, -0.5, 0.6), (0, -0.03, 0.02), 0.5, 18, (1.0, 0.95, 0.9))
        area("rim", (0.4, 0.4, 0.3), (0, 0, 0.02), 0.4, 8, (0.8, 0.85, 1.0))
        camera((0.16, -0.30, 0.17), (0.0, -0.02, 0.02), lens=85, dof=0.36, fstop=3.2)
    elif shot == "exploded":
        M = build_materials(on=False)
        obs, meta = build_lamp(M, explode=True, with_pcbs=True)
        BACKDROP_ROT = 130 - 90
        backdrop(mat("sweep", (0.86, 0.86, 0.86), 0.0, 0.6), width=9, depth=6, height=4, radius=1.0)
        world((0.7, 0.7, 0.72), 0.3)
        area("key", orbit(-125, 40, 1.8, T), T, 1.8, 260)
        area("fill", orbit(-20, 15, 1.8, T), T, 1.8, 90)
        area("top", (0, -0.1, 1.8), (0, -0.1, 0), 1.4, 140)
        tgt = (0, -0.095, 0.33)
        camera(orbit(-52, 14, 1.85, tgt), tgt, lens=50)
    elif shot == "underside":
        M = build_materials(on=True, level=0.12)
        obs, meta = build_lamp(M)
        BACKDROP_ROT = 125 - 90
        backdrop(mat("sweep", (0.10, 0.10, 0.11), 0.0, 0.7), width=9, depth=6, height=4, radius=1.0)
        world((0.02, 0.02, 0.025), 1.0)
        area("rim", orbit(-20, 50, 1.0, (0, -0.15, 0.44)), (0, -0.15, 0.44), 1.0, 30)
        area("key", orbit(-120, 10, 1.2, (0, -0.1, 0.3)), (0, -0.1, 0.3), 1.2, 25, (0.8, 0.85, 1.0))
        tgt = (0.0, -0.13, 0.36)
        camera(orbit(-70, -8, 0.95, tgt), tgt, lens=40)
    else:
        raise SystemExit("unknown shot " + shot)

    setup_render(args.samples, res, out)
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


if __name__ == "__main__":
    main()
