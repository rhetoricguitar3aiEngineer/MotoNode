# ECLIPSE: design notes

## 1. Concept

Most LED desk lamps are a bar or a disc on an arm. ECLIPSE reduces the lamp to two lines,
a brass arc and a graphite ring:

* **A halo, not a head.** The light-emitting element is an open ring. You see the desk through
  the middle of it, and from the seat it reads as a thin line of light rather than a glaring
  panel. An annular source also throws softer, less directional shadows than a compact head.
* **One gesture for the structure.** A single Ø12 mm tube rises from the back of the base and
  turns forward in one R90 bend. The halo hangs from its tip on a knurled brass friction hinge
  (±30°).
* **A calm base.** A heavy, low Ø150 puck. The only interface is a flush 52 mm smoked-glass
  window with an etched ring: slide around it for brightness, tap the centre for on/off, and
  hold the centre while sliding for colour temperature. A warm glow dot under the glass gives
  feedback. There are no buttons, no switch and no visible screws.
* **Materials.** Graphite-anodised aluminium (base, yoke, halo), a brass-tone PVD stem, a solid
  brass knob, opal PMMA, glass and cork.

## 2. Mechanical architecture

| Part | Notes |
|---|---|
| Base shell | 6061, turned + milled from bar. 3 mm top skin, 6 mm wall, stem socket boss with an M4 set screw, harness slot, pocket + slot for the right-hand USB-C port, 3 M3 PCB bosses |
| Core PCB | Pressed against the underside of the skin, so the copper electrodes sit right under the 3 mm glass and give strong touch sensitivity. All parts are on the bottom face |
| Weight | 7 mm laser-cut steel disc, ≈0.8 kg. It sits below the PCB with ≥3 mm clearance to the tallest part (JST-PH, 6 mm) |
| Bottom cover + foot | 1.2 mm aluminium cover (4 × M2 countersunk) with a die-cut cork ring |
| Stem | 12 × 2 mm 6063 tube, bent R90. It carries the 10-wire PTFE harness inside |
| Hinge | The yoke is clamped on the tube end. A Ø4 shoulder-screw pin with 2 wave washers sets the friction, and the brass knob is the screw head |
| Halo housing | Die-cast ADC12 + CNC: a 2 mm wall and 2.5 mm top with a fine V-groove accent at r = 96 mm. The knuckle has a harness channel and a pocket for the connector tab |
| Halo PCB | Ring OD200/ID160, screwed (4 × M2.5) LEDs-down against the top skin through a 0.5 mm gap pad. The housing is the heatsink |
| Diffuser | 2 mm opal PMMA ring, recessed 0.5 mm. The LED-to-diffuser distance is about 7 mm, and with a 14 mm LED pitch that hides the individual LEDs |

**Stability** (from CAD volumes): total ≈1.55 kg, centre of gravity 25 mm in front of the
base centre, so 50 mm behind the front edge of the base. Tipping it forward needs ≈0.75 N·m,
i.e. ≈9 N (0.9 kgf) pressed down on the centre of the halo.

## 3. Electronics

### 3.1 Block diagram

```
USB-C ──► PTC 1.5A ──► TVS 15V ──► VIN (9 V) ─┬─► TPS61165 #1 ──► W1 string (10 × 2700 K)
  │                                            ├─► TPS61165 #2 ──► C1 string (10 × 6500 K)   ═══ 10-wire
  └─ CC1/CC2 ─► CH224K (asks for 9 V)          ├─► TPS61165 #3 ──► W2 string (10 × 2700 K)       harness
                                               ├─► TPS61165 #4 ──► C2 string (10 × 6500 K)       through
                                               └─► AMS1117-3.3 ─► ATtiny1616 ◄─ touch key+wheel   the stem
                                                         PWM_W ─► CTRL #1,#3 ; PWM_C ─► CTRL #2,#4
                                                         NTC ◄──────────────── halo thermistor
```

### 3.2 LED drive

* String: 10 × MP-3030-1100. Vf ≈ 2.9 V at 100 mA, so V_string ≈ 29 V (27-31 V spread). That
  is well below the TPS61165's 38 V over-voltage protection, which also covers an open string.
* Current: I = V_FB / R_sense = 200 mV / 2.0 Ω = **100 mA** (20 mW in the resistor).
* Dimming: PWM (19.5 kHz from TCA0) on CTRL. The TPS61165 filters it into its FB reference,
  so the LED current is DC and flicker-free.
* Boost at 9 V in: D ≈ 1 − 9·0.85/29.4 ≈ 0.74, I_in ≈ 0.38 A per string, inductor ripple ≈
  9·0.74/(10 µH·1.2 MHz) ≈ 0.56 A pp, so the peak is ≈0.66 A. That is under the 1.2 A switch
  limit and the 1.6 A Isat of the SRN4018-100M.
* Boost at 5 V in (non-PD port): I_in ≈ 0.69 A per string, peak ≈0.87 A. That's fine per IC,
  but 4 strings would need 2.8 A, so the firmware caps the total duty at 25 % when VSENSE
  reads <6 V.
* Power budget at 9 V: firmware caps the sum of warm and cool duty at 75 % of 11.6 W, i.e.
  ≈8.5 W LED. That draws ≈1.1 A from 9 V, inside an 18 W charger and the 1.5 A PTC.

### 3.3 Halo board layout

The LED pattern is mirror-symmetric about the hinge axis, and the two LEDs next to the hinge
are both warm. Each half holds one warm and one cool string. Every chain link leaves the
cathode radially, runs along a lane and re-enters the next anode: warm lanes at r = 84.5 mm
(inside the LEDs), cool lanes at r = 95.5 mm (outside). The string returns run along
r = 82 mm and r = 98 mm. Nothing crosses, so the board is **single-layer**. Build it as a
1.5 mm aluminium MCPCB (1-2 W/mK) with white mask. All tracks are 0.8 mm.

### 3.4 Thermal

About 6 W of heat goes into the halo. The housing's exposed area is ≈0.034 m². With h ≈ 10 W/m²K
(still air plus radiation from anodised aluminium), ΔT ≈ 18 K, so the housing runs at about
45 °C in a 25 °C room. The LED Tj stays below roughly 60 °C. The NTC (10 k, B3380) on the
halo starts derating at 65 °C (ADC ≈ 0.68 V with a 10 k pull-up).

### 3.5 MCU pin map (ATtiny1616-S)

| Pin | Function | Notes |
|---|---|---|
| PA0 | UPDI | pogo pads J3 (DNP header) |
| PA1 | VSENSE | VIN × 15k/(100k+15k); 9 V → 1.17 V (use the 2.5 V internal ref) |
| PA2 | PD_PG | CH224K power-good (open drain, 10 k pull-up) |
| PA3 | NTC | 10 k pull-up to 3V3, 100 nF filter |
| PA4 | Touch key | PTC Y-line, 1 k series |
| PA5-PA7 | Touch wheel A/B/C | PTC Y-lines, 1 k series |
| PB0 | PWM_W (TCA0 WO0) | → CTRL of U4 (W1) and U6 (W2); 100 k pull-down |
| PB1 | PWM_C (TCA0 WO1) | → CTRL of U5 (C1) and U7 (C2); 100 k pull-down |
| PB2 | Glow LED (TCA0 WO2) | 470 Ω, 0603 white LED under the glass |
| PB3-PB5, PC0-PC3 | spare | no-connect |

### 3.6 Harness (JST-PH 10, 1:1, 520 mm, PTFE AWG28)

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | C1 cathode return | 6 | GND (NTC return) |
| 2 | C1 anode (boost out) | 7 | W2 cathode return |
| 3 | W1 anode | 8 | W2 anode |
| 4 | W1 cathode return | 9 | C2 anode |
| 5 | NTC | 10 | C2 cathode return |

## 4. Firmware behaviour (to implement)

* Tap the key to toggle. The lamp fades on to the last brightness and CCT (stored in EEPROM)
  over 400 ms.
* Slide the wheel for brightness (logarithmic, 1-100 %). Hold the key and slide for CCT
  (2700-6500 K). The warm/cool split keeps total flux constant along the CCT sweep.
* The glow LED breathes at 3 % while off as a locator, and briefly brightens on each touch.
* Protection: 5 V-only supply → 25 % cap. NTC above 65 °C → linear derate to 30 % at 80 °C.
* Toolchain: megaTinyCore or the bare AVR-GCC + Microchip QTouch library (PTC), programmed
  over UPDI.

## 5. Assembly sequence

1. SMT both boards (core: bottom side only, plus the glow LED on top; halo: top side).
2. Bond the glass into the base window (UV-curing glass adhesive, flush ±0.05 mm).
3. Fit the core PCB against the skin with 3 × M3 screws. Its top face must touch the glass.
4. Pull the harness through the stem and fit the stem into the socket (M4 set screw + a drop
   of threadlocker). Plug in J2.
5. Halo: gap pad, PCB with 4 × M2.5, plug the harness into J1 through the knuckle channel,
   press in the diffuser (4 × silicone dots).
6. Hinge: pin through the yoke and knuckle, 2 wave washers, then the knob. Torque it so the
   halo holds any angle.
7. Steel weight, bottom cover (4 × M2), cork ring.

## 6. Verification status and open items

Done and checked automatically:

* ERC is clean and DRC is clean on both boards: 0 violations, 0 unrouted, schematic/PCB
  parity OK.
* The KiCad-exported netlists equal the design description net-for-net (`verify_netlist.py`).
* All CAD solids are valid, and the part fits were checked: PCB-to-skin, LEDs-to-diffuser
  clearance, connector inside the knuckle pocket, and the core PCB notch around the stem boss.

Before ordering or tooling:

* **Datasheet cross-checks.** Check the CH224K VDD (1 k feed) and VBUS pin connection and the
  CFG1 resistor table. Check the TPS61165 SOT-23-6 pinout against the KiCad library symbol and
  footprint. Confirm the polarity of the MP-3030-1100 pads against the KiCad footprint (pad 1
  = cathode).
* **Luminus ordering codes.** Confirm the exact CCT/CRI bin part numbers.
* **Firmware** has not been written yet (behaviour is specified in §4).
* **EMI.** Four free-running 1.2 MHz boosts. Do a pre-compliance scan, then consider
  spread-spectrum or ferrite beads on the harness if needed.
* **Thermal.** Measure on a prototype. The numbers above are hand estimates.
* **DFM.** Die-cast draft angles and the parting line on the halo; the stem bend tooling.
  Glass-to-PCB contact tolerance matters for touch sensitivity.
* The BOM prices are budgetary estimates.
* The 3D models for the 3030 LED and the JST-PH SMD connector are simplified project models
  (KiCad ships none).
