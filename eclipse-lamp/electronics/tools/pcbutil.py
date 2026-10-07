"""Shared helpers for building KiCad boards with the pcbnew Python API."""
import json, math, os
import pcbnew
from kisexpr import parse, find, find1

FPDIR = "/usr/share/kicad/footprints"


def V(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def read_netlist(path):
    """Parse a kicadsexpr netlist -> (components, nets).

    components: {ref: dict(value, footprint, uuid)}
    nets: {name: [(ref, pin)]}
    """
    t = parse(open(path).read())
    comps = {}
    for c in find(find1(t, "components"), "comp"):
        ref = str(find1(c, "ref")[1])
        ts = find1(c, "tstamps")
        comps[ref] = dict(value=str(find1(c, "value")[1]),
                          footprint=str(find1(c, "footprint")[1]) if find1(c, "footprint") else "",
                          uuid=str(ts[1]) if ts else "")
    nets = {}
    for n in find(find1(t, "nets"), "net"):
        name = str(find1(n, "name")[1])
        nets[name] = [(str(find1(nd, "ref")[1]), str(find1(nd, "pin")[1])) for nd in find(n, "node")]
    return comps, nets


def load_fp(fpid, project_dir):
    lib, name = fpid.split(":")
    if lib == "eclipse":
        libpath = os.path.join(project_dir, "..", "lib", "eclipse.pretty")
    else:
        libpath = os.path.join(FPDIR, lib + ".pretty")
    fp = pcbnew.FootprintLoad(libpath, name)
    if fp is None:
        raise RuntimeError("footprint not found " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def populate(board, netfile, project_dir):
    comps, nets = read_netlist(netfile)
    netobj = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netobj[name] = ni
    pinnet = {}
    for name, nodes in nets.items():
        for ref, pin in nodes:
            pinnet[(ref, pin)] = name
    fps = {}
    for ref, c in comps.items():
        if not c["footprint"]:
            continue
        fp = load_fp(c["footprint"], project_dir)
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        if c["uuid"]:
            fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        for pad in fp.Pads():
            n = pinnet.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netobj[n])
        board.Add(fp)
        fps[ref] = fp
    return fps, netobj


def place(fp, x, y, rot=0, back=False):
    fp.SetPosition(V(x, y))
    if back and not fp.IsFlipped():
        fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)


def track(board, net, pts, w, layer=pcbnew.F_Cu):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(x0, y0))
        t.SetEnd(V(x1, y1))
        t.SetWidth(pcbnew.FromMM(w))
        t.SetLayer(layer)
        t.SetNet(net)
        board.Add(t)


def arc_track(board, net, c, r, a0, a1, w, polar, layer=pcbnew.F_Cu):
    """Arc of radius r from polar angle a0 to a1 (degrees) using polar(r, a)->(x,y)."""
    if abs(a1 - a0) < 1e-6:
        return
    # split long arcs to keep things robust
    nseg = max(1, int(abs(a1 - a0) // 90) + 1)
    for k in range(nseg):
        s = a0 + (a1 - a0) * k / nseg
        e = a0 + (a1 - a0) * (k + 1) / nseg
        m = (s + e) / 2
        a = pcbnew.PCB_ARC(board)
        a.SetStart(V(*polar(r, s)))
        a.SetMid(V(*polar(r, m)))
        a.SetEnd(V(*polar(r, e)))
        a.SetWidth(pcbnew.FromMM(w))
        a.SetLayer(layer)
        a.SetNet(net)
        board.Add(a)


def edge_line(board, p0, p1, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*p0))
    s.SetEnd(V(*p1))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(pcbnew.FromMM(w))
    board.Add(s)


def edge_arc(board, p0, pm, p1, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(V(*p0), V(*pm), V(*p1))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(pcbnew.FromMM(w))
    board.Add(s)


def edge_circle(board, c, r, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(V(*c))
    s.SetEnd(V(c[0] + r, c[1]))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(pcbnew.FromMM(w))
    board.Add(s)


def text(board, s, x, y, size=1.5, layer=pcbnew.F_SilkS, rot=0, bold=False, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(V(x, y))
    t.SetLayer(layer)
    t.SetTextSize(V(size, size))
    t.SetTextThickness(pcbnew.FromMM(size * (0.2 if bold else 0.15)))
    t.SetTextAngleDegrees(rot)
    if mirror:
        t.SetMirrored(True)
    board.Add(t)


def write_project(path, netclasses, rules=None):
    """Write a .kicad_pro with net classes + design rules."""
    classes = []
    for nc in netclasses:
        d = {"name": nc["name"], "clearance": nc.get("clearance", 0.2), "track_width": nc.get("track", 0.25),
             "via_diameter": nc.get("via", 0.6), "via_drill": nc.get("drill", 0.3),
             "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
             "microvia_diameter": 0.3, "microvia_drill": 0.1, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
             "schematic_color": "rgba(0, 0, 0, 0.000)", "wire_width": 6, "bus_width": 12, "priority": nc.get("priority", 0)}
        classes.append(d)
    patterns = []
    for nc in netclasses:
        for p in nc.get("nets", []):
            patterns.append({"netclass": nc["name"], "pattern": p})
    r = {"min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3,
         "min_copper_edge_clearance": 0.4, "min_hole_to_hole": 0.25, "min_hole_clearance": 0.25,
         "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.08, "solder_mask_to_copper_clearance": 0.0}
    if rules:
        r.update(rules)
    pro = {
        "board": {"design_settings": {"defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2,
                                                   "silk_line_width": 0.15, "silk_text_size_h": 1.0,
                                                   "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
                                      "rules": r,
                                      "rule_severities": {"silk_overlap": "ignore", "silk_over_copper": "ignore",
                                                          "silk_edge_clearance": "ignore", "lib_footprint_mismatch": "ignore",
                                                          "lib_footprint_issues": "ignore", "text_height": "ignore",
                                                          "courtyards_overlap": "warning"},
                                      "track_widths": [0.0, 0.25, 0.4, 0.6, 0.8, 1.0],
                                      "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3},
                                                         {"diameter": 0.8, "drill": 0.4}]}},
        "meta": {"filename": os.path.basename(path), "version": 3},
        "net_settings": {"classes": classes, "meta": {"version": 4}, "netclass_patterns": patterns},
        "pcbnew": {"page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [], "text_variables": {},
    }
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)


MODEL_SUBST = {
    "${KICAD9_3DMODEL_DIR}/LED_SMD.3dshapes/LED_Luminus_MP-3030-1100_3.0x3.0mm.step":
        "${KIPRJMOD}/../lib/eclipse.3dshapes/LED_3030.step",
    "${KICAD9_3DMODEL_DIR}/Connector_JST.3dshapes/JST_PH_S10B-PH-SM4-TB_1x10-1MP_P2.00mm_Horizontal.step":
        "${KIPRJMOD}/../lib/eclipse.3dshapes/JST_PH_S10B-PH-SM4-TB.step",
    "${KICAD9_3DMODEL_DIR}/Connector_USB.3dshapes/USB_C_Receptacle_HRO_TYPE-C-31-M-12.step":
        "${KIPRJMOD}/../lib/eclipse.3dshapes/USB_C_HRO_TYPE-C-31-M-12.step",
    "${KICAD9_3DMODEL_DIR}/Fuse.3dshapes/Fuse_1812_4532Metric.step":
        "${KIPRJMOD}/../lib/eclipse.3dshapes/Fuse_1812.step",
}


def patch_models(pcbfile):
    """KiCad ships no 3D models for two footprints used here: point them at project models."""
    src = open(pcbfile).read()
    for a, b in MODEL_SUBST.items():
        src = src.replace(a, b)
    open(pcbfile, "w").write(src)


def add_stackup(pcbfile, mask="Black", silk="White", cu=0.035, finish="ENIG", core="FR4"):
    """Insert a 2-layer stackup (with solder-mask / silk colours) into the board file."""
    src = open(pcbfile).read()
    if "(stackup" in src:
        return
    st = f'''(stackup
			(layer "F.SilkS" (type "Top Silk Screen") (color "{silk}"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (color "{mask}") (thickness 0.01))
			(layer "F.Cu" (type "copper") (thickness {cu}))
			(layer "dielectric 1" (type "core") (thickness {1.6 - 2 * cu - 0.02:.3f}) (material "{core}") (epsilon_r 4.5) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness {cu}))
			(layer "B.Mask" (type "Bottom Solder Mask") (color "{mask}") (thickness 0.01))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen") (color "{silk}"))
			(copper_finish "{finish}")
			(dielectric_constraints no)
		)
		'''
    src = src.replace("(setup\n\t\t", "(setup\n\t\t" + st, 1)
    open(pcbfile, "w").write(src)
