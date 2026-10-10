"""ECLIPSE Tree - HUB board (hidden in the burl at the trunk fork).

Lands the 40 sprig wire pairs and chains each colour channel's 10 sprigs in series
(~29 V at 100 mA), so only the same 10-wire harness as before runs down the trunk to
core J2.  Carries the crown NTC.
"""
from schgen import Part, Schematic
import hub_layout as H


def g(n):
    return round(round(n / 1.27) * 1.27, 3)


CH_NAMES = {"W1": "2700 K", "C1": "6500 K", "W2": "2700 K", "C2": "6500 K"}


def sprig_ref(ch, k):
    return f"S{H.CHANNEL_ORDER.index(ch) * 10 + k + 1}"


def build():
    s = Schematic("eclipse-hub", "ECLIPSE Tree - Hub board (sprig chaining, in the burl)", "A", paper="A2",
                  comments=("40 sprig lands, 4 series chains of 10 sprigs (W1, C1, W2, C2), crown NTC",
                            "Board: D36 mm, 2 layers 1.0 mm FR4, 1 oz, black mask, ENIG; potted in the burl",
                            "J1 = 10 trunk-wire lands, pinout identical to core J2"))
    nets = {pin: net for pin, net in H.J1_PIN_NET.items()}
    jn = {}
    for pin, net in nets.items():
        jn[str(pin)] = "NTC_RET" if net == "GND" else net
    for row, ch in enumerate(H.CHANNEL_ORDER):
        y = 70 + row * 70
        s.box(g(15), g(y - 30), g(470), g(y + 30), f"CHAIN {ch}  ({CH_NAMES[ch]}, 10 sprigs in series, 100 mA)")
        for k in range(10):
            a = f"{ch}_A" if k == 0 else f"{ch}_L{k}"
            kk = f"{ch}_K" if k == 9 else f"{ch}_L{k + 1}"
            s.add(Part(sprig_ref(ch, k), "Connector_Generic:Conn_01x02", f"SPRIG {ch}.{k + 1:02d}",
                       "eclipse:HubSprigPads", (g(40 + k * 42), g(y)), {"1": a, "2": kk}, rot=180,
                       fields={"Manufacturer": "-", "MPN": "wire lands",
                               "Description": "Magnet-wire pair from one LED sprig (1 = A, 2 = K)"},
                       in_bom=False))
    s.box(g(480), g(40), g(570), g(330), "TRUNK HARNESS + CROWN NTC")
    s.add(Part("J1", "Connector_Generic:Conn_01x10", "TO CORE J2", "eclipse:HubTrunkPads", (g(530), g(170)),
               jn, fields={"Manufacturer": "-", "MPN": "wire lands",
                           "Description": "10 x AWG30 PTFE down the trunk to core J2 (1:1)"}, in_bom=False))
    s.add(Part("TH1", "Device:Thermistor_NTC", "10k B3380", "Resistor_SMD:R_0603_1608Metric", (g(500), g(240)),
               {"1": "NTC", "2": "NTC_RET"},
               fields={"Manufacturer": "Murata", "MPN": "NCP18XH103F03RB", "Description": "NTC 10k 1% B=3380, 0603"}))
    return s


if __name__ == "__main__":
    import sys
    build().write(sys.argv[1])
