"""Generate the HALO ring PCB (placement + fully parametric single-layer routing).

All copper is on F.Cu so the board can be built either as 2-layer FR4 or as a
single-layer aluminium MCPCB (recommended).
"""
import math, os, sys
import pcbnew
from pcbutil import add_stackup, patch_models, V, populate, place, track, arc_track, edge_arc, edge_line, edge_circle, text, write_project
from design_halo import CHAINS, N_LED

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "..", "halo")
CX, CY = 150.0, 150.0
R_IN, R_OUT, R_LED = 80.0, 100.0, 90.0
R_WDET, R_WRET = 84.5, 82.0      # warm chain detour / return lane
R_CDET, R_CRET = 95.5, 98.0      # cool chain detour / return lane
W_TRK = 0.8
CONN_R = 102.0                   # connector origin radius (on the hinge tab)
TAB_W, TAB_R = 14.0, 107.6


def polar(r, a):
    """a in degrees, 0 = toward the hinge (screen up), positive = clockwise."""
    t = math.radians(a)
    return CX + r * math.sin(t), CY - r * math.cos(t)


def ang_of(x, y):
    return math.degrees(math.atan2(x - CX, -(y - CY))) % 360


def led_angle(i):
    return 360.0 / N_LED * i + 360.0 / N_LED / 2


def main():
    pcbfile = os.path.join(PROJ, "eclipse-halo.kicad_pcb")
    board = pcbnew.NewBoard(pcbfile)
    fps, nets = populate(board, os.path.join(PROJ, "eclipse-halo.net"), PROJ)

    # ---------------------------------------------------------------- outline
    xt = TAB_W
    yt = math.sqrt(R_OUT ** 2 - xt ** 2)
    edge_arc(board, (CX + xt, CY - yt), polar(R_OUT, 180), (CX - xt, CY - yt))
    edge_line(board, (CX - xt, CY - yt), (CX - xt, CY - TAB_R))
    edge_line(board, (CX - xt, CY - TAB_R), (CX + xt, CY - TAB_R))
    edge_line(board, (CX + xt, CY - TAB_R), (CX + xt, CY - yt))
    edge_circle(board, (CX, CY), R_IN)

    # ---------------------------------------------------------------- LEDs
    for i in range(N_LED):
        a = led_angle(i)
        half_a = i < N_LED // 2
        # local +x (anode pad) must point back toward the hinge along the chain
        tdir = a - 90 if half_a else a + 90          # polar direction of local +x
        ux, uy = math.sin(math.radians(tdir)), -math.cos(math.radians(tdir))
        rot = math.degrees(math.atan2(-uy, ux))
        fp = fps[f"D{i + 1}"]
        place(fp, *polar(R_LED, a), rot)
        # tidy silkscreen reference: just inside the LED towards the ring centre
        fp.Reference().SetPosition(V(*polar(R_LED - 3.2, a)))
        fp.Reference().SetTextSize(V(0.8, 0.8))
        fp.Reference().SetTextThickness(pcbnew.FromMM(0.12))
        fp.Reference().SetTextAngleDegrees((rot + 0) % 360)
        fp.Value().SetVisible(False)

    # connector on the hinge tab, mating face outward
    place(fps["J1"], *polar(CONN_R, 0), 180)
    # NTC between the two halves, pads tangential (pad1 -> +x)
    place(fps["TH1"], *polar(91.0, 0), 180)
    fps["TH1"].Reference().SetPosition(V(*polar(88.6, 0)))
    for k, a in enumerate((45, 135, 225, 315)):
        place(fps[f"H{k + 1}"], *polar(R_LED, a), 0)
        fps[f"H{k + 1}"].Reference().SetVisible(False)
        fps[f"H{k + 1}"].Value().SetVisible(False)
    fps["J1"].Value().SetVisible(False)

    def pad(ref, num):
        for p in fps[ref].Pads():
            if p.GetNumber() == num and p.GetSize().x > pcbnew.FromMM(0.55):
                pos = p.GetPosition()
                return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
        raise KeyError((ref, num))

    def pad_led(i, which):
        x, y = pad(f"D{i + 1}", "1" if which == "K" else "2")
        return x, y, ang_of(x, y)

    # ---------------------------------------------------------------- strings
    def link(net, p, q, rl):
        """pad p -> radial to lane rl -> arc -> radial -> pad q."""
        (x0, y0, a0), (x1, y1, a1) = p, q
        track(board, net, [(x0, y0), polar(rl, a0)], W_TRK)
        arc_track(board, net, (CX, CY), rl, a0, a1, W_TRK, polar)
        track(board, net, [polar(rl, a1), (x1, y1)], W_TRK)

    def J(pin):
        return pad("J1", str(pin))

    for st, chain in CHAINS.items():
        warm = st[0] == "W"
        rdet = R_WDET if warm else R_CDET
        rret = R_WRET if warm else R_CRET
        for a, b in zip(chain, chain[1:]):
            net = fps[f"D{a + 1}"].FindPadByNumber("1").GetNet()
            link(net, pad_led(a, "K"), pad_led(b, "A"), rdet)
        first, last = chain[0], chain[-1]
        anet = fps[f"D{first + 1}"].FindPadByNumber("2").GetNet()
        knet = fps[f"D{last + 1}"].FindPadByNumber("1").GetNet()
        # which connector pins (see design_halo J1 mapping)
        pins = {"C1": (2, 1), "W1": (3, 4), "W2": (8, 7), "C2": (9, 10)}[st]
        ja, jk = J(pins[0]), J(pins[1])
        pa, pk = pad_led(first, "A"), pad_led(last, "K")
        pad_in = CY - (CONN_R - 2.85 - 1.75) + 0.3     # inner end of connector pads (screen y)
        if warm:
            # feed: straight from connector pad to first anode
            track(board, anet, [ja, (ja[0], pad_in + 1.0), (pa[0], pa[1])], W_TRK)
            # return: last cathode -> inner return lane -> up into connector pad
            a_end = ang_of(jk[0], CY - math.sqrt(rret ** 2 - (jk[0] - CX) ** 2))
            track(board, knet, [(pk[0], pk[1]), polar(rret, pk[2])], W_TRK)
            arc_track(board, knet, (CX, CY), rret, pk[2], a_end, W_TRK, polar)
            track(board, knet, [polar(rret, a_end), (jk[0], jk[1])], W_TRK)
        else:
            # feed along the cool detour lane
            a_feed = ang_of(ja[0], CY - math.sqrt(rdet ** 2 - (ja[0] - CX) ** 2))
            track(board, anet, [ja, polar(rdet, a_feed)], W_TRK)
            a_target = pa[2]
            if a_target > 180 and a_feed < 180:
                a_feed += 360
            arc_track(board, anet, (CX, CY), rdet, a_feed, a_target, W_TRK, polar)
            track(board, anet, [polar(rdet, a_target), (pa[0], pa[1])], W_TRK)
            a_end = ang_of(jk[0], CY - math.sqrt(rret ** 2 - (jk[0] - CX) ** 2))
            if pk[2] > 180 and a_end < 180:
                a_end += 360
            track(board, knet, [(pk[0], pk[1]), polar(rret, pk[2])], W_TRK)
            arc_track(board, knet, (CX, CY), rret, pk[2], a_end, W_TRK, polar)
            track(board, knet, [polar(rret, a_end), (jk[0], jk[1])], W_TRK)

    # NTC -> connector pins 5 / 6
    for tp, jp in (("1", 5), ("2", 6)):
        x, y = pad("TH1", tp)
        jx, jy = J(jp)
        net = fps["TH1"].FindPadByNumber(tp).GetNet()
        track(board, net, [(x, y), (jx, y - 2.0), (jx, jy)], 0.4)

    # connector mounting tabs -> GND (pin 6) along the outer side of the pin row
    gnd = fps["TH1"].FindPadByNumber("2").GetNet()
    g6 = J(6)
    yb = CY - CONN_R - 0.2
    for p in fps["J1"].Pads():
        if p.GetNumber() == "MP":
            mx, my = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
            track(board, gnd, [(mx, my), (mx, yb), (g6[0], yb), g6], 0.4)

    # ---------------------------------------------------------------- silkscreen
    text(board, "ECLIPSE  HALO  rev A", *polar(86.85, 180), 1.4, bold=True, rot=0)
    text(board, "40x 3030  2700K/6500K  CRI90", *polar(86.85, 90), 1.1, rot=-90)
    text(board, "4 strings x 10  @ 100 mA", *polar(86.85, 270), 1.1, rot=90)
    text(board, "W1/C1 >", *polar(R_LED - 5, 30), 1.0, rot=-30)
    text(board, "< W2/C2", *polar(R_LED - 5, 330), 1.0, rot=30)
    text(board, "Al-MCPCB 1.5mm / 1oz / white", *polar(R_LED, 90), 1.0, layer=pcbnew.B_SilkS, rot=-90, mirror=True)

    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    board.Save(pcbfile)
    patch_models(pcbfile)
    add_stackup(pcbfile, mask="White", silk="Black", cu=0.07)
    write_project(os.path.join(PROJ, "eclipse-halo.kicad_pro"),
                  [{"name": "Default", "track": 0.8, "clearance": 0.25},
                   {"name": "Sense", "track": 0.4, "clearance": 0.2, "nets": ["NTC", "GND", "Net-(J1-Pin_5)"]}])
    print("written", pcbfile)


if __name__ == "__main__":
    main()
