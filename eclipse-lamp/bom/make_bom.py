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
    "MP-3030-1100-27-90": 0.12, "MP-3030-1100-65-90": 0.12, "NCP18XH103F03RB": 0.03, "LM281B+ 2700K": 0.03, "AO3400A": 0.03,
    "DNP (pogo pads)": 0.0, "PCB copper electrode": 0.0,
}
R0603 = 0.002

MECH = [  # ref, qty, description, material / process, part, unit USD
    ("M1", 1, "Base upper shell, D150 x 12 (touch skin + trunk socket)", "6061-T6, CNC turned+milled, bead blast, graphite anodise; cavity white-painted", "ECL-M-001", 7.50),
    ("M2", 1, "Weight / reflector disc, D110 x 6.5 (~0.48 kg)", "S235 steel, laser cut, white powder coat", "ECL-M-002", 1.60),
    ("M3", 1, "Root-glow band, D148/D138 x 7", "Light-diffusing PMMA, extruded tube cut + polished", "ECL-M-003", 0.70),
    ("M4", 1, "Plinth, D150 x 3 + 3 posts (~0.42 kg)", "S235 steel, laser cut, posts welded, black powder coat", "ECL-M-004", 2.40),
    ("M5", 1, "Foot ring, D146/D122 x 1", "Cork/rubber composite, die cut, PSA backed", "ECL-M-005", 0.30),
    ("M6", 1, "Touch window, D52 x 3", "Soda-lime glass, satin etch top, screen-printed ring", "ECL-M-006", 1.60),
    ("M7", 1, "Trunk, 14 x 2 tube, S-bent, ~150 mm + root flare", "C260 brass tube, CNC bent, flare spun + brazed", "ECL-M-007", 3.20),
    ("M8", 1, "Burl (fork knot), 2 cast halves, houses the hub", "Lost-wax cast silicon bronze, ~80 g", "ECL-M-008", 6.50),
    ("M9", 1, "Crown: 4 limbs, 75 branches + 189 spur twigs (4.7 m)", "C260 brass rod D1-6 mm, hand-formed on a jig from the CAD skeleton, brazed", "ECL-M-009", 18.00),
    ("M10", 1, "Bark finish, whole tree", "Brown-grey liver-of-sulphur patina + matte lacquer", "ECL-M-010", 2.50),
    ("M11", 1, "Magnet wire, 80 x 0.15 mm, ~0.35 m each, laid in branch grooves", "Polyurethane-enamelled Cu (solderable), bark-colour", "ECL-W-002", 0.60),
    ("M12", 1, "Trunk harness, 10 x AWG30 PTFE, 260 mm", "Hub J1 lands -> core J2 (JST PHR-10 + SPH-002T)", "ECL-W-001", 0.70),
    ("M13", 1, "Burl potting", "Black flexible epoxy, ~4 ml", "ECL-M-013", 0.20),
    ("F1", 3, "Screw M3 x 6, pan head (core PCB)", "A2 stainless", "ISO 14583", 0.02),
    ("F2", 1, "Set screw M4 x 4, cup point (trunk socket)", "A2 stainless", "ISO 4029", 0.02),
    ("F3", 3, "Screw M3 x 10, countersunk (plinth posts into shell)", "A2 stainless", "ISO 10642", 0.03),
    ("F4", 2, "Screw M2 x 6 (burl halves)", "A2 stainless", "ISO 14583", 0.02),
    ("F5", 40, "Sprig clip: 0.3 mm brass crimp sleeve, sprig root to twig tip", "C260 brass", "ECL-M-014", 0.01),
]
PCB_FAB = [
    ("PCB1", 1, "Core PCB, D124 + USB tab, 2L 1.6 mm FR4, 1 oz, matte black, ENIG", "eclipse-core", 1.20),
    ("PCB2", 1, "Hub PCB, D36 with D4 hole, 2L 1.0 mm FR4, black, ENIG", "eclipse-hub", 0.35),
    ("PCB3", 40, "Sprig flex, 2L polyimide 0.11 mm, bronze coverlay, ENIG (panelised)", "eclipse-sprig", 0.22),
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
    for board, label, mult in (("core", "Core board (base)", 1), ("hub", "Hub board (in the burl)", 1),
                               ("sprig", "LED sprigs (x40 per lamp)", 40)):
        for r in kicad_bom(board):
            mpn = r["MPN"]
            if board == "sprig" and r["Value"] == "LEAF":
                # one sprig design, two LED builds: 20 warm sprigs + 20 cool sprigs
                per = int(r["Qty"])
                for cct, cnt in (("2700 K", 20), ("6500 K", 20)):
                    q = per * cnt
                    rows.append({"Section": label, "Refs": f"{r['Refs']} on {cnt} sprigs", "Qty": q,
                                 "Value": f"LEAF {cct}", "Description": f"Leaf LED 0402 white {cct}, If 5 mA",
                                 "Manufacturer": r["Manufacturer"], "MPN": f"0402 white LED {cct} (select bin)",
                                 "LCSC": "", "Footprint": r["Footprint"].split(":")[-1],
                                 "Unit USD": 0.012, "Ext USD": round(0.012 * q, 3), "Note": "same Vf bin per sprig"})
                continue
            unit = PRICE.get(mpn, R0603 if mpn.startswith("RC0603") else None)
            if unit is None:
                raise SystemExit(f"no price for {mpn}")
            qty = int(r["Qty"]) * mult
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
    md = ["# ECLIPSE Tree - Bill of Materials", "",
          "Generated by `make_bom.py` from the KiCad schematics plus the mechanical parts list.",
          "Unit prices are **budgetary estimates** (USD, 1k-unit volume). Re-quote before ordering.", ""]
    for sec in ("Core board (base)", "Hub board (in the burl)", "LED sprigs (x40 per lamp)", "Bare PCBs", "Mechanical"):
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
