"""ECLIPSE Tree desk lamp - parametric 3D model (CadQuery).

Frame: X right, Y toward the REAR of the lamp, Z up; origin = centre of the
base footprint on the desk.  All dimensions in mm.

    python3 eclipse_cad.py [--out DIR]

Writes one STEP + STL per part, a coloured assembly STEP and a JSON file with
part placements (consumed by the Blender render script).
"""
import argparse, json, math, os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
ELEC = os.path.join(HERE, "..", "electronics")

# ----------------------------------------------------------------- parameters
BASE_D, BASE_H = 150.0, 22.0
BASE_WALL, BASE_SKIN = 6.0, 3.0
TOUCH_XY, TOUCH_D = (0.0, -30.0), 52.0
STEM_XY = (0.0, 58.0)
STEM_OD, STEM_ID = 14.0, 10.0       # trunk socket in the base
USB_PHI = 90.0                   # USB-C direction (deg, clockwise from rear seen from above)
PCB_TOP_Z = BASE_H - BASE_SKIN   # core PCB top face pressed against the skin
import tree_gen as TG                  # procedural cedar-elm skeleton (seeded)
HUB_D, HUB_T = 56.0, 1.0               # hub light-engine PCB inside the fork swelling
SHELL_T = 2.5                          # cast bronze trunk shell around the light-guide core
SHELL_Z0 = 10.0                  # aluminium upper shell of the base starts here
BAND_Z0, BAND_Z1 = 3.0, SHELL_Z0  # glowing opal band between plinth and shell
WEIGHT_D = 110.0                 # leaves an annular light chamber behind the band


# ----------------------------------------------------------------- base
def base_shell():
    body = (cq.Workplane("XY").workplane(offset=SHELL_Z0).circle(BASE_D / 2).extrude(BASE_H - SHELL_Z0)
            .faces(">Z").edges().fillet(5.0)
            .faces("<Z").edges().chamfer(0.4))
    # hollow from below, leaving the top skin
    cav = cq.Workplane("XY").circle(BASE_D / 2 - BASE_WALL).extrude(BASE_H - BASE_SKIN)
    body = body.cut(cav)
    # touch window
    body = body.cut(cq.Workplane("XY").center(*TOUCH_XY).circle(TOUCH_D / 2 + 0.1).extrude(BASE_H + 1))
    # glow slot for the status LED is the window itself; add a fine engraved ring around the window
    groove = (cq.Workplane("XY").workplane(offset=BASE_H - 0.4).center(*TOUCH_XY)
              .circle(TOUCH_D / 2 + 3.0).circle(TOUCH_D / 2 + 2.4).extrude(1))
    body = body.cut(groove)
    # stem socket: collar on top + internal boss with bore
    collar = (cq.Workplane("XY").workplane(offset=BASE_H - 1).center(*STEM_XY).circle(11).extrude(5)
              .faces(">Z").edges().fillet(1.5))
    boss = cq.Workplane("XY").workplane(offset=SHELL_Z0).center(*STEM_XY).circle(10.5).extrude(BASE_H - SHELL_Z0)
    body = body.union(collar).union(boss)
    body = body.cut(cq.Workplane("XY").workplane(offset=10).center(*STEM_XY).circle(STEM_OD / 2 + 0.1).extrude(30))
    body = body.cut(cq.Workplane("XY").workplane(offset=5).center(*STEM_XY).circle(4).extrude(10))
    # side slot for the harness from the boss into the cavity
    body = body.cut(cq.Workplane("XY").workplane(offset=10).center(STEM_XY[0], STEM_XY[1] - 9).rect(7, 8).extrude(6))
    # USB-C port: pocket for the board tab + rounded slot through the wall
    a = math.radians(USB_PHI)
    d = (math.sin(a), math.cos(a))
    ang = -USB_PHI  # rotate about Z so local +Y points along d
    pocket = (cq.Workplane("XY").workplane(offset=PCB_TOP_Z - 7).rect(15, 12).extrude(7)
              .translate((0, BASE_D / 2 - BASE_WALL + 1.5, 0)).rotate((0, 0, 0), (0, 0, 1), ang))
    slot = (cq.Workplane("XZ").workplane(offset=-(BASE_D / 2 + 2))
            .center(0, PCB_TOP_Z - 1.6 - 1.6).slot2D(9.6, 3.9).extrude(10)
            .rotate((0, 0, 0), (0, 0, 1), ang))
    body = body.cut(pocket).cut(slot)
    # three M3 screw bosses for the core PCB (under the skin)
    for phi in (150, 220, 312):
        x, y = 55 * math.sin(math.radians(phi)), 55 * math.cos(math.radians(phi))
        # KiCad y is flipped vs CAD y, and KiCad angles are measured from the rear clockwise
        b = cq.Workplane("XY").workplane(offset=PCB_TOP_Z).center(x, y).circle(3.5).extrude(BASE_SKIN - 0.6)
        body = body.union(b)
    return body


def base_weight():
    """Steel weight, white powder-coated: doubles as the reflector of the light chamber."""
    w = cq.Workplane("XY").workplane(offset=BAND_Z0).circle(WEIGHT_D / 2).extrude(6.5)
    return w.faces(">Z").edges().fillet(1.0)


def base_band():
    """Light-diffusing opal ring between plinth and shell: the base glows through its body."""
    return (cq.Workplane("XY").workplane(offset=BAND_Z0).circle(BASE_D / 2 - 1.0).circle(BASE_D / 2 - BASE_WALL)
            .extrude(BAND_Z1 - BAND_Z0))


def base_plinth():
    """Steel foot plate (black powder coat) with three posts that clamp the band to the shell.
    Steel here keeps the centre of gravity well back with the heavier glowing head."""
    p = (cq.Workplane("XY").circle(BASE_D / 2).extrude(BAND_Z0)
         .faces("<Z").edges().chamfer(0.8).faces(">Z").edges().chamfer(0.3))
    for phi in (150, 220, 312):
        x, y = 64 * math.sin(math.radians(phi)), 64 * math.cos(math.radians(phi))
        p = p.union(cq.Workplane("XY").workplane(offset=BAND_Z0).center(x, y).circle(2.5).extrude(BAND_Z1 - BAND_Z0))
    return p


def base_foot():
    return (cq.Workplane("XY").workplane(offset=-1.0).circle(BASE_D / 2 - 2).circle(BASE_D / 2 - 14)
            .extrude(1.0))


def touch_glass():
    g = (cq.Workplane("XY").workplane(offset=PCB_TOP_Z).center(*TOUCH_XY).circle(TOUCH_D / 2).extrude(BASE_SKIN)
         .faces(">Z").edges().fillet(0.6))
    # etched wheel ring + centre dot (0.15 mm deep)
    etch = (cq.Workplane("XY").workplane(offset=BASE_H - 0.15).center(*TOUCH_XY)
            .circle(22.6).circle(21.8).extrude(1))
    dot = cq.Workplane("XY").workplane(offset=BASE_H - 0.15).center(*TOUCH_XY).circle(1.2).extrude(1)
    return g.cut(etch).cut(dot)


def touch_etch():
    """The etched marks as a separate thin body (rendered with a lighter finish)."""
    e = (cq.Workplane("XY").workplane(offset=BASE_H - 0.15).center(*TOUCH_XY)
         .circle(22.6).circle(21.8).extrude(0.14))
    return e.union(cq.Workplane("XY").workplane(offset=BASE_H - 0.15).center(*TOUCH_XY).circle(1.2).extrude(0.14))


# ----------------------------------------------------------------- tree
def _tube(points, radii):
    """Tapered round 'wood' along a polyline: cones per segment + spheres at the joints."""
    out = []
    for i, (p, q) in enumerate(zip(points, points[1:])):
        d = cq.Vector(*q) - cq.Vector(*p)
        h = d.Length
        if h < 1e-3:
            continue
        if abs(radii[i] - radii[i + 1]) < 1e-4:
            out.append(cq.Solid.makeCylinder(radii[i], h, cq.Vector(*p), d.normalized()))
        else:
            out.append(cq.Solid.makeCone(radii[i], radii[i + 1], h, cq.Vector(*p), d.normalized()))
        if 0 < i:
            out.append(cq.Solid.makeSphere(radii[i], cq.Vector(*p), angleDegrees1=-90, angleDegrees2=90))
    return out


CAST_R = 6.0     # wood thicker than this is part of the hollow bronze casting (trunk, leaders, limbs)


def tree_solids(tree):
    """Trunk casting (trunk + flare + buttress roots) and the rest of the wood."""
    trunk = _tube(tree.branches[0]["points"], tree.branches[0]["radii"])
    for r in tree.roots:
        trunk += _tube(r["points"], r["radii"])
    # the buttress roots are half buried: trim everything below the base top
    above = cq.Solid.makeBox(400, 400, 300, cq.Vector(-200, -200, BASE_H))
    trunk = [s.intersect(above) for s in trunk]
    wood = []
    for b in tree.branches[1:]:
        if b["level"] >= 1:
            wood += _tube(b["points"], b["radii"])
    return cq.Compound.makeCompound(trunk), cq.Compound.makeCompound(wood)


CORE_WALL = 8.0     # PMMA light-guide tube wall


def trunk_core(tree):
    """Light-diffusing PMMA light guide inside the trunk shell: a thick-walled tube (TIR guide)
    lit from the top by the hub's 8 bottom LEDs; light escapes through the bark fissures.
    The trunk harness runs up its bore."""
    b = tree.branches[0]
    out = []
    pts, rad = b["points"], [r - SHELL_T - 0.5 for r in b["radii"]]
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        d = cq.Vector(*q) - cq.Vector(*p)
        if d.Length < 1e-3 or rad[i + 1] < CORE_WALL + 3 or q[2] > tree.hub[2] - 6.0:
            continue        # the tube ends under the hub's coupling disc
        def cone(r0, r1, h, at):
            if abs(r0 - r1) < 1e-4:
                return cq.Solid.makeCylinder(r0, h, at, d.normalized())
            return cq.Solid.makeCone(r0, r1, h, at, d.normalized())
        o = cone(rad[i], rad[i + 1], d.Length, cq.Vector(*p))
        n = cone(rad[i] - CORE_WALL, rad[i + 1] - CORE_WALL, d.Length * 1.02,
                 cq.Vector(*p) - d.normalized() * d.Length * 0.01)
        out.append(o.cut(n))
    return cq.Compound.makeCompound(out)


def samara_solids(tree):
    """Samaras (cedar-elm seeds): 3.6 x 2.4 x 0.9 mm diffusing epoxy wafers on the fibre tips."""
    from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
    from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
    unit = cq.Solid.makeSphere(1.0, angleDegrees1=-90, angleDegrees2=90).wrapped
    out = []
    for s in tree.samaras:
        d = cq.Vector(*s["dir"]).normalized()
        u = d.cross(cq.Vector(0, 0, 1))
        u = u.normalized() if u.Length > 1e-6 else cq.Vector(1, 0, 0)
        w = d.cross(u).normalized()
        # columns: seed long axis along the twig (1.8 mm half), half-width 1.2 mm, half-thickness 0.45 mm
        m = gp_Mat(d.x * 1.8, u.x * 1.2, w.x * 0.45, d.y * 1.8, u.y * 1.2, w.y * 0.45, d.z * 1.8, u.z * 1.2, w.z * 0.45)
        g = gp_GTrsf()
        g.SetVectorialPart(m)
        c = cq.Vector(*s["pos"]) + d * 1.5
        g.SetTranslationPart(gp_XYZ(c.x, c.y, c.z))
        out.append(cq.Shape.cast(BRepBuilderAPI_GTransform(unit, g, True).Shape()))
    return cq.Compound.makeCompound(out)


def foliage_stl(tree, path):
    """Leaf-film foliage as a binary STL (thousands of flat 0.125 mm leaves: a cutting file, not
    a solid model). Each leaf is the cedar-elm outline used by the renderer."""
    import struct
    tris = []
    for f in tree.foliage:
        for a, b, c in leaf_tris(f):
            tris.append((a, b, c))
    with open(path, "wb") as fh:
        fh.write(b"eclipse foliage".ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            fh.write(struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0))
    return len(tris)


LEAF_OUTLINE = ((0.0, 0.0), (0.18, 0.30), (0.45, 0.36), (0.75, 0.24), (1.0, 0.0),
                (0.75, -0.22), (0.45, -0.33), (0.18, -0.28))   # (along, across) x leaf length


def leaf_tris(f):
    p, ax, n, s = f["pos"], f["axis"], f["normal"], f["size"]
    w = TG.v_norm(TG.v_cross(n, ax))
    vs = [TG.v_add(TG.v_add(p, TG.v_mul(ax, s * u)), TG.v_mul(w, s * v)) for u, v in LEAF_OUTLINE]
    return [(vs[0], vs[k], vs[k + 1]) for k in range(1, len(vs) - 1)]


def mass_report(tree, solids):
    """Mass and centre of gravity from the skeleton (wall fractions per construction) + base parts."""
    def seg_iter(points, radii):
        for (p, q), r0, r1 in zip(zip(points, points[1:]), radii, radii[1:]):
            yield [(p[i] + q[i]) / 2 for i in range(3)], TG.v_len(TG.v_sub(q, p)), (r0 + r1) / 2
    m_tot, mom = 0.0, [0.0, 0.0, 0.0]
    def add(m, c):
        nonlocal m_tot
        m_tot += m
        for i in range(3):
            mom[i] += m * c[i]
    BRONZE, BRASS, PMMA = 8.8e-3, 8.5e-3, 1.19e-3   # g/mm^3
    for c, L, r in seg_iter(tree.branches[0]["points"], tree.branches[0]["radii"]):
        ro = r - SHELL_T - 0.5
        add(2 * math.pi * r * SHELL_T * L * BRONZE + math.pi * max(0, ro ** 2 - (ro - CORE_WALL) ** 2) * L * PMMA, c)
    for rt in tree.roots:
        for c, L, r in seg_iter(rt["points"], rt["radii"]):
            add(2 * math.pi * r * SHELL_T * L * BRONZE, c)
    for b in tree.branches[1:]:
        if b["level"] < 1:
            continue
        for c, L, r in seg_iter(b["points"], b["radii"]):
            if r >= CAST_R:
                v = 2 * math.pi * r * 2.0 * L               # cast shell, 2 mm wall
            elif r >= 2.0:
                v = 2 * math.pi * r * 0.8 * L               # brass tube, 0.8 mm wall
            else:
                v = math.pi * r * r * L                     # solid rod / wire
            add(v * (BRONZE if r >= CAST_R else BRASS), c)
    for f in tree.foliage:
        add(f["size"] ** 2 * 0.5 * 0.125 * 1.4e-3, f["pos"])
    for l in tree.leaves:
        add(0.02, l["pos"])
    for s in tree.samaras:
        add(0.03, s["pos"])
    dens = {"base_shell": 2.7e-3, "base_weight": 7.85e-3, "base_band": 1.19e-3, "base_plinth": 7.85e-3,
            "touch_glass": 2.5e-3}
    for name, d in dens.items():
        sh = solids[name]
        sh = sh.val() if hasattr(sh, "val") else sh
        c = sh.Center()
        add(sh.Volume() * d, (c.x, c.y, c.z))
    add(45.0, (0, 0, 14))           # core PCBA + harness + screws
    cog = [mom[i] / m_tot for i in range(3)]
    off = math.hypot(cog[0], cog[1])
    return m_tot, cog, off


def sprig_solids(tree):
    """Flex sprigs: polyimide ribbons modelled as thin rods (stem 0.45, petiole 0.28 mm radius)."""
    out = []
    for sp in tree.sprig_paths:
        for st in sp["stems"]:
            out += _tube(st, [0.45] * len(st))
        for b, p in sp["petioles"]:
            out += _tube([b, p], [0.28, 0.28])
    return cq.Compound.makeCompound(out)


def leaf_solids(tree, channel_prefix):
    """0402 LEDs (1.0 x 0.5 x 0.35) at the end of every petiole: the leaves."""
    out = []
    for lf in tree.leaves:
        if lf["channel"][0] != channel_prefix:
            continue
        d = cq.Vector(*lf["dir"])
        ref = cq.Vector(0, 0, 1) if abs(d.z) < 0.9 else cq.Vector(1, 0, 0)
        n = d.cross(ref).normalized()
        pl = cq.Plane(origin=lf["pos"], xDir=d, normal=n)
        out.append(cq.Solid.makeBox(1.0, 0.5, 0.35, pnt=cq.Vector(-0.5, -0.25, -0.175)).locate(cq.Location(pl)))
    return cq.Compound.makeCompound(out)


# ----------------------------------------------------------------- PCBs (KiCad STEP)
def kicad_step(board, z, flip=False):
    path = os.path.join(ELEC, board, f"eclipse-{board}.step")
    if not os.path.exists(path):
        return None
    s = cq.importers.importStep(path)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tree = TG.Tree()
    trunk, wood = tree_solids(tree)
    parts = {
        "base_shell": (base_shell(), "anodised aluminium, graphite"),
        "base_weight": (base_weight(), "steel, white powder coat (reflector)"),
        "base_band": (base_band(), "light-diffusing opal PMMA ring (glowing roots)"),
        "base_plinth": (base_plinth(), "steel foot plate, black powder coat"),
        "base_foot": (base_foot(), "silicone/cork ring"),
        "touch_glass": (touch_glass(), "3 mm soda-lime glass, satin etch"),
        "touch_etch": (touch_etch(), "etch marks"),
        "trunk": (cq.Workplane().add(trunk), "cast silicon-bronze shell 2.5 mm (trunk, fork swelling, roots) with glowing fissures"),
        "trunk_core": (cq.Workplane().add(trunk_core(tree)), "light-diffusing PMMA light-guide tube, 8 mm wall, harness in the bore"),
        "samaras": (cq.Workplane().add(samara_solids(tree)), f"{len(tree.samaras)} x diffusing epoxy samara on 0.5 mm end-glow fibre"),
        "branches": (cq.Workplane().add(wood), "leaders/limbs cast bronze shell, branches brass tube, twigs brass rod/wire, bark patina"),
        "sprigs": (cq.Workplane().add(sprig_solids(tree)), "40 x polyimide flex sprigs, bronze coverlay"),
        "leaves_warm": (cq.Workplane().add(leaf_solids(tree, "W")), "400 x 0402 LED 2700 K"),
        "leaves_cool": (cq.Workplane().add(leaf_solids(tree, "C")), "400 x 0402 LED 6500 K"),
    }
    core = kicad_step("core", 0)
    if core is not None:
        parts["pcb_core"] = (core.translate((0, 0, PCB_TOP_Z - 1.6)), "PCBA core")
    hub = kicad_step("hub", 0)
    if hub is not None:
        parts["pcb_hub"] = (hub.translate((tree.hub[0], tree.hub[1], tree.hub[2] - 0.5)), "PCBA hub (in the fork swelling)")

    asm = cq.Assembly(name="eclipse_lamp")
    colors = {"base_shell": (0.18, 0.18, 0.19), "base_weight": (0.6, 0.6, 0.62), "bottom_cover": (0.3, 0.3, 0.3),
              "base_foot": (0.55, 0.42, 0.3), "base_band": (0.97, 0.95, 0.9), "base_plinth": (0.18, 0.18, 0.19), "touch_glass": (0.1, 0.1, 0.12), "touch_etch": (0.8, 0.8, 0.8),
              "trunk": (0.30, 0.22, 0.14), "branches": (0.30, 0.22, 0.14),
              "sprigs": (0.45, 0.32, 0.12), "leaves_warm": (1.0, 0.85, 0.5), "leaves_cool": (0.85, 0.92, 1.0),
              "trunk_core": (0.97, 0.95, 0.9), "samaras": (1.0, 0.93, 0.75),
              "pcb_core": (0.1, 0.3, 0.15), "pcb_halo": (0.95, 0.95, 0.95)}
    meta = {}
    for name, (shape, mat) in parts.items():
        fine = name.startswith("base") or name.startswith("touch") or name == "trunk_core"
        if name not in ("sprigs", "leaves_warm", "leaves_cool", "samaras", "branches"):   # rendered from the skeleton (STEP kept)
            cq.exporters.export(shape, os.path.join(args.out, name + ".stl"),
                                tolerance=0.02 if fine else 0.1, angularTolerance=0.08 if fine else 0.6)
        if not name.startswith("pcb_"):
            cq.exporters.export(shape, os.path.join(args.out, name + ".step"))
        asm.add(shape, name=name, color=cq.Color(*colors.get(name, (0.5, 0.5, 0.5))))
        bb = shape.val().BoundingBox() if hasattr(shape, "val") else shape.BoundingBox()
        meta[name] = {"material": mat, "bbox": [bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax]}
        print(f"{name:14s} {bb.xlen:7.1f} x {bb.ylen:7.1f} x {bb.zlen:7.1f}  {mat}")
    asm.save(os.path.join(args.out, "eclipse_lamp_assembly.step"))
    ntri = foliage_stl(tree, os.path.join(args.out, "foliage.stl"))
    print(f"foliage        {len(tree.foliage)} leaves, {ntri} triangles -> foliage.stl")
    m, cog, off = mass_report(tree, {k: v[0] for k, v in parts.items()})
    print(f"mass {m / 1000:.2f} kg, CoG ({cog[0]:.1f}, {cog[1]:.1f}, {cog[2]:.1f}) mm: "
          f"{off:.1f} mm from the base centre, {BASE_D / 2 - off:.1f} mm inside the edge")
    # zip the heavy STEP files (thousands of tiny solids compress ~6x)
    import zipfile
    for f in sorted(os.listdir(args.out)):
        fp = os.path.join(args.out, f)
        if f.endswith(".step") and os.path.getsize(fp) > 3e6:
            with zipfile.ZipFile(fp + ".zip", "w", zipfile.ZIP_DEFLATED) as z:
                z.write(fp, f)
            os.remove(fp)
    lx = [l["pos"] for l in tree.leaves]
    cen = [sum(p[i] for p in lx) / len(lx) for i in range(3)]
    json.dump({"crown_center": cen, "touch": list(TOUCH_XY), "hub": list(tree.hub), "mass_g": round(m), "cog": [round(c, 1) for c in cog],
               "pcb_core_z": PCB_TOP_Z - 1.6,
               "skeleton": dict(
                   branches=[dict(p=[[round(c, 2) for c in q] for q in b["points"]],
                                  r=[round(r, 3) for r in b["radii"]], l=b["level"]) for b in tree.branches],
                   sprigs=[dict(stems=[[[round(c, 2) for c in q] for q in st] for st in sp["stems"]],
                                pet=[[[round(c, 2) for c in b], [round(c, 2) for c in q]] for b, q in sp["petioles"]],
                                ch=sp["channel"]) for sp in tree.sprig_paths]),
               "leaves": [dict(p=[round(c, 2) for c in l["pos"]], ch=l["channel"], s=l["sprig"]) for l in tree.leaves],
               "samaras": [dict(p=[round(c, 2) for c in s["pos"]], d=[round(c, 3) for c in s["dir"]], ch=s["channel"])
                           for s in tree.samaras],
               "foliage": [dict(p=[round(c, 2) for c in f["pos"]], a=[round(c, 3) for c in f["axis"]],
                                n=[round(c, 3) for c in f["normal"]], s=round(f["size"], 2)) for f in tree.foliage],
               "n_roots": len(tree.roots),
               "parts": meta}, open(os.path.join(args.out, "parts.json"), "w"), indent=0)


if __name__ == "__main__":
    main()
