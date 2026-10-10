"""ECLIPSE desk lamp - parametric 3D model (CadQuery).

Frame: X right, Y toward the REAR of the lamp, Z up; origin = centre of the
base footprint on the desk.  All dimensions in mm.

    python3 eclipse_cad.py [--tilt DEG] [--out DIR]

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
STEM_OD, STEM_ID = 12.0, 8.0
STEM_TOP = 350.0                 # where the vertical run ends
BEND_R = 90.0                    # radius of the forward bend
USB_PHI = 90.0                   # USB-C direction (deg, clockwise from rear seen from above)
PCB_TOP_Z = BASE_H - BASE_SKIN   # core PCB top face pressed against the skin
HINGE_Z = STEM_TOP + BEND_R      # 440
HINGE_Y = STEM_XY[1] - BEND_R - 10.0
RING_OD, RING_ID, RING_H = 212.0, 148.0, 25.0   # total halo height (diffusing body + cap)
CAP_T = 3.0                      # graphite aluminium cap on top of the glowing body
BODY_H = RING_H - CAP_T          # solid light-diffusing PMMA body
SHELL_Z0 = 10.0                  # aluminium upper shell of the base starts here
BAND_Z0, BAND_Z1 = 3.0, SHELL_Z0  # glowing opal band between plinth and shell
WEIGHT_D = 110.0                 # leaves an annular light chamber behind the band
RING_GAP = 10.0                  # hinge axis -> ring outer edge
RING_CY = HINGE_Y - RING_GAP - RING_OD / 2
RING_TOP_Z = HINGE_Z + 1.0


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


# ----------------------------------------------------------------- stem & hinge
def stem_path():
    x, y = STEM_XY
    return (cq.Workplane("YZ").moveTo(y, 10.0).lineTo(y, STEM_TOP)
            .radiusArc((y - BEND_R, STEM_TOP + BEND_R), -BEND_R)
            .lineTo(HINGE_Y + 9.0, HINGE_Z))


def stem():
    path = stem_path().wire().val()
    prof = cq.Workplane("XY").workplane(offset=10.0).center(*STEM_XY).circle(STEM_OD / 2).circle(STEM_ID / 2)
    return prof.sweep(cq.Workplane().add(path), transition="round")


def hinge_yoke():
    """Fork clamped on the stem end; two cheeks carry the pivot."""
    y0 = HINGE_Y + 14.0
    hub = (cq.Workplane("XZ").workplane(offset=-y0).center(0, HINGE_Z).circle(8.0).extrude(5.0))
    cheeks = None
    for sx in (-1, 1):
        c = (cq.Workplane("YZ").workplane(offset=sx * 9.5 - 2.0).center(HINGE_Y, HINGE_Z)
             .circle(7.0).extrude(4.0))
        bar = cq.Workplane("XY").box(4.0, y0 - HINGE_Y, 14.0).translate((sx * 9.5, (y0 + HINGE_Y) / 2, HINGE_Z))
        c = c.union(bar)
        cheeks = c if cheeks is None else cheeks.union(c)
    bridge = cq.Workplane("XY").box(23.0, 6.0, 14.0).translate((0, y0 - 3.0, HINGE_Z))
    y = hub.union(cheeks).union(bridge)
    y = y.cut(cq.Workplane("XZ").workplane(offset=-(y0 + 6)).center(0, HINGE_Z).circle(STEM_OD / 2 + 0.05).extrude(8))
    y = y.cut(cq.Workplane("YZ").workplane(offset=-20).center(HINGE_Y, HINGE_Z).circle(2.0).extrude(40))
    return y


def hinge_knob():
    k = (cq.Workplane("YZ").workplane(offset=11.5).center(HINGE_Y, HINGE_Z).circle(9.0).extrude(6.0)
         .faces(">X").edges().fillet(1.5))
    for i in range(24):  # knurl flutes
        a = 2 * math.pi * i / 24
        f = (cq.Workplane("YZ").workplane(offset=11.5).center(HINGE_Y + 9.0 * math.cos(a), HINGE_Z + 9.0 * math.sin(a))
             .circle(0.7).extrude(5.0))
        k = k.cut(f)
    return k


# ----------------------------------------------------------------- halo head (built at origin, then placed)
def _cap_local():
    """Graphite cap + hinge knuckle in the halo frame (centre at origin, halo bottom at z=0)."""
    ro, ri, h = RING_OD / 2, RING_ID / 2, RING_H
    cap = (cq.Workplane("XY").workplane(offset=BODY_H).circle(ro).circle(ri).extrude(CAP_T)
           .faces(">Z").edges().fillet(1.2))
    groove = cq.Workplane("XY").workplane(offset=h - 0.4).circle(96.4).circle(95.6).extrude(1)
    cap = cap.cut(groove)
    axis_y = ro + RING_GAP
    axis_z = HINGE_Z - (RING_TOP_Z - RING_H)
    # rear hood: covers the PCB connector tab and carries the knuckle
    hood = cq.Workplane("XY").box(32.0, 16.0, 11.0).translate((0, ro + 1.0, h - 5.5))
    neck = cq.Workplane("XY").box(14.0, RING_GAP + 4.0, 7.0).translate((0, ro + RING_GAP / 2, h - 3.5))
    barrel = cq.Workplane("YZ").workplane(offset=-7.0).center(axis_y, axis_z).circle(6.5).extrude(14.0)
    cap = cap.union(hood).union(neck).union(barrel)
    cap = cap.cut(cq.Workplane("XY").cylinder(16, 2.05, direct=(1, 0, 0)).translate((0, axis_y, axis_z)))
    # inside the hood: room for the connector tab, and the harness channel to the knuckle
    cap = cap.cut(cq.Workplane("XY").box(29.0, 13.0, 9.0).translate((0, ro - 0.5, BODY_H - 4.5)))
    cap = cap.cut(cq.Workplane("XY").box(6.0, RING_GAP + 4.0, 5.0).translate((0, ro + RING_GAP / 2, h - 5.0)))
    return cap


def _body_local():
    """Light-diffusing PMMA halo body (moulded as an inverted U). The LED board closes its top
    and fires down into it: the whole body glows, brightest through its underside."""
    ro, ri = RING_OD / 2, RING_ID / 2
    b = cq.Workplane("XY").circle(ro).circle(ri).extrude(BODY_H)
    b = b.faces("<Z").edges().fillet(9.0)
    # hollow light-mixing chamber, open at the top where the LED board closes it:
    # 4 mm diffusing floor, 5.4 mm diffusing side walls (keeps the head light: ~200 g)
    b = b.cut(cq.Workplane("XY").workplane(offset=4.0).circle(100.6).circle(79.4).extrude(BODY_H))
    # rear notch for the connector tab under the hood
    b = b.cut(cq.Workplane("XY").box(30.0, 14.0, 9.5).translate((0, ro - 3.0, BODY_H - 4.75)))
    return b


def ring_place(shape, tilt):
    """Ring frame -> world: knuckle axis lands on (0, HINGE_Y, HINGE_Z); then tilt about it."""
    s = shape.translate((0, RING_CY, RING_TOP_Z - RING_H))
    if tilt:
        s = s.rotate((0, HINGE_Y, HINGE_Z), (1, HINGE_Y, HINGE_Z), tilt)
    return s


# ----------------------------------------------------------------- PCBs (KiCad STEP)
def kicad_step(board, z, flip=False):
    path = os.path.join(ELEC, board, f"eclipse-{board}.step")
    if not os.path.exists(path):
        return None
    s = cq.importers.importStep(path)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tilt", type=float, default=0.0, help="halo tilt about the hinge (deg, + = front up)")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    parts = {
        "base_shell": (base_shell(), "anodised aluminium, graphite"),
        "base_weight": (base_weight(), "steel, white powder coat (reflector)"),
        "base_band": (base_band(), "light-diffusing opal PMMA ring"),
        "base_plinth": (base_plinth(), "steel foot plate, black powder coat"),
        "base_foot": (base_foot(), "silicone/cork ring"),
        "touch_glass": (touch_glass(), "3 mm soda-lime glass, satin etch"),
        "touch_etch": (touch_etch(), "etch marks"),
        "stem": (stem(), "aluminium tube 12x2, brass PVD"),
        "hinge_yoke": (hinge_yoke(), "machined aluminium, graphite"),
        "hinge_knob": (hinge_knob(), "machined brass"),
        "halo_cap": (ring_place(_cap_local(), args.tilt), "machined aluminium cap + knuckle, graphite"),
        "halo_body": (ring_place(_body_local(), args.tilt), "solid light-diffusing PMMA, injection moulded"),
    }
    # electronics from KiCad (exported with --user-origin 150x150mm, so XY already match)
    core = kicad_step("core", 0)
    if core is not None:
        # core board: top face at PCB_TOP_Z; KiCad puts the board bottom at z=0 -> top at 1.6
        parts["pcb_core"] = (core.translate((0, 0, PCB_TOP_Z - 1.6)), "PCBA core")
    halo = kicad_step("halo", 0)
    if halo is not None:
        # halo board hangs upside-down under the ring skin (LEDs face the desk). Its hinge tab is
        # at KiCad -y (screen up) = +Y, matching the knuckle.  Flip about Y, then place.
        ro = RING_OD / 2
        h = halo.rotate((0, 0, 0), (0, 1, 0), 180)
        h = h.translate((0, RING_CY, RING_TOP_Z - CAP_T))
        if args.tilt:
            h = h.rotate((0, HINGE_Y, HINGE_Z), (1, HINGE_Y, HINGE_Z), args.tilt)
        parts["pcb_halo"] = (h, "PCBA halo")

    asm = cq.Assembly(name="eclipse_lamp")
    colors = {"base_shell": (0.18, 0.18, 0.19), "base_weight": (0.6, 0.6, 0.62), "bottom_cover": (0.3, 0.3, 0.3),
              "base_foot": (0.55, 0.42, 0.3), "base_band": (0.97, 0.95, 0.9), "base_plinth": (0.18, 0.18, 0.19), "touch_glass": (0.1, 0.1, 0.12), "touch_etch": (0.8, 0.8, 0.8),
              "stem": (0.78, 0.64, 0.42), "hinge_yoke": (0.18, 0.18, 0.19), "hinge_knob": (0.78, 0.64, 0.42),
              "halo_cap": (0.18, 0.18, 0.19), "halo_body": (0.98, 0.97, 0.94),
              "pcb_core": (0.1, 0.3, 0.15), "pcb_halo": (0.95, 0.95, 0.95)}
    meta = {}
    for name, (shape, mat) in parts.items():
        cq.exporters.export(shape, os.path.join(args.out, name + ".stl"), tolerance=0.02, angularTolerance=0.08)
        if not name.startswith("pcb_"):
            cq.exporters.export(shape, os.path.join(args.out, name + ".step"))
        asm.add(shape, name=name, color=cq.Color(*colors.get(name, (0.5, 0.5, 0.5))))
        bb = shape.val().BoundingBox() if hasattr(shape, "val") else shape.BoundingBox()
        meta[name] = {"material": mat, "bbox": [bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax]}
        print(f"{name:14s} {bb.xlen:7.1f} x {bb.ylen:7.1f} x {bb.zlen:7.1f}  {mat}")
    asm.save(os.path.join(args.out, "eclipse_lamp_assembly.step"))
    json.dump({"tilt": args.tilt, "hinge": [0, HINGE_Y, HINGE_Z], "ring_center": [0, RING_CY, RING_TOP_Z - RING_H],
               "touch": list(TOUCH_XY), "pcb_halo_z": RING_TOP_Z - CAP_T, "pcb_core_z": PCB_TOP_Z - 1.6,
               "parts": meta}, open(os.path.join(args.out, "parts.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
