# MotoNodeIQ: Front Module, Central Hub, Rear Module

Three KiCad 10 projects for a distributed motorcycle body-electronics system
(sized for the 2003 Suzuki Katana 600, usable on most 12 V bikes):

| Board | Folder | Size | Job |
|---|---|---|---|
| **Central Hub** | `hub/` | 76.2 x 50.8 mm (3 x 2 in) | Battery input, smart-fused feeds to the front and rear modules and the ignition controller, starter-relay drive, aux output, key / neutral / side-stand / oil inputs, hardware kill gate, GNSS, IMU, power latch |
| **Front Module** | `front/` | 76.2 x 50.8 mm (3 x 2 in) | Headlight low/high, front turn signals, horn, aux output; 12 handlebar-switch inputs; front wheel speed |
| **Rear Module** | `rear/` | 76.2 x 50.8 mm (3 x 2 in) | Tail, brake, rear turn signals, plate light, aux output; rear brake switch, rear wheel speed, fuel level, two spare inputs |

All three boards are Rev B, built to a 2 x 3 inch maximum outline. Rev A (120-135 mm
boards, Mini-Fit Jr connectors) was replaced; the Rev B changes are listed under
"Rev B (2 x 3 inch) changes" below.

**Status: designed, not built.** Nothing has been bench-tested. Read
"Before you order" below.

| Check (KiCad 10.0.6) | Hub | Front | Rear |
|---|---|---|---|
| Board outline | 76.2 x 50.8 mm | 76.2 x 50.8 mm | 76.2 x 50.8 mm |
| Footprints / nets | 128 / 82 | 134 / 89 | 119 / 75 |
| ERC violations | 0 | 0 | 0 |
| Schematic vs model netlist (exported and compared net by net) | exact | exact | exact |
| Routed: tracks / vias | 431 / 277 | 408 / 233 | 327 / 186 |
| DRC violations / unconnected / schematic-parity errors | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

The schematics are written in KiCad 9 file format, which KiCad 10 opens
directly and upgrades on save. The boards are KiCad 10 native.

## System

```
 battery ──30 A fuse──► HUB (J1 XT60) ──FRONT_FEED + CAN + KILL_HW──► FRONT (J1)
                         │  └─────────REAR_FEED  + CAN ────────────► REAR  (J1)
                         └─ J4: IGN_FEED ─► ignition controller (MotoNode Rev D2)
                               STARTER ─► OEM starter relay coil
                               CAN tap  ─► ignition controller (for a future CAN rev)
```

* **Bus:** CAN 2.0B at 500 kbit/s. Each board has an ESP32-S3 (TWAI controller)
  and a TJA1051TK/3 transceiver (5 V bus side, 3.3 V logic, ±58 V bus pins).
  The ESP32-S3 controller is classic CAN only, not CAN FD; the transceiver
  would carry FD if a later MCU needs it. The front and rear modules are the
  bus ends: their termination jumper JP251 is bridged by default. On the hub,
  which sits mid-bus, it is open.
* **Power:** every board takes VBAT through a 600 W bidirectional TVS
  (SMBJ24CA), feeds its PROFET switches straight from VBAT, and feeds its logic
  through an SS14 reverse-block diode, then an LMR51430 buck (5 V, 500 kHz),
  then an AP2112K LDO (3.3 V).
* **Hub power latch:** the key line starts the hub's buck. Firmware drives
  HOLD (IO15) high at boot and releases it after key-off housekeeping, so the
  hub draws ~0 mA when parked. The front and rear modules are powered only
  while the hub enables their feeds.
* **Outputs:** Infineon PROFET+2 smart high-side switches, wired per
  Infineon's application diagram (R_IN / R_DEN 4.7 k, R_GND 47 R, C_VS 100 n,
  C_OUT 10 n). Current sense uses R_SENSE 2.7 k, then 4.7 k + 1 nF into the
  ADC, with a BAT54C clamp to 3V3. One DIAG_EN line per board enables the
  diagnosis outputs. A fault current reads above 3 V, which saturates the ADC.

  | Switch | R_DS(on) | I_L(NOM) | kILIS | ADC volts per amp |
  |---|---|---|---|---|
  | BTS7008-1EPP | 8.8 mΩ | 11 A | 14 800 | 0.18 V/A |
  | BTS7004-1EPP (hub feeds) | 4.4 mΩ | 15 A | 20 000 | 0.135 V/A |

* **Inputs:** switch-to-ground lines get a 4.7 k wetting pull-up to VBATP and
  a 10 nF filter, then one half of an MUN5211DW1 (a 50 V NPN with built-in
  bias resistors). The MCU pin uses its internal pull-up and reads **LOW while
  the line is high** (switch open). KEY_IN works the other way: it is +12 V
  when on, with a 10 k pull-down.
* **Kill switch (hardware):** the handlebar kill switch closes KILL_HW to GND
  in RUN. The line runs through the front module to the hub. There, Q401B
  pulls the IGN_FEED switch's IN pin low whenever the line is open, whatever
  the firmware does. A broken wire or unplugged connector also stops the
  engine.

## Connector pinouts

Every harness connector is Molex Micro-Fit 3.0 (3.0 mm pitch, vertical through-hole,
about 5 A per contact with 18 AWG crimps). The larger Mini-Fit Jr parts did not fit
the 2 x 3 inch outline. Pin 1 is marked by the square pad; pins 1..n run along the
first row and continue on the second.

**Trunk, hub J2 / J3 to module J1** (Micro-Fit 2x5, 43045-1012). The front and
rear trunks use the same pinout. Three contacts share the feed (15 A).

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | FEED (VBAT) | 6 | GND |
| 2 | FEED (VBAT) | 7 | GND |
| 3 | FEED (VBAT) | 8 | GND |
| 4 | CANH | 9 | KILL_HW (front only) |
| 5 | CANL | 10 | n.c. |

**Hub J1:** XT60, pin 1 = VBAT, pin 2 = GND. Fuse the battery lead at 30 A.

**Hub J4, vehicle** (Micro-Fit 2x6, 43045-1212)

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | IGN_FEED | 7 | CANH (ignition tap) |
| 2 | IGN_FEED | 8 | CANL (ignition tap) |
| 3 | STARTER relay coil | 9 | SIDESTAND switch |
| 4 | AUX_OUT | 10 | OIL pressure switch |
| 5 | KEY (+12 V when on) | 11 | AUX IN 1 |
| 6 | NEUTRAL switch | 12 | AUX IN 2 |

**Front J2 / Rear J2, loads** (Micro-Fit 2x6, 43045-1212): pins 1-6 are the
outputs (one contact each, 5 A), pins 7-12 are GND.

* Front: 1 HEAD_LO, 2 HEAD_HI, 3 TURN_LF, 4 TURN_RF, 5 HORN, 6 AUX_F.
* Rear: 1 TAIL, 2 BRAKE, 3 TURN_LR, 4 TURN_RR, 5 PLATE, 6 AUX_R.

**Front J3, handlebar switches** (Micro-Fit 2x7, 43045-1412)

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | HI beam | 8 | KILL (closed = RUN) |
| 2 | PASS | 9 | CLUTCH |
| 3 | TURN L | 10 | FRONT BRAKE |
| 4 | TURN R | 11 | FRONT SPEED (Hall, OC) |
| 5 | TURN CANCEL | 12 | AUX |
| 6 | HORN | 13 | +5 V sensor (200 mA PTC) |
| 7 | START | 14 | GND |

**Rear J3, sensors** (Micro-Fit 2x4, 43045-0812)

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | REAR BRAKE | 5 | FUEL sender (330 R bias from 5 V) |
| 2 | REAR SPEED (Hall, OC) | 6 | +5 V sensor |
| 3 | AUX 1 | 7 | GND |
| 4 | AUX 2 | 8 | GND |

**Programming, all boards:** Tag-Connect TC2030-NL pads. Pinout: 1 n.c.
(power the board from its 12 V input while programming), 2 USB D-,
3 USB D+, 4 IO0 (rear only; n.c. on the hub and front), 5 GND, 6 EN. Native-USB flashing needs no IO0:
a blank chip boots into download mode, and esptool resets running firmware over
USB-Serial-JTAG. The BOOT button covers the rest. Every board also has RESET and BOOT buttons
and a green status LED.

## GPIO maps (ESP32-S3-WROOM-1-N8, no PSRAM, so IO35-37 are free)

| Function | Hub | Front | Rear |
|---|---|---|---|
| PROFET IN (ch 1..n) | IO11, IO12, IO13, IO14, IO21 | IO11, IO12, IO13, IO14, IO21, IO47 | IO11, IO12, IO13, IO14, IO21, IO47 |
| PROFET sense ADC (ch 1..n) | IO4, IO5, IO6, IO7, IO9 | IO4, IO5, IO6, IO7, IO9, IO10 | IO4, IO5, IO6, IO7, IO9, IO10 |
| DIAG_EN | IO18 | IO18 | IO18 |
| CAN TX / RX | IO16 / IO17 | IO15 / IO16 | IO41 / IO42 |
| VBAT monitor (100k/20k) | IO2 | IO2 | IO2 |
| Status LED | IO43 (TXD0: flickers during the ROM boot log) | IO8 | IO39 |
| Board-specific | HOLD IO15, KILL_DET IO41, KEY IO35, NEUTRAL IO36, SIDESTAND IO37, OIL IO38, AUX1 IO39, AUX2 IO40, GPS TX→ IO1 / RX← IO44, I2C SDA IO47 / SCL IO48, IMU_INT IO8 | HI IO42, PASS IO41, TURN_L IO40, TURN_R IO39, CANCEL IO38, HORN IO37, START IO36, KILL IO35, CLUTCH IO44, FBRAKE IO1, FSPEED IO3, AUX IO17 | RBRAKE IO35, RSPEED IO36, AUX1 IO37, AUX2 IO38, FUEL ADC IO1 |

The channel order follows the output tables in `generator/hub.py`,
`front.py` and `rear.py`. The IN pins run along the module's bottom edge, and
the ADC pins run down its left side, both in channel order. That order lets both
buses reach the compact switch row without crossing.

## Board construction

* 4 layers, 1.6 mm, 1 oz on all layers. F.Cu carries signals and pours. In1
  is a solid GND plane. In2 is split: +3V3 under the logic, VBAT under the
  power section. B.Cu carries signals and a GND pour.
* Design rules: 0.15 mm signal tracks, 0.125 mm clearance, 0.5 / 0.25 mm
  signal vias (a standard 4-layer process at the usual fabs; no HDI); 0.3 to
  0.4 mm power tracks, 0.2 mm clearance on power and load nets. Outputs run as 1.2 to 1.5 mm tracks from a collector pour.
  The hub feeds are F.Cu pours, 6 to 9 mm wide, from each PROFET collector
  straight down over their connector pins.
* Passives are 0402 except where rating or value needs more (pull-ups 0603,
  10 µF 0603, 22 µF 0805, 4.7 µF 1206, fuel bias 330 R 0805).
* Parts on both sides: R_IN and R_DEN of every switch, the BAT54C ADC clamps
  the RESET / BOOT buttons, the CAN termination parts and (hub) the IMU are on
  B.Cu, the buttons and IMU under the ESP32 module. Order double-sided assembly.
* Each switch cell is 7.5 mm wide. R_ADC, R_SENSE and R_GND are on top, and
  R_IN and R_DEN directly beneath them on the bottom. The IN lines arrive on
  B.Cu, the sense lines on F.Cu, and the DIAG_EN bus runs on B.Cu between the
  resistor row and the switches.
* Each PROFET exposed pad (VS) sits on an F.Cu VBAT strip, with 6 vias in the
  pad and two 0.8 mm vias beside it down to the In2 VBAT plane. The in-pad
  vias must be **filled or capped** (order "via-in-pad, plugged").
* ESP32 antenna: the module sits on the top edge, with the footprint's 15 mm
  keep-out (no copper on any layer) honoured.
* GNSS (hub): MAX-M10S with a u.FL for an active antenna. A 3.3 V bias
  reaches the antenna through 10 R + 47 nH from VCC_RF. The RF trace is
  0.36 mm (about 50 Ω over the In1 GND plane, 0.21 mm prepreg); check this
  against your fab's stack-up.

## Files (per board folder)

| Path | Content |
|---|---|
| `MotoNodeIQ_*.kicad_pro / .kicad_sch / .kicad_pcb` | KiCad project: root sheet plus 4-5 hierarchical sheets, routed board |
| `fab/*_gerbers.zip` | Gerbers (11 layers) and Excellon drill files with a drill map |
| `fab/*_BOM.csv` | Grouped BOM with MPN and manufacturer |
| `fab/*_pos.csv` | Pick-and-place |
| `fab/*_schematic.pdf`, `fab/*_3d_top.png`, `fab/*_3d_bottom.png`, `fab/*.step` | Documentation and 3D |
| `reports/erc.json`, `reports/drc.json`, `reports/netlist.xml` | Check results |

## Regenerating

Everything comes from Python in `generator/`. The netlist modules
(`hub.py`, `front.py`, `rear.py`, `blocks.py`) are the single source of truth.

```bash
cd generator
python build.py hub front rear     # schematic + ERC + parity, place, route, fill, DRC
python fab.py hub front rear       # fabrication outputs
```

* `schgen.py` writes the schematics from the KiCad 10 standard symbol libraries.
* `pcbgen.py` (run with KiCad's own Python) places the footprints from the
  `layout_*.py` files and draws the zones.
* `router.py` is a purpose-built grid router (numpy, scipy, shapely). It
  routes every net, including plane fan-outs, and passes KiCad DRC at nominal
  clearance.
* `pcbfinish.py` imports the routes and fills the zones.
* `drc.py` runs KiCad DRC with schematic parity.
* `build.py` runs the whole chain.

If you edit the boards in KiCad, treat the KiCad files as the master from then
on. Re-running the generator overwrites them.

## Before you order

1. **Bench-validate one board first.** Nothing here has been built.
2. **MUN5211DW1 pinout.** The KiCad library maps it E1-B1-C2-E2-B2-C1, the
   standard SOT-363 dual-transistor order. Confirm it against the onsemi
   datasheet; every input depends on it.
3. **Brake and turn lights depend on firmware.** No hardware path drives them
   if the MCU hangs. Run the ESP32 task watchdog. The modules should fall back
   to *tail and brake on* when CAN from the hub goes silent.
4. **Starter:** keep the OEM clutch / neutral interlock in series with the hub's
   STARTER output. The hub's own interlock is firmware.
5. **Current:** the connectors set the limits, not the switches. Each module
   output has one Micro-Fit contact (5 A): a 55 W H4 low beam (4.6 A) fits,
   but a 100 W bulb does not. Each trunk carries 15 A on three contacts. The hub
   feeds share one 3.2 mm VBAT strip plus the In2 plane; 25 A combined is the
   practical ceiling. Fuse the battery lead at 30 A.
6. **24 V jump starts** are outside the SMBJ24CA / PROFET ratings (35 V
   suppressed load dump only). The 600 W SMB TVS is smaller than Rev A's
   1500 W part. It suits a bike with a working regulator; add a central load-dump
   suppressor if the charging system is suspect.
7. Silkscreen reference designators overlap in dense areas. This is cosmetic;
   tidy them in KiCad if you care.
8. Via-in-pad under the PROFETs needs filled vias (see Board construction).
9. The schematics are generated: each pin ends in a labelled stub instead of
   drawn wires. They are electrically checked but read more like a netlist
   than a hand-drawn sheet.
10. The boards are full: 0402 parts at 0.2 mm track / 0.15 mm clearance, with
    no spare area. Any added part means re-running `build.py`, which places,
    routes several seeds in parallel (`--seeds N`) and keeps the best.

## Rev B (2 x 3 inch) changes

* Outline 76.2 x 50.8 mm on all three boards (was 115-135 x 85-98 mm). Two
  M2.5 holes per board (was four).
* Connectors: Mini-Fit Jr trunk / loads / vehicle replaced by Micro-Fit 3.0
  (pinouts above). Front J3 is now 2x7 (was 2x8: GND pins 15-16 dropped).
* TVS SMCJ24CA → SMBJ24CA; bulk capacitor → 47 µF 35 V (6.3 x 7.7 mm); buck
  inductor → Coilcraft XAL4030-682 (4 x 4 mm); CAN transceiver → TJA1051TK/3
  (HVSON-8); polyfuse → 0805; buttons → C&K KMR2.
* Programming-port Schottky D201 removed: power the board from its 12 V input
  while programming (TC2030 pin 1 is now n.c.).
* GPIO maps changed (table above) so the switch control and sense buses stay
  planar on the compact layout.
* Hub J4 pinout changed: CAN tap moved to pins 7-8, inputs to 9-12.
