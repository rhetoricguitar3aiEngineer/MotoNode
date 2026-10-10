"""Generate the HUB PCB (D36, lives in the burl): parametric placement + single-layer routing.

Each channel owns 10 consecutive slots.  Inner (K) pad of sprig k -> outer (A) pad of
sprig k+1 is a short diagonal; the channel's anode feed runs inward through the channel's
empty gap slot, its cathode return inward from the last slot.  Nothing crosses.
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
        # anode feed: first outer pad -> gap slot -> inward to the trunk land
        first = sprig_ref(ch, 0)
        ag = H.slot_angle(11 * n)
        pin_a = [p for p, nn in H.J1_PIN_NET.items() if nn == f"{ch}_A"][0]
        pin_k = [p for p, nn in H.J1_PIN_NET.items() if nn == f"{ch}_K"][0]
        net = fps[first].FindPadByNumber("1").GetNet()
        track(board, net, [padpos(first, "1"), pol(H.R_OUT, ag), padpos("J1", str(pin_a))], W)
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
    add_stackup(PCB, mask="Black", silk="White", thickness=1.0)
    write_project(os.path.join(PROJ, "eclipse-hub.kicad_pro"),
                  [{"name": "Default", "track": W, "clearance": 0.15}],
                  rules={"min_clearance": 0.15, "min_copper_edge_clearance": 0.3})
    print("written", PCB)


if __name__ == "__main__":
    main()
