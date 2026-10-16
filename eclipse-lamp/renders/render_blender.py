"""Photoreal renders of the ECLIPSE lamp with Blender/Cycles (bpy module).

    python3 render_blender.py <shot> [--samples N] [--res WxH]

shots: hero, trunk, cool, studio, leaves, night, detail
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


def glow_mat(name, on, warmth, strength, side=0.3, up=0.1, falloff=1.0):
    """Light-diffusing PMMA that glows through its whole body.

    Emission is weighted by the surface normal: faces looking down (the halo's
    underside, where the LEDs fire) are brightest, the side walls glow softly.
    Off, it is a milky translucent opal.
    """
    m = bpy.data.materials.new(name + ("_on" if on else "_off"))
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.94, 0.93, 0.90, 1)
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Subsurface Weight"].default_value = 1.0
    b.inputs["Subsurface Radius"].default_value = (0.006, 0.005, 0.004)
    b.inputs["Transmission Weight"].default_value = 0.25
    b.inputs["Coat Weight"].default_value = 0.3
    if not on:
        return m
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (1, 1, 1, 1)
    els[1].position, els[1].color = 1.0, (up * side, up * side, up * side, 1)
    mid = els.new(0.5)
    mid.color = (side, side, side, 1)
    # vertical falloff: walls glow brightest near the underside, fading toward the cap
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sepg = nt.nodes.new("ShaderNodeSeparateXYZ")
    fall = nt.nodes.new("ShaderNodeMapRange")
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = falloff
    nt.links.new(tc.outputs["Generated"], sepg.inputs["Vector"])
    nt.links.new(sepg.outputs["Z"], fall.inputs["Value"])
    mul0 = nt.nodes.new("ShaderNodeMath")
    mul0.operation = "MULTIPLY"
    nt.links.new(fall.outputs["Result"], mul0.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    nt.links.new(geo.outputs["Normal"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mul0.inputs[0])
    nt.links.new(mul0.outputs["Value"], mul.inputs[0])
    nt.links.new(mul.outputs["Value"], b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (*warmth, 1)
    return m


def bark_material():
    """Dark bronze bark patina: metallic base, rough, with fine furrowed bump (cedar-elm bark)."""
    m = bpy.data.materials.new("bark")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.105, 0.075, 0.050, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.75
    b.inputs["Specular IOR Level"].default_value = 0.18   # patina: little sheen
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (420.0, 420.0, 90.0)   # furrows run along the branches (mostly z)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.62
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.85
    bump.inputs["Distance"].default_value = 0.0006   # metres: furrowed bark, not a 1 m default
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # lighter worn bronze on the high spots
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.035, 0.029, 0.024, 1)
    ramp.color_ramp.elements[1].color = (0.135, 0.110, 0.088, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


FORK_Z = [0.158]


def bark_glow_material(strength, warmth=(1.0, 0.50, 0.18)):
    """Bark with fissures that glow: the trunk is a bronze shell around a light-guide core, and
    the light leaks out where the bark is cracked open (Voronoi edge network, stretched along
    the grain), plus the root buttresses."""
    m = bark_material()
    m.name = "bark_glow"
    if strength <= 0:
        return m
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (170.0, 170.0, 9.0)   # long, narrow furrows along the grain
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 1.0
    vor.inputs["Randomness"].default_value = 0.9
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 0.016
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    # break the network up so only some fissures are open
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 30.0
    gate = nt.nodes.new("ShaderNodeMapRange")
    gate.inputs["From Min"].default_value = 0.52
    gate.inputs["From Max"].default_value = 0.60
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    mul2.inputs[1].default_value = strength
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], vor.inputs["Vector"])
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], gate.inputs["Value"])
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(gate.outputs["Result"], mul.inputs[1])
    # only the trunk holds the light guide: fade the glow out just above the fork
    sepz = nt.nodes.new("ShaderNodeSeparateXYZ")
    zmask = nt.nodes.new("ShaderNodeMapRange")
    zmask.inputs["From Min"].default_value = FORK_Z[0] + 0.012
    zmask.inputs["From Max"].default_value = FORK_Z[0] - 0.004
    nt.links.new(tc.outputs["Object"], sepz.inputs["Vector"])
    nt.links.new(sepz.outputs["Z"], zmask.inputs["Value"])
    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    nt.links.new(mul.outputs["Value"], mul3.inputs[0])
    nt.links.new(zmask.outputs["Result"], mul3.inputs[1])
    nt.links.new(mul3.outputs["Value"], mul2.inputs[0])
    nt.links.new(mul2.outputs["Value"], b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (*warmth, 1)
    # the fissures are grooves: chain a relief bump on top of the fine bark grain
    old = [l for l in nt.links if l.to_socket == b.inputs["Normal"]][0].from_socket
    clamp = nt.nodes.new("ShaderNodeMath")
    clamp.operation = "MINIMUM"
    clamp.inputs[1].default_value = 0.12
    bump2 = nt.nodes.new("ShaderNodeBump")
    bump2.inputs["Strength"].default_value = 0.9
    bump2.inputs["Distance"].default_value = 0.0015
    nt.links.new(vor.outputs["Distance"], clamp.inputs[0])
    nt.links.new(clamp.outputs["Value"], bump2.inputs["Height"])
    nt.links.new(old, bump2.inputs["Normal"])
    nt.links.new(bump2.outputs["Normal"], b.inputs["Normal"])
    return m


def samara_material(name, color, strength):
    """Diffusing epoxy samara lit from inside by its fibre: translucent, softly glowing."""
    m = mat(name, (0.95, 0.88, 0.70), 0.0, 0.35, emit=color if strength > 0 else None, strength=strength,
            transmission=0.35, subsurface=0.8)
    return m


def leaf_film_material():
    """Olive light-diffusing leaf film (0.125 mm): glossy on top, translucent, so the LED leaves
    in the crown light it from inside."""
    m = bpy.data.materials.new("leaf_film")
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.38
    b.inputs["Coat Weight"].default_value = 0.2
    # per-leaf colour variation: young yellow-green to deep olive
    rnd = nt.nodes.new("ShaderNodeAttribute")
    rnd.attribute_name = "tone"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.018, 0.036, 0.009, 1)
    els[1].position, els[1].color = 1.0, (0.10, 0.13, 0.028, 1)
    mid = els.new(0.55)
    mid.color = (0.038, 0.068, 0.016, 1)
    nt.links.new(rnd.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    hue = nt.nodes.new("ShaderNodeMix")
    hue.data_type = "RGBA"
    hue.inputs["Factor"].default_value = 0.6
    hue.inputs["B"].default_value = (0.55, 0.62, 0.18, 1)
    nt.links.new(ramp.outputs["Color"], hue.inputs["A"])
    nt.links.new(hue.outputs["Result"], tr.inputs["Color"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.35
    nt.links.new(b.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


WARM = (1.0, 0.70, 0.40)
COOL = (0.82, 0.90, 1.0)


def build_materials(on=True, warmth=(1.0, 0.80, 0.60), level=1.0, band=None, cool_mix=0.5, trunk=None):
    trunk = level if trunk is None else trunk
    LEVEL[0] = level
    M = {}
    M["graphite"] = mat("graphite", (0.030, 0.031, 0.034), 1.0, 0.30, aniso=0.2)
    M["steel"] = mat("steel", (0.55, 0.56, 0.58), 1.0, 0.35)
    M["cork"] = mat("cork", (0.42, 0.28, 0.16), 0.0, 0.85)
    M["glass"] = mat("smoked_glass", (0.006, 0.006, 0.008), 0.0, 0.06, coat=1.0, ior=1.52)
    M["etch"] = mat("etch", (0.55, 0.55, 0.56), 0.0, 0.7, emit=warmth if on else None, strength=0.25 * level if on else 0)
    band_on = on if band is None else True
    M["band"] = glow_mat("band_glow", band_on, warmth, 0.9 * (level if band is None else band), side=1.0, up=1.0)
    M["white"] = mat("white_powder", (0.85, 0.85, 0.83), 0.0, 0.6)
    M["bark"] = bark_material()
    M["bark_glow"] = bark_glow_material(3.2 * trunk if on else 0.0)
    M["samara_W"] = samara_material("samara_warm", (1.0, 0.72, 0.42), 2.2 * level if on else 0)
    M["samara_C"] = samara_material("samara_cool", (0.85, 0.92, 1.0), 2.2 * level * cool_mix if on else 0)
    M["flex"] = mat("flex_coverlay", (0.22, 0.13, 0.06), 0.3, 0.35, coat=0.5)
    M["leaf_film"] = leaf_film_material()
    # leaves: 0402 LEDs. Off: yellow phosphor dots.  On: tiny emitters (warm / cool channels)
    w_on, c_on = on, on and cool_mix > 0
    M["leaf_W"] = mat("leaf_warm", (0.95, 0.80, 0.30), 0.0, 0.3, emit=WARM if w_on else None,
                      strength=140.0 * level * (1 - cool_mix * 0.5) if w_on else 0)
    M["leaf_C"] = mat("leaf_cool", (0.95, 0.85, 0.35), 0.0, 0.3, emit=COOL if c_on else None,
                      strength=140.0 * level * cool_mix if c_on else 0)
    return M


PART_MAT = {"base_shell": "graphite", "base_weight": "white", "base_band": "band", "base_plinth": "graphite",
            "base_foot": "cork", "touch_glass": "glass", "touch_etch": "etch"}


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
def curve_tube(name, polylines, material, radii=None, const_r=None):
    """One curve object holding many tapered tubes (fast to build and to render)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0 if const_r is None else const_r
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    for i, pl in enumerate(polylines):
        sp = cu.splines.new("POLY")
        sp.points.add(len(pl) - 1)
        for j, p in enumerate(pl):
            sp.points[j].co = (p[0] * MM, p[1] * MM, p[2] * MM, 1.0)
            if radii is not None:
                sp.points[j].radius = radii[i][j] * MM
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(material)
    return ob


def leaf_mesh(name, points, material, r=0.55):
    """All leaves of one colour as one mesh of tiny boxes (an 0402 LED is 1.0 x 0.5 x 0.35 mm)."""
    import bmesh
    bm = bmesh.new()
    for p in points:
        geom = bmesh.ops.create_cube(bm, size=1.0)
        vs = geom["verts"]
        bmesh.ops.scale(bm, vec=(1.0 * MM * r / 0.55, 0.6 * MM, 0.45 * MM), verts=vs)
        bmesh.ops.translate(bm, vec=(p[0] * MM, p[1] * MM, p[2] * MM), verts=vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(material)
    return ob


def samara_mesh(name, seeds, material):
    """Flat oval seed wafers (3.6 x 2.4 x 0.9 mm) along each fibre tip's direction."""
    import bmesh
    from mathutils import Matrix
    bm = bmesh.new()
    for s in seeds:
        d = Vector(s["d"]).normalized()
        u = d.cross(Vector((0, 0, 1)))
        u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0))
        w = d.cross(u).normalized()
        c = Vector(s["p"]) + d * 1.5
        M4 = Matrix(((d.x * 1.8, u.x * 1.2, w.x * 0.45, c.x), (d.y * 1.8, u.y * 1.2, w.y * 0.45, c.y),
                     (d.z * 1.8, u.z * 1.2, w.z * 0.45, c.z), (0, 0, 0, 1)))
        M4 = Matrix.Scale(MM, 4) @ M4
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0, matrix=M4)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(material)
    return ob


THICK_R = 2.2      # wood at least this thick is meshed as one blended body (smooth forks and collars)


def blended_wood(branches, material, voxel=0.45):
    """Trunk, roots and the thicker branches as ONE mesh: the tubes are voxel-remeshed together
    and relaxed, so every fork grows out of its parent with a smooth collar like real wood."""
    thick = [b for b in branches if b["l"] <= 0 or max(b["r"]) >= THICK_R]
    ob = curve_tube("wood", [b["p"] for b in thick], material, radii=[b["r"] for b in thick])
    ob.data.bevel_resolution = 8
    ob.data.resolution_u = 2
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.view_layer.objects.active
    rm = ob.modifiers.new("remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel * MM
    rm.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier="remesh")
    sm = ob.modifiers.new("relax", "SMOOTH")
    sm.factor = 0.8
    sm.iterations = 6
    bpy.ops.object.modifier_apply(modifier="relax")
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.name = "wood"
    return ob


def foliage_mesh(name, leaves, material):
    """Leaf-film foliage: one flat cedar-elm leaf (8-point outline, slight cup) per entry."""
    import bmesh, random
    OUT = ((0.0, 0.0), (0.18, 0.30), (0.45, 0.36), (0.75, 0.24), (1.0, 0.0),
           (0.75, -0.22), (0.45, -0.33), (0.18, -0.28))
    rnd = random.Random(5)
    bm = bmesh.new()
    tone = bm.faces.layers.float.new("tone")
    for f in leaves:
        p, a, n, s = Vector(f["p"]), Vector(f["a"]), Vector(f["n"]), f["s"]
        w = n.cross(a).normalized()
        vs = [bm.verts.new(((p + a * (s * u) + w * (s * v) + n * (0.25 * s * abs(v))) * MM)) for u, v in OUT]
        face = bm.faces.new(vs)
        face[tone] = rnd.random()
        face.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    # expose the per-leaf tone to the shader as a face attribute
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(material)
    return ob


def build_lamp(M, crown_light=0.0):
    """Base from STL, the tree, branches/sprigs/leaves from the skeleton in parts.json."""
    meta = json.load(open(os.path.join(MECH, "parts.json")))
    obs = {}
    for name in PART_MAT:
        ob = import_stl(name)
        ob.data.materials.append(M[PART_MAT[name]])
        obs[name] = ob
    sk = meta["skeleton"]
    obs["wood"] = blended_wood(sk["branches"], M["bark_glow"])
    thin = [b for b in sk["branches"] if b["l"] >= 1 and max(b["r"]) < THICK_R]
    obs["branches"] = curve_tube("branches", [b["p"] for b in thin], M["bark"], radii=[b["r"] for b in thin])
    obs["foliage"] = foliage_mesh("foliage", meta["foliage"], M["leaf_film"])
    for c in ("W", "C"):
        ss = [s for s in meta.get("samaras", []) if s["ch"][0] == c]
        if ss:
            obs["samaras_" + c] = samara_mesh("samaras_" + c, ss, M["samara_" + c])
    stems = [st for sp in sk["sprigs"] for st in sp["stems"]]
    pets = [pt for sp in sk["sprigs"] for pt in sp["pet"]]
    obs["sprigs"] = curve_tube("sprig_stems", stems, M["flex"], const_r=0.45 * MM)
    obs["petioles"] = curve_tube("sprig_petioles", pets, M["flex"], const_r=0.28 * MM)
    for c in ("W", "C"):
        pts = [l["p"] for l in meta["leaves"] if l["ch"][0] == c]
        obs["leaves_" + c] = leaf_mesh("leaves_" + c, pts, M["leaf_" + c])
    if crown_light > 0:
        # aggregate light of 800 tiny LEDs onto the desk: a few soft area lights inside the crown
        cc = meta["crown_center"]
        lv = meta["leaves"]
        for k in range(6):
            sub = lv[k::6]
            x = sum(l["p"][0] for l in sub) / len(sub)
            y = sum(l["p"][1] for l in sub) / len(sub)
            z = min(l["p"][2] for l in sub)
            l = bpy.data.lights.new(f"crown{k}", "AREA")
            l.shape = "DISK"
            l.size = 0.12
            l.energy = 6.0 * crown_light
            l.color = (1.0, 0.80, 0.60)
            ob = bpy.data.objects.new(f"crown{k}", l)
            bpy.context.scene.collection.objects.link(ob)
            ob.location = (x * MM, y * MM, (z - 12.0) * MM)   # just under the crown, firing down
    return obs, meta


def glare(strength=0.35, size=0.10):
    """Compositor fog-glow so each tiny LED leaf blooms a little, like it does to the eye.
    (Blender 5 node-group compositor.)"""
    s = bpy.context.scene
    tree = bpy.data.node_groups.new("comp", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers")
    gl = tree.nodes.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Fog Glow"
    gl.inputs["Quality"].default_value = "High"
    gl.inputs["Threshold"].default_value = 2.5
    gl.inputs["Strength"].default_value = strength
    gl.inputs["Size"].default_value = size
    out = tree.nodes.new("NodeGroupOutput")
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"])
    tree.links.new(gl.outputs["Image"], out.inputs[0])
    s.compositing_node_group = tree


def props(M):
    paper = mat("paper", (0.86, 0.84, 0.79), 0.0, 0.8)
    cover = mat("cover", (0.07, 0.11, 0.15), 0.0, 0.55)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.17, -0.22, 0.006))
    nb = bpy.context.active_object
    nb.scale = (0.15, 0.21, 0.012)
    nb.rotation_euler = (0, 0, math.radians(-14))
    nb.data.materials.append(cover)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.05, -0.26, 0.0012))
    sh = bpy.context.active_object
    sh.scale = (0.21, 0.297, 0.0024)
    sh.rotation_euler = (0, 0, math.radians(9))
    sh.data.materials.append(paper)


def main():
    global BACKDROP_ROT
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--res", default="1920x1280")
    ap.add_argument("--out", default=None)
    ap.add_argument("--view", default=None, help="camera override: az,el,dist_m,target_z_m,lens")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    res = tuple(int(v) for v in args.res.split("x"))
    FORK_Z[0] = json.load(open(os.path.join(MECH, "parts.json")))["hub"][2] * MM + 0.009
    bpy.ops.wm.read_factory_settings(use_empty=True)
    out = args.out or os.path.join(HERE, f"eclipse_{args.shot}.png")
    shot = args.shot
    crown_glow = [0.0, (1.0, 0.78, 0.55)]
    T = (0.0, 0.0, 0.20)

    if shot == "hero":
        # evening: the crown sparkling, the trunk glowing through its fissures, a pool on the desk
        M = build_materials(on=True, level=1.0, cool_mix=0.35, trunk=1.0)
        obs, meta = build_lamp(M, crown_light=1.0)
        crown_glow[0] = 1.0
        add_plane("desk", 3.0, (0, 0, 0), wood_material())
        add_plane("wall", 4.0, (0, 0.45, 1.0), mat("wall", (0.24, 0.23, 0.21), 0.0, 0.95), rot=(math.pi / 2, 0, 0))
        props(M)
        world((0.004, 0.005, 0.009), 1.0)
        area("fill", orbit(-150, 25, 1.6, T), T, 1.5, 2, (0.55, 0.65, 1.0))
        area("rim", orbit(60, 35, 1.2, T), T, 0.8, 4, (1.0, 0.9, 0.8))
        tgt = (0.0, 0.0, 0.205)
        camera(orbit(-58, 4, 1.05, tgt), tgt, lens=40)
        bpy.context.scene.view_settings.exposure = -0.2
        glare()
    elif shot == "studio":
        # daylight product shot: the lamp off, read as a bronze sculpture
        M = build_materials(on=False)
        obs, meta = build_lamp(M)
        BACKDROP_ROT = 125 - 90
        backdrop(mat("sweep", (0.80, 0.80, 0.80), 0.0, 0.6), width=9, depth=6, height=4, radius=1.0)
        world((0.6, 0.6, 0.62), 0.25)
        area("key", orbit(-125, 40, 1.8, T), T, 1.8, 150)
        area("fill", orbit(-20, 15, 1.8, T), T, 1.8, 45)
        area("top", (0, 0.0, 1.8), (0, 0.0, 0), 1.4, 70)
        tgt = (0.0, 0.0, 0.20)
        camera(orbit(-55, 10, 1.45, tgt), tgt, lens=50)
    elif shot == "leaves":
        # macro: flex sprigs and 0402 LED leaves
        M = build_materials(on=True, level=0.35, cool_mix=0.35)
        obs, meta = build_lamp(M, crown_light=0.3)
        crown_glow[0] = 0.25
        add_plane("wall", 4.0, (0, 0.45, 1.0), mat("wall", (0.18, 0.17, 0.16), 0.0, 0.95), rot=(math.pi / 2, 0, 0))
        add_plane("desk", 3.0, (0, 0, 0), wood_material())
        world((0.01, 0.011, 0.016), 1.0)
        area("rim", orbit(40, 30, 0.8, T), T, 0.6, 4, (1.0, 0.9, 0.8))
        lv = sorted(meta["leaves"], key=lambda l: (l["p"][1], -l["p"][0]))
        cx = lv[len(lv) // 8]["p"]
        tgt = (cx[0] * MM, cx[1] * MM, cx[2] * MM)
        camera(orbit(-70, 5, 0.22, tgt), tgt, lens=85, dof=0.22, fstop=6.0)
        bpy.context.scene.view_settings.exposure = -0.3
        glare(size=0.08)
    elif shot == "night":
        # night mode: crown dimmed to embers, the base band (roots) breathing a warm glow
        M = build_materials(on=True, level=0.02, band=4.0, cool_mix=0.0)
        obs, meta = build_lamp(M, crown_light=0.02)
        crown_glow[0] = 0.04
        add_plane("desk", 3.0, (0, 0, 0), wood_material())
        add_plane("wall", 4.0, (0, 0.45, 1.0), mat("wall", (0.20, 0.19, 0.18), 0.0, 0.95), rot=(math.pi / 2, 0, 0))
        world((0.004, 0.005, 0.009), 1.0)
        area("moon", orbit(150, 30, 1.5, T), T, 1.2, 8.0, (0.55, 0.65, 1.0))
        tgt = (0.0, 0.0, 0.17)
        camera(orbit(-62, 10, 1.25, tgt), tgt, lens=45)
        glare(size=0.12)
    elif shot == "detail":
        M = build_materials(on=True, level=0.6, cool_mix=0.35)
        obs, meta = build_lamp(M, crown_light=0.4)
        crown_glow[0] = 0.6
        add_plane("desk", 3.0, (0, 0, 0), wood_material())
        world((0.02, 0.022, 0.03), 1.0)
        area("key", (-0.5, -0.5, 0.6), (0, -0.03, 0.02), 0.5, 18, (1.0, 0.95, 0.9))
        area("rim", (0.4, 0.4, 0.3), (0, 0, 0.02), 0.4, 8, (0.8, 0.85, 1.0))
        camera((0.16, -0.30, 0.17), (0.0, -0.02, 0.02), lens=85, dof=0.36, fstop=3.2)
    elif shot == "trunk":
        # close-up: light leaking from the trunk's light-guide core through the bark fissures
        M = build_materials(on=True, level=0.25, cool_mix=0.25, trunk=0.9)
        obs, meta = build_lamp(M, crown_light=0.15)
        crown_glow[0] = 0.25
        add_plane("desk", 3.0, (0, 0, 0), wood_material())
        add_plane("wall", 4.0, (0, 0.45, 1.0), mat("wall", (0.18, 0.17, 0.16), 0.0, 0.95), rot=(math.pi / 2, 0, 0))
        world((0.006, 0.007, 0.010), 1.0)
        area("rim", orbit(70, 25, 0.9, (0, 0.03, 0.1)), (0, 0.03, 0.1), 0.6, 3, (0.8, 0.85, 1.0))
        tgt = (0.0, 0.02, 0.12)
        camera(orbit(-65, 8, 0.66, tgt), tgt, lens=60, dof=0.66, fstop=5.6)
        glare(size=0.08)
    elif shot == "cool":
        # same scene as hero with the colour temperature slid to daylight
        M = build_materials(on=True, level=1.0, cool_mix=1.0)
        obs, meta = build_lamp(M, crown_light=1.0)
        crown_glow[:] = [1.0, (0.85, 0.92, 1.0)]
        add_plane("desk", 3.0, (0, 0, 0), wood_material())
        add_plane("wall", 4.0, (0, 0.45, 1.0), mat("wall", (0.26, 0.25, 0.23), 0.0, 0.95), rot=(math.pi / 2, 0, 0))
        props(M)
        world((0.008, 0.010, 0.016), 1.0)
        for ob in bpy.data.objects:
            if ob.name.startswith("crown"):
                ob.data.color = (0.85, 0.92, 1.0)
        tgt = (0.0, 0.0, 0.215)
        camera(orbit(-60, 8, 1.12, tgt), tgt, lens=45)
        bpy.context.scene.view_settings.exposure = -0.4
        glare()
    else:
        raise SystemExit("unknown shot " + shot)

    if args.view:
        az, el, dist, tz, lens = (float(v) for v in args.view.split(","))
        tgt = (0.0, 0.0, tz)
        bpy.context.scene.camera.data.lens = lens
        bpy.context.scene.camera.location = orbit(az, el, dist, tgt)
        look_at(bpy.context.scene.camera, tgt)
    # inner canopy glow: the 800 LED leaves light the leaf film around them (stand-in for the
    # many small emitters, which Cycles would need thousands of samples to resolve)
    if crown_glow[0] > 0:
        lv = meta["leaves"]
        g = bpy.data.collections.new("canopy")
        for name in ("foliage", "wood", "branches"):
            g.objects.link(bpy.data.objects[name])
        for k in range(10):
            sub = lv[k::10]
            c = [sum(l["p"][i] for l in sub) / len(sub) for i in range(3)]
            l = bpy.data.lights.new(f"canopy{k}", "POINT")
            l.shadow_soft_size = 0.05
            l.energy = 1.0 * crown_glow[0]
            l.color = crown_glow[1]
            ob = bpy.data.objects.new(f"canopy{k}", l)
            bpy.context.scene.collection.objects.link(ob)
            ob.location = (c[0] * MM, c[1] * MM, c[2] * MM)
            ob.light_linking.receiver_collection = g
    # the crown helper lights stand in for 800 LEDs lighting the room: they must not light the tree
    tree_parts = {"wood", "branches", "foliage", "sprig_stems", "sprig_petioles", "leaves_W", "leaves_C",
                  "samaras_W", "samaras_C"}
    crown = [o for o in bpy.data.objects if o.name.startswith("crown")]
    if crown:
        coll = bpy.data.collections.new("lit_by_crown")
        for o in bpy.data.objects:
            if o.type in ("MESH", "CURVE") and o.name not in tree_parts:
                coll.objects.link(o)
        for o in crown:
            o.light_linking.receiver_collection = coll
    setup_render(args.samples, res, out)
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


if __name__ == "__main__":
    main()
