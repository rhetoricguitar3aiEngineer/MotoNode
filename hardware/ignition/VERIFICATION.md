# Verification: Rev E KiCad 10 project

Every result below was produced by the scripts and re-run as one pipeline (`kfinal.py` for the schematic side, `pcb_layout/` + KiCad 10 DRC for the board). Raw reports are in `reports/`.

## Results
| # | Check | Tool | Result |
|---|-------|------|--------|
| 1 | Connectivity sanity: nets declared, >= 2 pins per net, unique designators | `check_netlist.py` | PASS |
| 2 | Voltage rating of every part against worst-case stress (incl. transformer working voltage) | `check_netlist.py` | PASS |
| 3 | Interlock and safety chain: 65,536 states x 16 invariants, reset and firmware-hang cases | `check_netlist.py` | PASS |
| 4 | ESP32-S3 pin rules (flash/PSRAM, strapping, USB, ADC1-only analog, pull-downs); hub pins IO35/36/42/47/48, TXD0/RXD0 | `check_netlist.py` | PASS |
| 5 | HV fault injection: 10 source cases (+/-) x 346 single faults | `check_netlist.py` | PASS, one accepted residual (Q201 short in CDI mode, as in Rev D) |
| 6 | Drawing ERC on all 5 sheets | `kengine.py` | 0 issues |
| 7 | **KiCad ERC** (`--severity-all`) | KiCad 10.0.6 | **0 errors, 0 warnings** |
| 8 | **Netlist parity** schematic vs `netlist.py`, pin for pin | KiCad 7.0.11 + 10.0.6 + `kparity.py` | **144/144 nets, 241 parts, 0 differences** |
| 9 | **Board DRC with schematic parity** | KiCad 10.0.6 `pcb drc --severity-all --schematic-parity` | **0 errors, 0 unconnected items, 0 schematic-parity issues**; 1 warning (`lib_footprint_mismatch` on the Espressif U302 footprint). Report: `reports/drc_kicad10_routed.rpt` |
| 10 | HV creepage on the board | custom rules in `.kicad_dru`, enforced by the DRC above | 2.5 mm outer / 0.5 mm inner HV-to-LV, 1.0 mm HV-to-HV |
| 11 | STEP export of the routed board | KiCad 10.0.6 | 280 solid bodies, 0 model problems (`fab/MotoNode_ignition.step`) |
| 12 | Footprints vs datasheets (38 footprints) | `fpcheck.py` -> `VERIFICATION_footprints.md` | 11 PASS, 23 PASS\*, 4 CHECK |
| 13 | Pinouts vs datasheets (39 multi-pin parts incl. MPU-6050) | `fpcheck.py` | 39 PASS |
| 14 | BOM under $25 | `kbom.py` | **$30.08: over target** (push-in terminals, IMU) |
| 15 | SPICE validation (CDI, flyback, TCI, safety chain, high side, crank input, supply transients) | ngspice 42 | see `SIMULATION.md` (Rev D2 circuits; unchanged in Rev E) |

## Check before ordering boards
1. **Push-in terminal hole patterns and wire-entry side.** J101/J201 footprints were drawn from the Würth 4067B drawing (pitch 5.0, rows 8.2, 1.2 mm drill); the wire-entry side was read from a first-angle side view: confirm on a sample that the wire enters from the board edge. J102 uses KiCad's Phoenix PTSM V-THR footprint: confirm against the 1771017 drawing.
2. **GPS module supply.** J102 pin 6 is 3.3 V through a 0.2 A PTC: use a NEO-6M breakout that runs from 3.0-3.3 V (most have a 3.3 V LDO that needs >= 3.6 V; bypass it or pick a 3.3 V-input board).
3. **T101 EFD15** footprint letter keys and the transformer design itself (custom-wound).
4. **F101 ATO holder** against Littelfuse 178.6164.0001.
5. **T102 WE-AGDT** row spacing and secondary dot.
6. **LEDs D107/D301** cathode mark of the part ordered.
7. Pin numbers taken from the KiCad library: SUD50P06-15, CSD19537Q3, AO3400A/AO3401A.
8. **Via-in-pad**: a few ground pins of U202, U307, U401 use 0.3/0.15 mm filled + capped vias. Order with "via-in-pad / epoxy filled, capped" (free on JLCPCB 6-layer).
9. **Approximate 3D bodies** for the terminals, ATO holder, WE-AGDT, EFD15 and SRN5040: clearance only.
10. **Prices marked `est`** in the BOM (Würth terminals, T101, T102).

## Not verified
- The flyback transformer design (T101 custom-wound; simulation assumes 10 uH, 1:15, k 0.99).
- Thermal behaviour of the output stage and planes; EMC.
- Signal integrity of the autorouted logic (all low-speed except USB-less ESP32 I/O; no length matching was needed).
- ISO 16750-2 load dump and 24 V jump start (simulated: **fails**, see `SIMULATION.md`).
