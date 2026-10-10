# ECLIPSE: design notes

## 1. Concept

ECLIPSE has no shade, no lens and no visible LED. **All of its light comes out through
the material of its body**:

* **A glowing halo body.** The 212 mm ring is moulded from light-diffusing PMMA (volume
  scattering, PLEXIGLAS Satinice / LED-grade opal type). It is an inverted U: 4 mm floor,
  5.4 mm side walls, and a 15 mm air chamber where the light mixes. The LED board closes the
  top and fires down into it. The floor carries most of the light, giving a soft, even task
  pool. The walls glow too, brightest near the underside and fading toward the dark cap, so
  the halo reads as a ring of light with a "corona", not a lamp head.
* **A dark cap, a brass arc.** A thin graphite aluminium cap (also the heatsink) stops
  up-light and carries the hinge knuckle. A single Ø12 mm brass-tone tube rises from the
  back of the base and turns forward in one R90 bend.
* **A base that glows from inside.** A 7 mm band of the same opal material separates the
  graphite upper shell from the steel plinth. Inside, 8 warm LEDs on the core board's rim fire
  down onto the white powder-coated weight. That cavity works as an integrating light chamber
  and the band glows evenly all the way round. It is used as a breathing night-light and as
  touch feedback.
* **A calm interface.** A flush 52 mm smoked-glass window with an etched ring: slide around
  it for brightness, tap the centre for on/off, hold and slide for colour temperature,
  double-tap for the night-glow.

## 2. Mechanical architecture

| Part | Notes |
|---|---|
| Upper shell | 6061, z = 10-22 mm: 3 mm touch skin, 6 mm wall, stem socket boss with an M4 set screw, harness slot, USB-C pocket + slot (right side), 3 M3 PCB bosses. Its interior is painted matte white |
| Core PCB | Pressed against the underside of the skin, so the copper electrodes sit right under the 3 mm glass. All parts are on the bottom face, including 8 rim glow LEDs firing down |
| Glow band | Light-diffusing PMMA ring, Ø148 / Ø138 × 7 mm, clamped between the shell and the plinth |
| Weight / reflector | Ø110 × 6.5 mm steel (≈0.48 kg), white powder coat. It leaves an annular light chamber (r 55-69 mm) behind the band |
| Plinth | 3 mm steel plate (≈0.42 kg) with 3 welded posts; 3 × M3 countersunk screws pull it up into the shell and clamp the band. Black powder coat, with a cork ring underneath |
| Stem | 12 × 2 mm 6063 tube, bent R90. It carries the 10-wire PTFE harness inside |
| Hinge | The yoke is clamped on the tube end. A Ø4 shoulder-screw pin with 2 wave washers sets the friction, and the brass knob is the screw head |
| Halo cap | 3 mm graphite aluminium ring with a rear hood (covers the PCB connector tab) and the knuckle. The halo PCB is screwed to it (4 × M2.5) over a 0.5 mm gap pad, so the cap is the heatsink |
| Halo body | Hollow light-diffusing PMMA ring, 22 mm tall, 9 mm radius on the lower edges, rear notch for the connector. 6 × M2 screws into the cap |

**Stability** (from CAD volumes): total ≈1.69 kg, centre of gravity 35 mm in front of the
base centre, so 40 mm behind the front edge of the base. Tipping it forward needs ≈8 N
pressed down on the centre of the halo. A solid (not hollow) body would have weighed 405 g
and brought the CoG to within 17 mm of the edge. That is why the body is an inverted U and
the plinth is steel.

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
                                                         GLOW_PWM ─► AO3400A ─► 8 rim LEDs → light chamber → opal band
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

About 6 W of heat goes into the cap; the PMMA body is a poor conductor and is not counted. The
cap's exposed area (top, edges and hood) is ≈0.022 m². With h ≈ 10 W/m²K (still air plus
radiation from anodised aluminium), ΔT ≈ 27 K, so the cap runs at about 52 °C in a 25 °C
room. The LED Tj is around 65 °C. The LEDs sit 0.7 mm from the PMMA, so the body's inner face
reaches roughly 55-60 °C. That is inside PMMA's long-term limit (about 80 °C) but with limited
margin, so the NTC derating now starts at 60 °C (ADC ≈ 0.80 V with a 10 k pull-up). If the
prototype runs hotter, use LED-grade polycarbonate (≈120 °C) or reduce the 8.5 W cap.

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
| PC0 | GLOW_PWM (TCD0 WOC) | → AO3400A gate (100 Ω, 100 k pull-down): 8 rim LEDs that light the base band |
| PB3-PB5, PC1-PC3 | spare | no-connect |

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
* The glow dot and the base band breathe at a few percent while off, as a locator.
  Double-tap the key for a steady night-glow, and the band briefly brightens on each touch.
* Protection: 5 V-only supply → 25 % cap. NTC above 60 °C → linear derate to 30 % at 75 °C.
* Toolchain: megaTinyCore or the bare AVR-GCC + Microchip QTouch library (PTC), programmed
  over UPDI.

## 5. Assembly sequence

1. SMT both boards (core: bottom side only, plus the glow LED on top; halo: top side).
2. Bond the glass into the base window (UV-curing glass adhesive, flush ±0.05 mm). Mask the
   window, then paint the shell interior matte white.
3. Fit the core PCB against the skin with 3 × M3 screws. Its top face must touch the glass.
4. Pull the harness through the stem and fit the stem into the socket (M4 set screw + a drop
   of threadlocker). Plug in J2.
5. Drop in the white weight, seat the opal band, then pull the plinth up with 3 × M3
   countersunk screws to clamp the band. Fit the cork ring.
6. Halo: gap pad, PCB onto the cap with 4 × M2.5, plug the harness into J1 through the
   knuckle channel, then fit the glow body to the cap with 6 × M2. Keep fingerprints off the
   inside of the body.
7. Hinge: pin through the yoke and knuckle, 2 wave washers, then the knob. Torque it so the
   halo holds any angle.

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
* **Thermal.** Measure on a prototype. The numbers above are hand estimates, and the PMMA
  temperature margin is the main thing to confirm (see §3.4).
* **Optics.** Choose the PMMA diffuser grade for luminance uniformity versus transmission.
  Hot spots from the 14 mm LED pitch should vanish at a 15 mm throw with a strong diffuser.
  Check the side-to-floor brightness ratio on a moulded sample.
* **Glow LEDs.** Confirm the 2835 part number and 2700 K bin, and check the band's
  uniformity around the 3 posts and the USB-C pocket.
* **DFM.** Die-cast draft angles and the parting line on the halo; the stem bend tooling.
  Glass-to-PCB contact tolerance matters for touch sensitivity.
* The BOM prices are budgetary estimates.
* The 3D models for the 3030 LED and the JST-PH SMD connector are simplified project models
  (KiCad ships none).
