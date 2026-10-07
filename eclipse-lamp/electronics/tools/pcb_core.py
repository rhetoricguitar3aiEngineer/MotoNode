"""Generate the CORE board (base): outline, placement, zones; routing by Freerouting.

usage: python3 pcb_core.py place      -> writes eclipse-core.kicad_pcb + .dsn
       python3 pcb_core.py finish     -> imports .ses, adds GND pours, fills, saves
"""
import math, os, sys
import pcbnew
from pcbutil import add_stackup, patch_models, V, populate, place, edge_arc, edge_line, text, write_project

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "..", "core")
PCB = os.path.join(PROJ, "eclipse-core.kicad_pcb")
CX, CY = 150.0, 150.0
R_BOARD = 62.0
STEM = (0.0, -58.0)      # stem axis, relative to board centre (screen up = rear of lamp)
R_NOTCH = 11.0
USB_PHI = 90.0           # USB-C direction, degrees clockwise from rear (right-hand side)
R_MOUTH = 74.0           # radius of the receptacle mouth (base outer radius = 75)
TAB_HW = 7.5
TOUCH = (0.0, 30.0)      # centre of the touch wheel (front of the base)


def P(x, y):
    return CX + x, CY + y


def polar(r, phi):
    t = math.radians(phi)
    return r * math.sin(t), -r * math.cos(t)


def usb_frame(u, v):
    t = math.radians(USB_PHI)
    d = (math.sin(t), -math.cos(t))
    tt = (math.cos(t), math.sin(t))
    return u * d[0] + v * tt[0], u * d[1] + v * tt[1]


def outline(board):
    # notch around the stem foot
    yN = (STEM[1] ** 2 - R_NOTCH ** 2 + R_BOARD ** 2) / (2 * STEM[1])
    xN = math.sqrt(R_BOARD ** 2 - yN ** 2)
    edge_arc(board, P(-xN, yN), P(0, STEM[1] + R_NOTCH), P(xN, yN))
    phiN = math.degrees(math.asin(xN / R_BOARD))
    # tab for the USB-C receptacle
    u0 = math.sqrt(R_BOARD ** 2 - TAB_HW ** 2)
    dphi = math.degrees(math.asin(TAB_HW / R_BOARD))
    u1 = R_MOUTH - 0.8
    a_start, a_end = USB_PHI - dphi, USB_PHI + dphi
    edge_arc(board, P(xN, yN), P(*polar(R_BOARD, (phiN + a_start) / 2)), P(*polar(R_BOARD, a_start)))
    c = [usb_frame(u0, -TAB_HW), usb_frame(u1, -TAB_HW), usb_frame(u1, TAB_HW), usb_frame(u0, TAB_HW)]
    for a, b in zip(c, c[1:]):
        edge_line(board, P(*a), P(*b))
    edge_arc(board, P(*polar(R_BOARD, a_end)), P(*polar(R_BOARD, (a_end + 360 - phiN) / 2)), P(-xN, yN))


# boost cell: (ref prefix, dx, dy, rot)
CELL = [("U", 0, 0, 0), ("L", -6.8, -0.5, 0), ("D", 0.5, -5.6, 180), ("Cout", 6.6, -4.2, 90),
        ("Cin", -6.8, 4.6, 0), ("Ccomp", -2.0, 3.6, 0), ("Rfb", 3.4, 3.6, 0)]
BOOSTS = [  # channel index n -> cell origin
    (-41.0, 16.0), (-40.0, -14.0), (36.0, 30.0), (36.0, -30.0)]


def placement(fps):
    # single-sided assembly on the BOTTOM: the top face sits directly under the
    # 3 mm touch glass, so only the electrodes and the glow LED live on top.
    top = {"E1", "E2", "E3", "E4", "D2"}

    def pl(ref, x, y, rot=0):
        place(fps[ref], *P(x, y), rot, back=ref not in top)

    # USB-C on the tab, mouth facing outward
    ox, oy = usb_frame(R_MOUTH - 3.65, 0)
    pl("J1", ox, oy, -USB_PHI)  # bottom-side: mirrored, so mouth faces outward at -phi
    # PD trigger + protection cluster, rotated with the tab
    def uf(u, v, ref, rot=0):
        x, y = usb_frame(u, v)
        pl(ref, x, y, (rot - USB_PHI) % 360)
    uf(58.0, -2.0, "R1", 90)
    uf(58.0, 2.5, "C3", 90)
    uf(52.0, 0.0, "U1", 0)
    uf(45.5, -3.5, "R2", 0)
    uf(45.5, 3.5, "R3", 0)
    uf(57.5, -8.5, "F1", 90)
    uf(50.0, -12.5, "D1", 90)
    uf(43.5, -12.0, "C1", 90)
    uf(52.0, 10.0, "C2", 90)
    # LDO + MCU
    pl("U2", -16.0, -31.0, 0)
    pl("C4", -25.0, -31.0, 90)
    pl("C5", -7.0, -31.0, 90)
    pl("U3", 0.0, -14.0, 0)
    pl("C6", -8.5, -20.0, 90)
    pl("C7", -8.5, -16.0, 90)
    pl("J3", 14.0, -26.0, 90)
    pl("R4", 9.0, -8.5, 0)
    pl("R5", 9.0, -6.5, 0)
    pl("C8", 9.0, -4.5, 0)
    pl("R6", -9.0, -7.0, 0)
    pl("C9", -9.0, -5.0, 0)
    pl("R12", 9.0, -18.0, 0)
    pl("R13", 9.0, -16.0, 0)
    # touch electrodes + series resistors
    pl("E1", *TOUCH, 0)
    for k, ref in enumerate(("E2", "E3", "E4")):
        pl(ref, *TOUCH, -k * 120)
    pl("R7", -1.5, 0.5, 90)
    pl("R8", 1.5, 0.5, 90)
    pl("R9", 21.0, 15.0, 30)
    pl("R10", -21.0, 15.0, -30)
    # status glow LED at the front rim of the touch window
    pl("D2", 0.0, 55.0, 0)
    pl("R11", 0.0, 58.5, 0)
    # LED drivers
    pre = {"U": 4, "L": 1, "D": 3, "Cout": 14, "Cin": 10, "Ccomp": 18, "Rfb": 14}
    for n, (bx, by) in enumerate(BOOSTS):
        for kind, dx, dy, rot in CELL:
            ref = {"U": "U", "L": "L", "D": "D", "Cout": "C", "Cin": "C", "Ccomp": "C", "Rfb": "R"}[kind] + \
                str(pre[kind] + n)
            pl(ref, bx + dx, by + dy, rot)
    # halo harness next to the stem foot, mating face toward the rear wall
    pl("J2", -25.0, -44.0, 180)
    # mounting holes
    for ref, phi in (("H1", 150), ("H2", 220), ("H3", 312)):
        pl(ref, *polar(55.0, phi))


def zone(board, net, layer, pts, priority=0, keepout=False):
    z = pcbnew.ZONE(board)
    ls = pcbnew.LSET()
    ls.AddLayer(layer)
    z.SetLayerSet(ls)
    poly = z.Outline()
    poly.NewOutline()
    for x, y in pts:
        poly.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    if keepout:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
    else:
        z.SetNet(net)
        z.SetAssignedPriority(priority)
        z.SetMinThickness(pcbnew.FromMM(0.25))
        z.SetLocalClearance(pcbnew.FromMM(0.3))
        z.SetThermalReliefGap(pcbnew.FromMM(0.3))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)  # reflow-assembled board
    board.Add(z)
    return z


def circle_pts(c, r, n=72):
    return [P(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def silk(board):
    text(board, "ECLIPSE  CORE  rev A", *P(0, -52), 1.6, bold=True)
    text(board, "USB-C PD 9V  |  4x TPS61165  |  ATtiny1616", *P(0, 49.5), 1.0, layer=pcbnew.B_SilkS, mirror=True)
    B = dict(layer=pcbnew.B_SilkS, mirror=True)
    text(board, "TO HALO", *P(-25, -40.5), 1.0, **B)
    text(board, "UPDI", *P(14, -30.5), 0.9, **B)
    for n, (bx, by) in enumerate(BOOSTS):
        text(board, ["W1", "C1", "W2", "C2"][n], *P(bx, by + 8.4), 1.0, **B)


def do_place():
    board = pcbnew.NewBoard(PCB)
    fps, nets = populate(board, os.path.join(PROJ, "eclipse-core.net"), PROJ)
    outline(board)
    placement(fps)
    fps["J3"].SetDNP(True)  # UPDI header: pogo-pin pads only
    for fp in fps.values():
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(V(0.8, 0.8))
        fp.Reference().SetTextThickness(pcbnew.FromMM(0.12))
    for ref in ("E1", "E2", "E3", "E4", "H1", "H2", "H3"):
        fps[ref].Reference().SetVisible(False)
    silk(board)
    board.GetDesignSettings().SetCopperLayerCount(2)
    board.Save(PCB)
    add_stackup(PCB, mask="Black", silk="White")
    # net classes by function (schematic nets are wired, so most carry KiCad auto names)
    power, led = ["VIN", "VBUS", "GND"], []
    for net in nets:
        pads = [(fp.GetReference(), p.GetNumber()) for fp in fps.values() for p in fp.Pads()
                if p.GetNetname() == net]
        if any(r in ("U4", "U5", "U6", "U7") and n == "3" for r, n in pads):
            power.append(net)
        elif any(r == "J2" and n in ("1", "2", "3", "4", "7", "8", "9", "10") for r, n in pads):
            led.append(net)
    write_project(os.path.join(PROJ, "eclipse-core.kicad_pro"),
                  [{"name": "Default", "track": 0.25, "clearance": 0.19},
                   {"name": "Power", "track": 0.5, "clearance": 0.21, "via": 0.8, "drill": 0.4, "nets": power},
                   {"name": "LED", "track": 0.35, "clearance": 0.21, "nets": led}],
                  rules={"min_clearance": 0.15})
    # reload so the project net classes apply, then export DSN for Freerouting
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ExportSpecctraDSN(board, os.path.join(PROJ, "eclipse-core.dsn"))
    print("placed; DSN written")


def do_finish():
    board = pcbnew.LoadBoard(PCB)
    # NOTE: run on a freshly placed board (route_core.sh does place -> route -> finish)
    ses = os.path.join(PROJ, "eclipse-core.ses")
    if os.path.exists(ses):
        pcbnew.ImportSpecctraSES(board, ses)
    gnd = board.FindNet("GND")
    big = circle_pts((0, 0), 80)
    zone(board, gnd, pcbnew.B_Cu, big, 0)
    zone(board, gnd, pcbnew.F_Cu, big, 0)
    # no pour around/under the touch electrodes (keeps their parasitic capacitance low)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = zone(board, None, layer, circle_pts(TOUCH, 25.5), keepout=True)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(PCB)
    patch_models(PCB)
    print("finished")


if __name__ == "__main__":
    {"place": do_place, "finish": do_finish}[sys.argv[1]]()
