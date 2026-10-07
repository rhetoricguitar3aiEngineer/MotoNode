"""Build the full ECLIPSE bill of materials.

Electronics lines come straight from the KiCad schematics (kicad-cli BOM export,
grouped by MPN); mechanical lines are listed here.  Unit prices are budgetary
estimates in USD at 1k units (distributor / quote level, Oct 2026) - re-quote
before ordering.

    python3 make_bom.py      -> eclipse_bom.csv, BOM.md
"""
import csv, io, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ELEC = os.path.join(HERE, "..", "electronics")

PRICE = {  # MPN -> USD @1k (estimate)
    "TYPE-C-31-M-12": 0.12, "CH224K": 0.35, "MF-MSMF150/24X-2": 0.10, "SMAJ15CA": 0.05,
    "GRM31CR61E226KE15L": 0.06, "AMS1117-3.3": 0.05, "ATTINY1616-SNR": 0.85, "TPS61165DBVR": 0.55,
    "SRN4018-100M": 0.12, "MBRA160T3G": 0.06, "GRM31MR71H105KA88L": 0.04, "CL21A106KAYNNNE": 0.02,
    "CL21A226MAQNNNE": 0.02, "GRM188R71E224KA88D": 0.006, "GRM188R71H104KA93D": 0.004,
    "GRM188R61E105KA12D": 0.006, "RC0805FR-072RL": 0.004, "LTW-C191TS5": 0.03, "S10B-PH-SM4-TB": 0.25,
    "MP-3030-1100-27-90": 0.12, "MP-3030-1100-65-90": 0.12, "NCP18XH103F03RB": 0.03,
    "DNP (pogo pads)": 0.0, "PCB copper electrode": 0.0,
}
R0603 = 0.002

MECH = [  # ref, qty, description, material / process, part, unit USD
    ("M1", 1, "Base shell, D150 x 22", "6061-T6, CNC turned+milled, bead blast, graphite anodise", "ECL-M-001", 9.00),
    ("M2", 1, "Base weight disc, D137 x 7 (~0.8 kg)", "S235 steel, laser cut, zinc plated", "ECL-M-002", 2.20),
    ("M3", 1, "Bottom cover, D137 x 1.2", "5052 aluminium, laser cut, anodise", "ECL-M-003", 1.20),
    ("M4", 1, "Foot ring, D146/D122 x 1", "Cork/rubber composite, die cut, PSA backed", "ECL-M-004", 0.30),
    ("M5", 1, "Touch window, D52 x 3", "Soda-lime glass, satin etch top, screen-printed ring", "ECL-M-005", 1.60),
    ("M6", 1, "Stem, 12 x 2 tube, 340 mm + R90 bend", "6063 tube, CNC bent, brass-tone PVD", "ECL-M-006", 3.50),
    ("M7", 1, "Hinge yoke", "6061 CNC, graphite anodise", "ECL-M-007", 2.20),
    ("M8", 1, "Friction knob, knurled D18", "C360 brass, CNC, clear lacquer", "ECL-M-008", 1.80),
    ("M9", 1, "Halo housing, D212/D148 x 14 + knuckle", "ADC12 die-cast + CNC, graphite anodise-look powder", "ECL-M-009", 6.50),
    ("M10", 1, "Diffuser ring, D208/D152 x 2", "Opal PMMA (55 % T), laser cut, polished edge", "ECL-M-010", 0.90),
    ("M11", 1, "Thermal pad ring, D200/D160 x 0.5", "Silicone gap pad 1.5 W/mK, die cut", "ECL-M-011", 0.60),
    ("M12", 1, "Harness, 10 x AWG28, 520 mm, JST PH 1:1", "PHR-10 housings, SPH-002T crimps, PTFE wire", "ECL-W-001", 0.80),
    ("F1", 3, "Screw M3 x 6, pan head (core PCB)", "A2 stainless", "ISO 14583", 0.02),
    ("F2", 4, "Screw M2.5 x 5, pan head (halo PCB)", "A2 stainless", "ISO 14583", 0.02),
    ("F3", 1, "Set screw M4 x 4, cup point (stem)", "A2 stainless", "ISO 4029", 0.02),
    ("F4", 1, "Shoulder screw D4 x 16 + M3 (hinge pin)", "A2 stainless", "ISO 7379", 0.25),
    ("F5", 2, "Wave washer D4.2 (hinge friction)", "Spring steel", "DIN 137B", 0.04),
    ("F6", 4, "Screw M2 x 4, countersunk (bottom cover)", "A2 stainless", "ISO 10642", 0.02),
]
PCB_FAB = [
    ("PCB1", 1, "Core PCB, D124 + USB tab, 2L 1.6 mm FR4, 1 oz, matte black, ENIG", "eclipse-core", 1.20),
    ("PCB2", 1, "Halo PCB, ring D200/D160, 1L aluminium MCPCB 1.5 mm, white mask, ENIG", "eclipse-halo", 2.50),
]


def kicad_bom(board):
    sch = os.path.join(ELEC, board, f"eclipse-{board}.kicad_sch")
    tmp = f"/tmp/eclipse-{board}-bom.csv"
    subprocess.run(["kicad-cli", "sch", "export", "bom", "-o", tmp, "--fields",
                          "Reference,Value,Footprint,Manufacturer,MPN,LCSC,Description,${QUANTITY},${DNP}",
                          "--labels", "Refs,Value,Footprint,Manufacturer,MPN,LCSC,Description,Qty,DNP",
                          "--group-by", "Value,Footprint,MPN", "--ref-range-delimiter", "", sch],
                         capture_output=True, text=True, check=True)
    return list(csv.DictReader(open(tmp)))


def main():
    rows = []
    for board, label in (("core", "Core board (base)"), ("halo", "Halo ring board")):
        for r in kicad_bom(board):
            mpn = r["MPN"]
            unit = PRICE.get(mpn, R0603 if mpn.startswith("RC0603") else None)
            if unit is None:
                raise SystemExit(f"no price for {mpn}")
            qty = int(r["Qty"])
            dnp = bool(r["DNP"].strip())
            rows.append({"Section": label, "Refs": r["Refs"], "Qty": qty, "Value": r["Value"],
                         "Description": r["Description"], "Manufacturer": r["Manufacturer"], "MPN": mpn,
                         "LCSC": r["LCSC"], "Footprint": r["Footprint"].split(":")[-1],
                         "Unit USD": unit, "Ext USD": 0.0 if dnp else round(unit * qty, 3),
                         "Note": "DNP" if dnp else ""})
    for ref, qty, desc, part, unit in PCB_FAB:
        rows.append({"Section": "Bare PCBs", "Refs": ref, "Qty": qty, "Value": "", "Description": desc,
                     "Manufacturer": "PCB fab (e.g. JLCPCB)", "MPN": part, "LCSC": "", "Footprint": "",
                     "Unit USD": unit, "Ext USD": round(unit * qty, 3), "Note": "gerbers via KiCad"})
    for ref, qty, desc, matl, part, unit in MECH:
        rows.append({"Section": "Mechanical", "Refs": ref, "Qty": qty, "Value": "", "Description": desc,
                     "Manufacturer": matl, "MPN": part, "LCSC": "", "Footprint": "",
                     "Unit USD": unit, "Ext USD": round(unit * qty, 3), "Note": ""})
    cols = list(rows[0].keys())
    with open(os.path.join(HERE, "eclipse_bom.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    totals = {}
    for r in rows:
        totals[r["Section"]] = totals.get(r["Section"], 0) + r["Ext USD"]
    md = ["# ECLIPSE - Bill of Materials", "",
          "Generated by `make_bom.py` from the KiCad schematics plus the mechanical parts list.",
          "Unit prices are **budgetary estimates** (USD, 1k-unit volume). Re-quote before ordering.", ""]
    for sec in ("Core board (base)", "Halo ring board", "Bare PCBs", "Mechanical"):
        md += [f"## {sec}", "", "| Refs | Qty | Value | Description | Manufacturer | MPN | Unit $ | Ext $ |",
               "|---|---:|---|---|---|---|---:|---:|"]
        for r in rows:
            if r["Section"] == sec:
                refs = r["Refs"] if len(r["Refs"]) < 60 else r["Refs"][:57] + "..."
                md.append(f"| {refs} | {r['Qty']} | {r['Value']} | {r['Description']}{' (DNP)' if r['Note']=='DNP' else ''} "
                          f"| {r['Manufacturer']} | {r['MPN']} | {r['Unit USD']:.3f} | {r['Ext USD']:.2f} |")
        md += ["", f"**Subtotal: ${totals[sec]:.2f}**", ""]
    grand = sum(totals.values())
    md += ["## Summary", "", "| Section | USD |", "|---|---:|"]
    md += [f"| {k} | {v:.2f} |" for k, v in totals.items()]
    md += [f"| **Total material (excl. assembly, packaging, PSU)** | **{grand:.2f}** |", ""]
    open(os.path.join(HERE, "BOM.md"), "w").write("\n".join(md))
    print(f"{len(rows)} lines, total ${grand:.2f}")
    for k, v in totals.items():
        print(f"  {k}: {v:.2f}")


if __name__ == "__main__":
    main()
