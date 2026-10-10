"""ECLIPSE Tree - LED SPRIG flex (x40 per lamp).

A cedar-elm spray on 2-layer polyimide: main stem + 3 side shoots, 20 leaves; each leaf
is one 0402 LED.  All 20 LEDs in parallel between the root pads (A, K).  In the lamp each
sprig is one series element of a 10-sprig chain driven at 100 mA -> ~5 mA per leaf.
Warm (2700 K) and cool (6500 K) sprigs are the same board with different LEDs.
"""
from schgen import Part, Schematic
from sprig_layout import N_LEAVES


def g(n):
    return round(round(n / 1.27) * 1.27, 3)


def build():
    s = Schematic("eclipse-sprig", "ECLIPSE Tree - LED sprig flex (20 leaves)", "A", paper="A3",
                  comments=(f"{N_LEAVES} x 0402 LED in parallel, ~5 mA each (100 mA per sprig)",
                            "Board: 2-layer polyimide flex 0.11 mm, 1/2 oz, bronze coverlay, ENIG",
                            "Build 20 with 2700 K LEDs and 20 with 6500 K LEDs per lamp"))
    s.box(g(15), g(25), g(400), g(160), "LEAVES (all in parallel)")
    s.add(Part("J1", "Connector_Generic:Conn_01x02", "ROOT", "eclipse:SprigRoot", (g(30), g(92)),
               {"1": "SPRIG_A", "2": "SPRIG_K"}, rot=180,
               fields={"Manufacturer": "-", "MPN": "PCB land", "Description": "Root pads: 1 = anode, 2 = cathode"},
               in_bom=False))
    for k in range(N_LEAVES):
        row, col = divmod(k, 10)
        x = 70 + col * 30
        y = 60 + row * 60
        s.add(Part(f"D{k + 1}", "Device:LED", "LEAF", "LED_SMD:LED_0402_1005Metric", (g(x), g(y)),
                   {"2": "SPRIG_A", "1": "SPRIG_K"}, rot=90,
                   fields={"Manufacturer": "Inolux / Lite-On (select bin)", "MPN": "0402 white LED, 2700K or 6500K",
                           "Description": "Leaf: 0402 white LED, If 5 mA"}))
    s.text("Same Vf bin on one sprig: the 20 LEDs share 100 mA without ballast resistors", g(20), g(155), 1.5)
    return s


if __name__ == "__main__":
    import sys
    build().write(sys.argv[1])
