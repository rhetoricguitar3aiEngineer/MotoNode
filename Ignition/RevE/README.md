# MotoNode ignition controller + hub: KiCad 10 project, Rev E

4 TCI channels plus 1 CDI channel, an ESP32-S3 controller and a hardware safety chain, now with the **hub functions on the same board** (MPU-6050 motion sensor, NEO-6M GPS port, two protected OEM-sensor inputs) and **tool-less push-in terminals for every wire**.

- **Rev E** = Rev D2 (SPICE-validated, see `SIMULATION.md`) + merged hub + push-in connectors + a fully laid-out board.
- **Status: designed and checked by software, not built.** Nothing has been bench-tested.

## Opening it
Open `MotoNode_ignition.kicad_pro` in **KiCad 10**. All files are native KiCad 10.0 format; the project needs nothing outside this folder (symbols, footprints, 3D models, library tables, design rules are all inside).

## The board
| | |
|---|---|
| Size | **100 x 70 mm** (3.94 x 2.76 in), inside the 4 x 3 in limit |
| Layers | **6**: F.Cu / In1 ground planes / In2, In3, In4 signals / B.Cu. In1 is split: PGND (power side, left) and GND (logic side, right), joined once at net tie NT101 beside the battery terminal. |
| Parts | 241, on both sides |
| Routing | **100 % routed**: 0 unconnected items (2,726 track segments, 391 vias), copper pours on both outer layers tied to the In1 planes |
| DRC (KiCad 10.0.6, `--severity-all --schematic-parity`) | **0 errors, 0 unconnected, 0 schematic-parity issues**; 1 warning: `lib_footprint_mismatch` on U302 (the Espressif ESP32-S3-MINI-1 footprint copy on the board differs from the library copy only in how its antenna keep-out is stored; the board copy is the one used) |
| HV spacing | Net class HV (HV_BUS, COIL1_TOP, coil collectors, flyback secondary, dividers, SCR gate): **2.5 mm to LV copper on outer layers** (IPC-2221B B2, 301-500 V, uncoated: no conformal coating needed), **0.5 mm on inner layers** (B1 internal, 0.25 mm x 2), **1.0 mm between different HV nets** |
| Exemptions (`MotoNode_ignition.kicad_dru`) | pads inside one HV-rated part (the package sets them); floating no-net pads (unused transformer pins); the SCR gate network, which floats with its own cathode COIL1_TOP; copper on the pads of the 0603 HV-indicator LED D107 |
| Fab notes | 0.15/0.15 mm track/space, 0.6/0.3 mm vias plus a few 0.3/0.15 mm **via-in-pad (filled and capped)** on ground pins of fine-pitch ICs. JLCPCB fills/caps via-in-pad at no charge on 6-layer boards. |

**Why 6 layers:** the same placement on 4 layers left about 50 connections the autorouter could not finish around the ESP32 / comparator / driver logic; 6 layers closes them without making the board bigger.

### Floor plan
- **Bottom edge, wire entry flush with the edge:** J201 coils (6 x 5.0 mm), J101 battery (2 x 5.0 mm), J102 signals (8 x 2.5 mm, vertical entry).
- **Output stage directly above J201, one power device per terminal column:** Q203 (CH1) and Q205 (CH3) on top, Q204 (CH2) and Q206 (CH4) underneath, Q201 coil feed on top, Q207 CDI SCR underneath. Each collector runs straight into its terminal on 2.0-2.5 mm copper; emitter shunts sit right above, gate resistors and pull-downs in the band between.
- **HV block, top left:** flyback T101 + C113, CDI SCR Q105, trigger transformer T102, four 3 x 1206 divider chains in straight lines. The CDI output reaches J201.1 on an inner layer along the left edge.
- **Battery path:** J101.1 -> ATO fuse F101 -> reverse-polarity FET Q101 -> +12V -> HS shunt R201 -> Q201 -> J201.6.
- **Logic, right half:** ESP32-S3 top right (antenna at the board edge, copper keep-out on all layers), comparators and dwell logic, gate driver U304 and sense amp U202 next to the output stage, IMU U401 in the quiet corner above J102, away from the flyback.

How it was laid out: the power and HV skeleton (about 150 tracks: collectors, emitters, gates, battery path, CDI and flyback secondary) was placed and routed by script (`pcb_layout/powroute.py`); the rest was autorouted with Freerouting in stages (HV + power nets first with an HV clearance matrix, then everything), the last few connections with a grid router that applies the same rules, and every step re-checked with KiCad 10 DRC.

## Connectors (no soldering or crimping of wires)
| Ref | Part | Wire | Pins |
|---|---|---|---|
| J101 battery | Würth WR-TBL 4067B **691406710002B**, 2 pole, push-in, 5.0 mm | 24-12 AWG (your 18-14 AWG fits), 20 A, 300 V | 1 +12 V battery (fused), 2 battery - |
| J201 coils | Würth **691406710006B**, 6 pole | 24-12 AWG, 20 A | 1 CH1 coil + (CDI/TCI), 2 CH1 coil -, 3 CH2 -, 4 CH3 -, 5 CH4 -, 6 CH2-4 coil + feed |
| J102 signals | Phoenix **1771017** PTSM 0,5/8-2,5-V THR, 8 pole, push-in, vertical | 26-20 AWG | 1 crank (VR+/Hall), 2 GND, 3 AUX1, 4 AUX2, 5 GND, 6 GPS +3.3 V, 7 GPS TX, 8 GPS RX |

Strip, push in until it locks; press the release to remove. **J201 pin order changed in Rev E** (feed moved to pin 6, next to the battery terminal) so each coil terminal lines up with its own IGBT.

## Sheets
| Page | File | Content |
|---|---|---|
| 1 | `MotoNode_ignition.kicad_sch` | Root: hierarchy and overview |
| 2 | `supply_hv_cdi.kicad_sch` | Supply entry, 5 V drive rail, 3.3 V buck, 350 V flyback, CDI discharge |
| 3 | `output_4ch.kicad_sch` | 12 V high-side feed, 4 TCI IGBTs, CDI low side, shunts, quad current sense |
| 4 | `control_safety.kicad_sch` | ESP32-S3-MINI-1, interlock logic, over-current and dwell limits, comparators, safety chain |
| 5 | `hub_sensors.kicad_sch` | **New:** J102, protected AUX inputs, GPS port (PTC-fed 3.3 V, series R + clamps), MPU-6050 (I2C 0x68) |

ESP32 pins added for the hub: IO47 SDA, IO48 SCL, IO42 IMU_INT, TXD0/RXD0 GPS, IO35/IO36 AUX1/AUX2 (the module is the N8 variant, no octal PSRAM, so IO35-37 are free).

## Other files
| File | What it is |
|---|---|
| `fab/` | Gerbers (6 copper layers), Excellon drill (PTH/NPTH) + drill map, pick-and-place CSV, STEP model, 3D renders, per-layer PDFs |
| `MotoNode_ignition_BOM.csv` | Refs, value, MPN, manufacturer, footprint, price: **241 parts, $30.08** at qty 100 (components only). Above the $25 target, mainly the push-in terminals (~$4.80) and the IMU. |
| `MotoNode_ignition_schematic.pdf` | All sheets, plotted by KiCad 10.0.6 |
| `SIMULATION.md` + `spice/` | SPICE validation (Rev D2 circuits; the hub adds only low-voltage sensor parts) |
| `VERIFICATION.md`, `VERIFICATION_footprints.md` | What was checked, how, and what still needs a human check |
| `pcb_layout/` | The layout scripts (placement, hand routes, fan-out, staged routing, finishing router) |
| `reports/` | ERC / DRC reports, netlists, logs |

## Regenerating
`netlist.py` is the single source of truth for the schematic; `kfinal.py` rebuilds the schematic, libraries and an unrouted placement and re-runs every check. The routed board in this folder comes from `pcb_layout/` and is the master for layout: if you change the netlist, use KiCad's "Update PCB from Schematic" on this board rather than regenerating it.

Earlier change history (Rev D -> D1 -> D2) is in `REVISION_HISTORY.md`.
