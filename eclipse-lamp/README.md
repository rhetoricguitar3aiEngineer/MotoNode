# ECLIPSE Tree: a cedar elm made of light

![ECLIPSE Tree on a desk](renders/eclipse_hero.png)

ECLIPSE Tree is a desk lamp in the form of an old cedar elm (*Ulmus crassifolia*). In
daylight it reads as a small tree in leaf; switched on, it fills with light:

* **Grown, not drawn.** The crown is grown by space colonisation: buds compete for space in
  a rounded crown, so the wood forks where the space divides and tapers continuously (pipe
  model) from a 77 mm trunk through three leaders to **1,174 twigs**.
* **Leaves.** 40 flexible-circuit sprays carry **800 LED leaves** (0402) among **21,770
  leaves of light-diffusing film**, so the foliage glows green-gold around every light.
* **Trunk.** The trunk, its fork and its buttress roots are a thin bronze shell around a
  light-diffusing acrylic light-guide tube. Light travels down the tube and leaks out
  wherever the bark is split, so the trunk glows through its furrows.
* **Seeds.** End-glow optical fibres light **567 diffusing samaras** (cedar-elm seeds) among
  the twigs.

Warm and cool light is interleaved everywhere, so the whole tree can be mixed from candle
glow to daylight, dimmed to embers, or left with only its roots glowing.

| | |
|---|---|
| ![trunk](renders/eclipse_trunk.png) | ![leaves](renders/eclipse_leaves.png) |
| ![night](renders/eclipse_night.png) | ![studio](renders/eclipse_studio.png) |
| ![cool](renders/eclipse_cool.png) | ![detail](renders/eclipse_detail.png) |
| ![hub top](renders/pcb_hub.png) | ![sprig](renders/pcb_sprig.png) |

## Four light paths, one driver per colour channel

```
                     ┌─ 2 top LEDs ──► fibre ferrule ──► 4 bundles × ~142 end-glow fibres ──► 567 glowing samaras
 HUB light engine  ──┤
 (in the trunk fork) └─ 2 bottom LEDs ─► trunk PMMA light-guide tube ──► TIR + extraction ──► glowing bark furrows
        │                                                                                    and buttress roots
        └─ then 10 LED sprigs in series ──► 20 × 0402 leaves each ──► 800 LED leaves ──► glowing leaf film

 CORE board (base): USB-C PD 9 V → 4 × TPS61165 constant-current boost @ 100 mA (W1 C1 W2 C2)
                    ATtiny1616 touch wheel, colour mix, + 8 LEDs → opal root-glow band (night light)
```

Each colour channel is **one series string of 11 elements** (≈31.5 V, inside the 38 V OVP):
first the hub's 4-LED light-engine group, then 10 sprigs. So all four optical systems dim
and colour-shift together from the same four drivers. The core board circuit is unchanged
from the previous revision, and only 10 wires run down the trunk.

## Key specs

| | |
|---|---|
| Size | ≈435 mm tall, crown ≈370 × 360 mm, on a Ø150 mm base |
| Tree | Space-colonisation grown cedar elm: 77 mm trunk (cast bronze shell + PMMA light-guide tube), 7 buttress roots, 3 leaders, 1,174 branches and twigs, 21,770 film leaves (seeded, reproducible) |
| Light sources | 800 × 0402 LED leaves + 16 × 2835 light-engine LEDs (8 → fibres, 8 → trunk core) + 8 × 2835 root glow |
| Optics | PMMA light-guide trunk with fissure extraction · light-diffusing leaf film lit by the LED leaves · 567 × 0.5 mm end-glow PMMA fibres in 4 bundles · 567 diffusing-epoxy samaras · opal root band |
| Light | 12.6 W max LED power (firmware cap ≈8.5 W), ≈600 lm total (estimated), 2700-6500 K, flicker-free |
| Mass / stability | ≈4.1 kg, centre of gravity 8.5 mm from the base centre (66 mm inside the base edge) |
| Power / controls | USB-C PD 9 V (18 W+ charger), capacitive wheel through 3 mm glass |

## What's in this folder

```
eclipse-lamp/
├── mechanical/   tree_gen.py (space-colonisation cedar elm: trunk, fork, roots, wood, sprigs, samaras, foliage),
│                 eclipse_cad.py (CadQuery, mass/CoG), wiring_map.py, out/ (STEP/STL, big STEPs zipped,
│                 foliage.stl leaf-cutting file, parts.json)
├── electronics/
│   ├── core/     KiCad 9: base board (power, 4 drivers, touch MCU, root glow), unchanged circuit
│   ├── hub/      KiCad 9: Ø56 two-sided light engine in the trunk fork (16 LEDs) + 40 sprig lands + chaining + NTC
│   ├── sprig/    KiCad 9: polyimide flex cedar-elm spray, 20 × 0402 LED leaves (×40 per lamp)
│   ├── lib/      custom footprints + 3D models
│   └── tools/    generators: schematics (wire router), PCBs, layouts, netlist checks, fab export
├── bom/          eclipse_bom.csv, BOM.md (≈$147 material at 1k units, estimates)
├── renders/      Cycles renders + KiCad board renders, render_blender.py
└── docs/         DESIGN.md (design notes, optics, calculations), WIRING.md (sprig map)
```

## Verification

Every schematic draws every signal connection as a visible wire. There are no net labels,
and power uses power symbols only (see `/CLAUDE.md`).

| Check | Core | Hub | Sprig |
|---|---|---|---|
| ERC | 0 / 0 | 0 / 0 | 0 / 0 |
| DRC | 0 violations | 0 violations | 0 violations |
| Unrouted | 0 | 0 | 0 |
| Schematic ↔ PCB parity | 0 issues | 0 issues | 0 issues |
| Netlist vs design intent | 0 mismatches | 0 mismatches | 0 mismatches |

## Rebuild everything

Requires KiCad 9 (`kicad-cli` + `pcbnew` Python), CadQuery 2.x, numpy, scipy, shapely, Freerouting 1.9
(core board only, Java 21 + `xvfb-run`) and the `bpy` 5.x module for renders.

```sh
cd electronics/tools
python3 make_footprints.py && python3 make_3d_models.py
for b in core hub sprig; do
  python3 design_$b.py ../$b/eclipse-$b.kicad_sch
  (cd ../$b && kicad-cli sch export netlist --format kicadsexpr -o eclipse-$b.net eclipse-$b.kicad_sch)
  python3 verify_netlist.py design_$b ../$b/eclipse-$b.net
done
python3 pcb_hub.py && python3 pcb_sprig.py   # parametric layouts
./route_core.sh                             # core: placement → Freerouting → pours → DRC
./export_fab.sh                             # gerbers, drill, P&P, PDFs, STEP/GLB, reports
cd ../../mechanical && python3 eclipse_cad.py && python3 wiring_map.py
cd ../bom && python3 make_bom.py
cd ../renders && python3 render_blender.py hero   # hero | trunk | leaves | night | studio | cool | detail
```

See [docs/DESIGN.md](docs/DESIGN.md) for the optics, the calculations and the open items.
