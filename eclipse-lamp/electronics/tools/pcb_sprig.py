"""Generate the LED SPRIG flex PCB (2-layer polyimide), fully parametric.

Top copper (F.Cu) = anode bus along every stem and petiole to each LED's inner pad.
Bottom copper (B.Cu) = cathode bus along the same paths, up through a via just beyond
each LED's outer pad.  The board outline is grown around the copper (the flex *is* the
twig), so the sprig is only ~1 mm wide.
"""
import math, os
import pcbnew
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from shapely import affinity
from pcbutil import V, populate, place, track, edge_line, add_stackup, patch_models, write_project
from sprig_layout import layout

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "..", "sprig")
PCB = os.path.join(PROJ, "eclipse-sprig.kicad_pcb")
C = (100.0, 100.0)
W = 0.15              # trace width
VIA_D, VIA_DRILL = 0.45, 0.2
VIA_OFF = 0.65        # via centre beyond the LED's outer (cathode) pad centre
STEM_HALF = 0.5       # flex half-width along stems
PET_HALF = 0.42


def P(p):
    return (C[0] + p[0], C[1] - p[1])        # layout y-up -> KiCad y-down


def via(board, net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y))
    v.SetWidth(pcbnew.FromMM(VIA_D))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net)
    board.Add(v)


def main():
    L = layout()
    board = pcbnew.NewBoard(PCB)
    fps, nets = populate(board, os.path.join(PROJ, "eclipse-sprig.net"), PROJ)
    netA = fps["J1"].FindPadByNumber("1").GetNet()
    netK = fps["J1"].FindPadByNumber("2").GetNet()
    place(fps["J1"], *P((0.0, 0.0)), 0)
    shapes = []

    # stems: anode on top, cathode on bottom, stacked
    for st in L["stems"]:
        pts = [P(p) for p in st]
        track(board, netA, pts, W, pcbnew.F_Cu)
        track(board, netK, pts, W, pcbnew.B_Cu)
        shapes.append(LineString(pts).buffer(STEM_HALF, quad_segs=6))

    # leaves
    for i, lf in enumerate(L["leaves"]):
        b, p = P(lf["base"]), P(lf["pos"])
        ux, uy = p[0] - b[0], p[1] - b[1]
        n = math.hypot(ux, uy)
        ux, uy = ux / n, uy / n
        # LED local +x (pad 2 = anode) points back toward the stem
        rot = math.degrees(math.atan2(uy, -ux))
        fp = fps[f"D{i + 1}"]
        place(fp, p[0], p[1], rot)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        pa = fp.FindPadByNumber("2").GetPosition()
        pk = fp.FindPadByNumber("1").GetPosition()
        pa = (pcbnew.ToMM(pa.x), pcbnew.ToMM(pa.y))
        pk = (pcbnew.ToMM(pk.x), pcbnew.ToMM(pk.y))
        vpos = (pk[0] + ux * VIA_OFF, pk[1] + uy * VIA_OFF)
        track(board, netA, [b, pa], W, pcbnew.F_Cu)
        track(board, netK, [b, vpos], W, pcbnew.B_Cu)
        track(board, netK, [vpos, pk], W, pcbnew.F_Cu)
        via(board, netK, *vpos)
        shapes.append(LineString([b, (vpos[0] + ux * 0.1, vpos[1] + uy * 0.1)]).buffer(PET_HALF, quad_segs=6))
        led = affinity.rotate(box(-0.8, -0.5, 0.8, 0.5), math.degrees(math.atan2(uy, ux)), origin=(0, 0))
        shapes.append(affinity.translate(led, p[0], p[1]).buffer(0.15, quad_segs=4))

    # root: pads A/K + via for K; a small tab for soldering to the twig wires
    r = fps["J1"]
    a1 = r.FindPadByNumber("1").GetPosition()
    k1 = r.FindPadByNumber("2").GetPosition()
    a1 = (pcbnew.ToMM(a1.x), pcbnew.ToMM(a1.y))
    k1 = (pcbnew.ToMM(k1.x), pcbnew.ToMM(k1.y))
    root = P((0.0, 0.0))
    kv = (root[0] - 0.25, k1[1] + 0.05)
    track(board, netA, [a1, root], W, pcbnew.F_Cu)
    track(board, netK, [k1, kv], W, pcbnew.F_Cu)
    via(board, netK, *kv)
    track(board, netK, [kv, root], W, pcbnew.B_Cu)
    shapes.append(box(root[0] - 2.05, root[1] - 1.5, root[0] + 0.6, root[1] + 1.5))

    outline = unary_union(shapes).simplify(0.01)
    if outline.geom_type != "Polygon":
        outline = max(outline.geoms, key=lambda g: g.area)
    for ring in [outline.exterior] + list(outline.interiors):
        cs = list(ring.coords)
        for q0, q1 in zip(cs, cs[1:]):
            edge_line(board, q0, q1, 0.05)

    board.GetDesignSettings().SetCopperLayerCount(2)
    board.Save(PCB)
    patch_models(PCB)
    add_stackup(PCB, mask="#5C3A1E", silk="White", cu=0.018, finish="ENIG", core="Polyimide", thickness=0.11)
    write_project(os.path.join(PROJ, "eclipse-sprig.kicad_pro"),
                  [{"name": "Default", "track": W, "clearance": 0.1, "via": VIA_D, "drill": VIA_DRILL}],
                  rules={"min_clearance": 0.1, "min_track_width": 0.1, "min_via_diameter": 0.4,
                         "min_through_hole_diameter": 0.2, "min_copper_edge_clearance": 0.12,
                         "min_hole_clearance": 0.12, "min_hole_to_hole": 0.25, "min_via_annular_width": 0.1})
    print("written", PCB, "area mm2 =", round(outline.area, 1))


if __name__ == "__main__":
    main()
