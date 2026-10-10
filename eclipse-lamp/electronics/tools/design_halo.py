"""ECLIPSE lamp - HALO ring board (inside the floating ring head).

40x Luminus MP-3030-1100 mid-power LEDs on an annular board (OD 200 / ID 160),
alternating 2700 K / 6500 K (mirror-symmetric about the hinge axis).  Four series strings of ten LEDs:
  W1 / C1 on the "left" half of the ring, W2 / C2 on the "right" half,
each driven by its own TPS61165 constant-current boost on the core board.
A 10 k NTC near the hinge reports head temperature.
"""
from schgen import Part, Schematic

N_LED = 40


def led_color(i):
    """Mirror-symmetric pattern: the two LEDs next to the hinge are both warm."""
    half_a = i < N_LED // 2
    return "W" if (i % 2 == 0) == half_a else "C"


def led_string(i):
    """Return (string, position-in-chain, chain) for ring LED index i (0..39)."""
    half = "1" if i < N_LED // 2 else "2"
    col = led_color(i)
    members = [k for k in range(N_LED) if (k < N_LED // 2) == (half == "1") and led_color(k) == col]
    if half == "2":
        members = members[::-1]  # half B chains run clockwise from the hinge
    return col + half, members.index(i), members


STRINGS = ["W1", "C1", "W2", "C2"]
CHAINS = {s: None for s in STRINGS}
for _i in range(N_LED):
    _s, _k, _m = led_string(_i)
    CHAINS[_s] = _m


def g(n):
    return round(round(n / 1.27) * 1.27, 3)


def build():
    s = Schematic("eclipse-halo", "ECLIPSE - Halo ring LED board", "A", paper="A3",
                  comments=("40x Luminus MP-3030-1100, 2700K/6500K CRI90, 4 strings x 10 @ 100 mA",
                            "Board: annulus OD200/ID160, 2 layers 1.6 mm FR4, 2 oz, white mask, ENIG",
                            "J1 mates with core board J2 through a 1:1 10-wire JST-PH harness"))
    LEDFP = "LED_SMD:LED_Luminus_MP-3030-1100_3.0x3.0mm"
    labels = {"W1": "2700 K", "C1": "6500 K", "W2": "2700 K", "C2": "6500 K"}
    y0 = 50.8
    for row, st in enumerate(STRINGS):
        y = g(y0 + row * 33.02)
        s.box(g(15.24), y - 15.24, g(287.02), y + 12.7,
              f"STRING {st}  ({labels[st]}, half {'A' if st[1] == '1' else 'B'} of the ring)")
        chain = CHAINS[st]
        parts = []
        for k, i in enumerate(chain):
            x = g(40.64 + k * 24.13)
            nets = {"2": f"LED_{st}_A" if k == 0 else f"{st}_N{k}",
                    "1": f"LED_{st}_K" if k == len(chain) - 1 else f"{st}_N{k + 1}"}
            mpn = "MP-3030-1100-27-90" if st[0] == "W" else "MP-3030-1100-65-90"
            parts.append(s.add(Part(f"D{i + 1}", "Device:LED", "2700K" if st[0] == "W" else "6500K", LEDFP,
                                    (x, y), nets, rot=180,
                                    fields={"Manufacturer": "Luminus", "MPN": mpn,
                                            "Description": "3030 mid-power LED, CRI90"})))

    yb = g(y0 + 4 * 33.02)
    s.box(g(300), g(35.56), g(400), g(190), "HARNESS & SENSING")
    s.add(Part("J1", "Connector_Generic_MountingPin:Conn_01x10_MountingPin", "TO CORE",
               "Connector_JST:JST_PH_S10B-PH-SM4-TB_1x10-1MP_P2.00mm_Horizontal", (g(330), g(110)),
               {"1": "LED_C1_K", "2": "LED_C1_A", "3": "LED_W1_A", "4": "LED_W1_K", "5": "NTC", "6": "GND",
                "7": "LED_W2_K", "8": "LED_W2_A", "9": "LED_C2_A", "10": "LED_C2_K", "MP": "GND"},
               fields={"Manufacturer": "JST", "MPN": "S10B-PH-SM4-TB", "Description": "PH 2.0 mm 10-pin side-entry SMD"}))
    s.add(Part("TH1", "Device:Thermistor_NTC", "10k B3380", "Resistor_SMD:R_0603_1608Metric",
               (g(370), g(100)), {"1": "NTC", "2": "GND"},
               fields={"Manufacturer": "Murata", "MPN": "NCP18XH103F03RB", "Description": "NTC 10k 1% B=3380, 0603"}))
    for k in range(4):
        s.add(Part(f"H{k + 1}", "Mechanical:MountingHole", "M2.5", "MountingHole:MountingHole_2.7mm_M2.5",
                   (g(30 + k * 10), g(yb + 5)), {},
                   fields={"Manufacturer": "-", "MPN": "-", "Description": "M2.5 mounting hole"}, in_bom=False))
    s.flag("GND", g(385), g(150))
    s.text("Head temperature: firmware derates above 60 C NTC reading (PMMA body limit)", g(302), g(185), 1.5)
    return s


if __name__ == "__main__":
    import sys
    build().write(sys.argv[1])
