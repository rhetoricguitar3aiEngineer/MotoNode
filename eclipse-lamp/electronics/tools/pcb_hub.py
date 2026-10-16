"""Generate the HUB light-engine PCB (D56, lives in the trunk fork): parametric placement + routing.

Each channel owns 10 consecutive slots.  Inner (K) pad of sprig k -> outer (A) pad of
sprig k+1 is a short diagonal.  The channel's feed comes up from its trunk land, runs an
anode arc (r 8.6) to the 4-LED light-engine group in the middle of its sector (2 LEDs top,
2 bottom, vias between), and the group's cathode arc (r 17.5) returns to the gap slot and out
to the first sprig.  The cathode return of the chain runs inward from the last slot.
Nothing crosses.
"""
import math, os
import pcbnew
from pcbutil import V, populate, place, track, arc_track, edge_circle, text, add_stackup, patch_models, write_project
import hub_layout as H
from design_hub import sprig_ref

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "..", "hub")
PCB = os.path.join(PROJ, "eclipse-hub.kicad_pcb")
C = (150.0, 150.0)
W = 0.25


def pol(r, a):
    return H.polar(r, a, C)


def via(board, net, x, y, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y))
    v.SetWidth(pcbnew.FromMM(d))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net)
    board.Add(v)


def main():
    board = pcbnew.NewBoard(PCB)
    fps, nets = populate(board, os.path.join(PROJ, "eclipse-hub.net"), PROJ)
    edge_circle(board, C, H.R_BOARD)
    edge_circle(board, C, H.R_HOLE)
    place(fps["J1"], *C, 0)
    fps["J1"].Reference().SetVisible(False)
    fps["J1"].Value().SetVisible(False)
    rm = (H.R_OUT + H.R_IN) / 2

    def padpos(ref, num):
        p = fps[ref].FindPadByNumber(num).GetPosition()
        return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)

    for ch in H.CHANNEL_ORDER:
        for k in range(10):
            ref = sprig_ref(ch, k)
            a = H.slot_angle(H.sprig_slot(ch, k))
            place(fps[ref], *pol(rm, a), -a)
            fps[ref].Reference().SetVisible(False)
            fps[ref].Value().SetVisible(False)
    for ch in H.CHANNEL_ORDER:
        n = H.CHANNEL_ORDER.index(ch)
        for k in range(9):
            r0, r1 = sprig_ref(ch, k), sprig_ref(ch, k + 1)
            net = fps[r0].FindPadByNumber("2").GetNet()
            track(board, net, [padpos(r0, "2"), padpos(r1, "1")], W)
        # light engine: trunk land -> anode arc -> 4 LEDs (2 top, 2 bottom) -> cathode arc -> first sprig
        first = sprig_ref(ch, 0)
        ag = H.slot_angle(11 * n)
        mid = H.sector_mid(ch)
        pin_a = [p for p, nn in H.J1_PIN_NET.items() if nn == f"{ch}_A"][0]
        pin_k = [p for p, nn in H.J1_PIN_NET.items() if nn == f"{ch}_K"][0]
        leds = [f"D{4 * n + j + 1}" for j in range(4)]
        net_a = fps[leds[0]].FindPadByNumber("2").GetNet()
        net_g = fps[leds[0]].FindPadByNumber("1").GetNet()
        for j, ref in enumerate(leds):
            a = mid + (-H.LED_DANG if j % 2 == 0 else H.LED_DANG)
            rot = math.degrees(math.atan2(-math.cos(math.radians(a)), -math.sin(math.radians(a))))
            place(fps[ref], *pol(H.LED_R, a), rot, back=(j >= 2))
            # anode pad must face the centre (works for both the top and the mirrored bottom part)
            def rad(num):
                x, y = padpos(ref, num)
                return math.hypot(x - C[0], y - C[1])
            if rad("2") > rad("1"):
                place(fps[ref], *pol(H.LED_R, a), rot + 180, back=(j >= 2))
            fps[ref].Reference().SetVisible(False)
            fps[ref].Value().SetVisible(False)
            layer = pcbnew.B_Cu if j >= 2 else pcbnew.F_Cu
            va, vk = pol(H.VIA_A_R, a), pol(H.VIA_K_R, a)
            track(board, net_a, [va, padpos(ref, "2")], W, layer)
            track(board, net_g, [padpos(ref, "1"), vk], W, layer)
            if j < 2:   # vias + stubs to the arcs once per angle (top side)
                via(board, net_a, *va)
                via(board, net_g, *vk)
                track(board, net_a, [pol(H.ARC_A_R, a), va], W)
                track(board, net_g, [vk, pol(H.ARC_K_R, a)], W)
        a_lo, a_hi = mid - H.LED_DANG, mid + H.LED_DANG
        track(board, net_a, [padpos("J1", str(pin_a)), pol(H.ARC_A_R, ag)], W)
        arc_track(board, net_a, C, H.ARC_A_R, ag, a_hi, W, pol)
        arc_track(board, net_g, C, H.ARC_K_R, ag, a_hi, W, pol)
        track(board, net_g, [pol(H.ARC_K_R, ag), pol(H.R_OUT, ag), padpos(first, "1")], W)
        last = sprig_ref(ch, 9)
        net = fps[last].FindPadByNumber("2").GetNet()
        track(board, net, [padpos(last, "2"), padpos("J1", str(pin_k))], W)
    # crown NTC between its two trunk lands
    place(fps["TH1"], *pol(H.NTC_R, H.NTC_ANG), -H.NTC_ANG)  # tangential
    pin_n = [p for p, nn in H.J1_PIN_NET.items() if nn == "NTC"][0]
    pin_g = [p for p, nn in H.J1_PIN_NET.items() if nn == "GND"][0]
    for tp, jp in (("1", pin_n), ("2", pin_g)):
        net = fps["TH1"].FindPadByNumber(tp).GetNet()
        track(board, net, [padpos("TH1", tp), padpos("J1", str(jp))], W)
    fps["TH1"].Reference().SetVisible(False)
    # silk: channel names in the free band
    for ch in H.CHANNEL_ORDER:
        n = H.CHANNEL_ORDER.index(ch)
        a = H.slot_angle(11 * n + 2.5)
        text(board, ch, *pol(9.6, a), 0.8, rot=-a)
    board.GetDesignSettings().SetCopperLayerCount(2)
    board.Save(PCB)
    patch_models(PCB)
    add_stackup(PCB, mask="White", silk="Black", thickness=1.0)   # white mask: reflector in the trunk fork
    write_project(os.path.join(PROJ, "eclipse-hub.kicad_pro"),
                  [{"name": "Default", "track": W, "clearance": 0.15}],
                  rules={"min_clearance": 0.15, "min_copper_edge_clearance": 0.3})
    print("written", PCB)


if __name__ == "__main__":
    main()
