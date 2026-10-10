"""ECLIPSE lamp - CORE board (lives in the weighted base).

USB-C PD sink (9 V) -> 4x TPS61165 boost constant-current LED drivers
(2x warm 2700 K strings, 2x cool 6500 K strings, 100 mA each),
ATtiny1616 with PTC capacitive touch (center key + 3-segment wheel),
NTC read-back from the halo ring, status glow LED, UPDI programming.
"""
from schgen import Part, Schematic

R0603 = "Resistor_SMD:R_0603_1608Metric"
R0805 = "Resistor_SMD:R_0805_2012Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"

G = 2.54


SCALE = 1.9


def g(n):
    return round(round((n + 3) * SCALE / 1.27) * 1.27, 3)


def build():
    s = Schematic("eclipse-core", "ECLIPSE - Core board (base): power, drivers, touch MCU", "A",
                  comments=("USB-C PD 9 V sink, 4ch boost CC LED drivers, ATtiny1616 capacitive touch",
                            "Board: 2 layers, 1.6 mm FR4, 1 oz, matte black mask, ENIG",
                            "Mates with eclipse-halo ring board through J2 / 10-wire JST-PH harness (1:1)"))
    P = lambda *a, **k: s.add(Part(*a, **k))

    def R(ref, val, x, y, n1, n2, fp=R0603, mpn="", mfr="Yageo", desc="", **kw):
        return P(ref, "Device:R", val, fp, (g(x), g(y)), {"1": n1, "2": n2},
                 fields={"Manufacturer": mfr, "MPN": mpn, "Description": desc}, **kw)

    def C(ref, val, x, y, n1, n2, fp=C0603, mpn="", mfr="Murata", desc=""):
        return P(ref, "Device:C", val, fp, (g(x), g(y)), {"1": n1, "2": n2},
                 fields={"Manufacturer": mfr, "MPN": mpn, "Description": desc})

    # ------------------------------------------------------------------ USB-C / PD
    s.box(g(4), g(4), g(84), g(62), "1  USB-C POWER DELIVERY SINK (requests 9 V)")
    P("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C 16P",
      "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", (g(14), g(34)),
      {"S1": "GND", "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
       "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
       "A7": "DM", "B7": "DM", "A6": "DP", "B6": "DP", "A8": None, "B8": None},
      fields={"Manufacturer": "Korean Hroparts", "MPN": "TYPE-C-31-M-12", "LCSC": "C165948",
              "Description": "USB Type-C receptacle, 16P, SMD + THT shell"})
    P("U1", "Interface_USB:CH224K", "CH224K", "Package_SO:SSOP-10-1EP_3.9x4.9mm_P1mm_EP2.1x3.3mm",
      (g(48), g(36)),
      {"7": "CC1", "6": "CC2", "5": "DM", "4": "DP", "8": "VBUS", "11": "GND", "1": "PD_VDD",
       "10": "PD_PG", "9": "PD_CFG1", "2": None, "3": None},
      fields={"Manufacturer": "WCH", "MPN": "CH224K", "LCSC": "C970725",
              "Description": "USB PD/QC sink trigger, resistor-configured output voltage"})
    R("R1", "1k", 40, 14, "VBUS", "PD_VDD", mpn="RC0603FR-071KL", desc="CH224K VDD feed")
    C("C3", "1uF", 58, 14, "PD_VDD", "GND", mpn="GRM188R61E105KA12D", desc="CH224K VDD decoupling")
    R("R2", "6.8k", 72, 44, "PD_CFG1", "GND", mpn="RC0603FR-076K8L", desc="CFG1: 6.8k = 9 V request")
    R("R3", "10k", 66, 24, "+3V3", "PD_PG", mpn="RC0603FR-0710KL", desc="PG pull-up")
    s.text("CFG1 resistor sets the PD request: 6.8k=9V  24k=12V  56k=15V  open=20V", g(36), g(56), 1.5)
    s.text("(firmware derates if only 5 V is granted, see VSENSE)", g(36), g(58.5), 1.5)

    # protection & bulk
    s.box(g(86), g(4), g(140), g(62), "2  INPUT PROTECTION & BULK")
    P("F1", "Device:Polyfuse", "1.5A", "Fuse:Fuse_1812_4532Metric", (g(96), g(20)),
      {"1": "VBUS", "2": "VIN"},
      fields={"Manufacturer": "Bourns", "MPN": "MF-MSMF150/24X-2", "Description": "PTC resettable fuse 1.5 A hold, 24 V"})
    P("D1", "Device:D_TVS", "SMAJ15CA", "Diode_SMD:D_SMA", (g(108), g(34)), {"1": "VIN", "2": "GND"},
      fields={"Manufacturer": "Littelfuse", "MPN": "SMAJ15CA", "Description": "TVS 15 V standoff, bidirectional, 400 W"})
    C("C1", "22uF 25V", 122, 20, "VIN", "GND", fp=C1206, mpn="GRM31CR61E226KE15L", desc="Input bulk")
    C("C2", "22uF 25V", 132, 20, "VIN", "GND", fp=C1206, mpn="GRM31CR61E226KE15L", desc="Input bulk")
    s.flag("VBUS", g(90), g(44))
    s.flag("VIN", g(100), g(44))
    s.flag("GND", g(110), g(48))

    # 3V3
    s.box(g(142), g(4), g(196), g(62), "3  3.3 V LOGIC SUPPLY")
    P("U2", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
      (g(168), g(30)), {"3": "VIN", "1": "GND", "2": "+3V3"},
      fields={"Manufacturer": "Advanced Monolithic Systems", "MPN": "AMS1117-3.3", "LCSC": "C6186",
              "Description": "LDO 3.3 V 1 A"})
    C("C4", "10uF", 152, 30, "VIN", "GND", fp=C0805, mpn="CL21A106KAYNNNE", mfr="Samsung", desc="LDO input")
    C("C5", "22uF", 184, 30, "+3V3", "GND", fp=C0805, mpn="CL21A226MAQNNNE", mfr="Samsung", desc="LDO output")
    s.flag("PD_VDD", g(64), g(9))

    # ------------------------------------------------------------------ MCU
    s.box(g(4), g(64), g(110), g(150), "4  MCU - ATtiny1616 (PTC touch, TCA0 PWM)")
    P("U3", "MCU_Microchip_ATtiny:ATtiny1616-S", "ATtiny1616-S", "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
      (g(40), g(106)),
      {"1": "+3V3", "20": "GND", "16": "UPDI", "17": "VSENSE", "18": "PD_PG", "19": "NTC",
       "2": "TCH0", "3": "TCH1", "4": "TCH2", "5": "TCH3",
       "11": "PWM_W", "10": "PWM_C", "9": "LED_STAT", "8": None, "7": None, "6": None,
       "12": "GLOW_PWM", "13": None, "14": None, "15": None},
      fields={"Manufacturer": "Microchip", "MPN": "ATTINY1616-SNR", "Description": "AVR 16 kB, PTC touch, 20 MHz"})
    C("C6", "100nF", 12, 76, "+3V3", "GND", mpn="GRM188R71H104KA93D", desc="MCU decoupling")
    C("C7", "1uF", 20, 76, "+3V3", "GND", mpn="GRM188R61E105KA12D", desc="MCU decoupling")
    P("J3", "Connector_Generic:Conn_01x03", "UPDI", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
      (g(14), g(132)), {"1": "+3V3", "2": "UPDI", "3": "GND"},
      fields={"Manufacturer": "-", "MPN": "DNP (pogo pads)", "Description": "UPDI programming header"}, dnp=True)
    R("R4", "100k", 80, 80, "VIN", "VSENSE", mpn="RC0603FR-07100KL", desc="VIN sense divider top")
    R("R5", "15k", 80, 92, "VSENSE", "GND", mpn="RC0603FR-0715KL", desc="VIN sense divider bottom")
    C("C8", "100nF", 88, 92, "VSENSE", "GND", mpn="GRM188R71H104KA93D")
    R("R6", "10k", 98, 80, "+3V3", "NTC", mpn="RC0603FR-0710KL", desc="NTC pull-up")
    C("C9", "100nF", 98, 92, "NTC", "GND", mpn="GRM188R71H104KA93D")
    R("R12", "100k", 80, 132, "PWM_W", "GND", mpn="RC0603FR-07100KL", desc="Keeps drivers off during reset")
    R("R13", "100k", 90, 132, "PWM_C", "GND", mpn="RC0603FR-07100KL", desc="Keeps drivers off during reset")
    R("R11", "470", 70, 106, "LED_STAT", "LED_STAT_A", mpn="RC0603FR-07470RL", desc="Status LED")
    P("D2", "Device:LED", "WHITE", "LED_SMD:LED_0603_1608Metric", (g(84), g(114)),
      {"1": "GND", "2": "LED_STAT_A"},
      fields={"Manufacturer": "Lite-On", "MPN": "LTW-C191TS5", "Description": "0603 white - glow under touch glass"})

    # ------------------------------------------------------------------ touch
    s.box(g(112), g(64), g(196), g(150), "5  CAPACITIVE TOUCH (self-cap through 3 mm glass)")
    for i, (ref, x, y, name) in enumerate([("E1", 160, 76, "KEY"), ("E2", 160, 96, "WHEEL_A"),
                                            ("E3", 160, 116, "WHEEL_B"), ("E4", 160, 136, "WHEEL_C")]):
        R("R%d" % (7 + i), "1k", 136, y - 6, "TCH%d" % i, "TPAD%d" % i, mpn="RC0603FR-071KL",
          desc="PTC series resistor", rot=90)
        fp = "eclipse:TouchKey_D14" if i == 0 else "eclipse:TouchWheel_Seg120"
        P(ref, "Connector:TestPoint", "TOUCH_" + name, fp, (g(x), g(y - 6)), {"1": "TPAD%d" % i},
          fields={"Manufacturer": "-", "MPN": "PCB copper electrode", "Description": "Touch electrode"},
          in_bom=False)
    s.text("Wheel = brightness, tap key = on/off, hold key + wheel = colour temperature", g(114), g(146), 1.5)

    # ------------------------------------------------------------------ LED drivers
    chans = [("W1", "PWM_W"), ("C1", "PWM_C"), ("W2", "PWM_W"), ("C2", "PWM_C")]
    for n, (ch, pwm) in enumerate(chans):
        x0 = 4 + n * 48
        s.box(g(x0), g(152), g(x0 + 46), g(206), f"{6 + n}  BOOST CC DRIVER {ch} (100 mA, <=38 V)")
        bx = x0 + 22
        P(f"U{4 + n}", "Driver_LED:TPS61165DBV", "TPS61165", "Package_TO_SOT_SMD:SOT-23-6",
          (g(bx), g(180)),
          {"1": "VIN", "2": pwm, "5": f"COMP_{ch}", "4": "GND", "3": f"SW_{ch}", "6": f"LED_{ch}_K"},
          fields={"Manufacturer": "Texas Instruments", "MPN": "TPS61165DBVR",
                  "Description": "38 V boost white-LED driver, 1.2 A switch"})
        C(f"C{10 + n}", "10uF 25V", x0 + 6, 172, "VIN", "GND", fp=C0805, mpn="CL21A106KAYNNNE", mfr="Samsung",
          desc="Boost input")
        C(f"C{18 + n}", "220nF", x0 + 10, 192, f"COMP_{ch}", "GND", mpn="GRM188R71E224KA88D",
          desc="Loop compensation")
        P(f"L{1 + n}", "Device:L", "10uH", "Inductor_SMD:L_Bourns-SRN4018", (g(bx + 10), g(162)),
          {"1": "VIN", "2": f"SW_{ch}"},
          fields={"Manufacturer": "Bourns", "MPN": "SRN4018-100M", "Description": "10 uH shielded, Isat 1.6 A"})
        P(f"D{3 + n}", "Device:D_Schottky", "MBRA160", "Diode_SMD:D_SMA", (g(bx + 16), g(170)),
          {"2": f"SW_{ch}", "1": f"LED_{ch}_A"},
          fields={"Manufacturer": "onsemi", "MPN": "MBRA160T3G", "Description": "Schottky 60 V 1 A"})
        C(f"C{14 + n}", "1uF 50V", x0 + 42, 182, f"LED_{ch}_A", "GND", fp=C1206, mpn="GRM31MR71H105KA88L",
          desc="Boost output")
        R(f"R{14 + n}", "2.0", x0 + 36, 194, f"LED_{ch}_K", "GND", fp=R0805, mpn="RC0805FR-072RL",
          desc="Sense: 200 mV / 2.0 R = 100 mA")

    # ------------------------------------------------------------------ ring connector
    s.box(g(198), g(4), g(232), g(100), "11  BODY GLOW (lights the opal base band) + MECHANICAL")
    for k in range(8):
        x = 201 + k * 4
        R(f"R{18 + k}", "100", x, 38, "+3V3", f"GLOW_A{k}", mpn="RC0603FR-07100RL",
          desc="Glow LED ballast, ~5 mA")
        P(f"D{7 + k}", "Device:LED", "2700K", "LED_SMD:LED_PLCC_2835", (g(x), g(50)),
          {"2": f"GLOW_A{k}", "1": "GLOW_K"}, rot=90,
          fields={"Manufacturer": "Samsung", "MPN": "LM281B+ 2700K",
                  "Description": "2835 warm white, fires down into the white-lined base cavity"})
    P("Q1", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23", (g(216), g(68)),
      {"1": "GLOW_G", "3": "GLOW_K", "2": "GND"},
      fields={"Manufacturer": "Alpha & Omega", "MPN": "AO3400A", "Description": "N-MOSFET 30 V, low-side glow switch"})
    R("R26", "100", 206, 70, "GLOW_PWM", "GLOW_G", mpn="RC0603FR-07100RL", desc="Gate series", rot=90)
    R("R27", "100k", 210, 80, "GLOW_G", "GND", mpn="RC0603FR-07100KL", desc="Gate pull-down")
    s.text("PC0 = TCD0 WOC PWM: breathing night-glow through the base", g(200), g(96), 1.5)
    s.box(g(198), g(152), g(232), g(206), "10  HALO HARNESS")
    P("J2", "Connector_Generic_MountingPin:Conn_01x10_MountingPin", "TO HALO",
      "Connector_JST:JST_PH_S10B-PH-SM4-TB_1x10-1MP_P2.00mm_Horizontal", (g(222), g(176)),
      {"1": "LED_C1_K", "2": "LED_C1_A", "3": "LED_W1_A", "4": "LED_W1_K", "5": "NTC", "6": "GND",
       "7": "LED_W2_K", "8": "LED_W2_A", "9": "LED_C2_A", "10": "LED_C2_K", "MP": "GND"},
      fields={"Manufacturer": "JST", "MPN": "S10B-PH-SM4-TB", "Description": "PH 2.0 mm 10-pin side-entry SMD"})
    for i, (ref, x) in enumerate([("H1", 204), ("H2", 212), ("H3", 220)]):
        P(ref, "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", (g(x), g(14)), {},
          fields={"Manufacturer": "-", "MPN": "-", "Description": "M3 mounting hole"}, in_bom=False)
    s.text("1:1 harness to halo J1 (through the stem)", g(200), g(203), 1.5)
    return s


if __name__ == "__main__":
    import sys
    sch = build()
    sch.write(sys.argv[1])
