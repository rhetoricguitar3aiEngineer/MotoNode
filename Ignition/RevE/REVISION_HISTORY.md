# Revision history

## Rev E (this release)
- Hub merged onto the ignition board: MPU-6050 IMU (U401), NEO-6M GPS port (PTC F401, series resistors + BAT54S clamps), two protected OEM-sensor inputs (47k + 100k + 1 nF + BAT54S), new sheet `hub_sensors.kicad_sch`.
- All wiring on tool-less push-in terminals: J101 Würth 691406710002B, J201 Würth 691406710006B, J102 Phoenix 1771017 (replaces the Mini-Fit Jr headers).
- J201 pin order: feed moved from pin 2 to pin 6; coil (-) terminals are now pins 2-5.
- Routed 6-layer board, 100 x 70 mm.
- Net classes: HV clearance 2.5 mm (outer) / 0.5 mm (inner); new class Gnd for GND/PGND; shunt and sense nodes (HS_SNS, I_SH1-4, BST_S) moved from Power to Default (their high-current copper is drawn wide by hand).
- DRC rules: floating-pad, SCR-gate and HV-LED exemptions documented in the .kicad_dru.

## Rev D2 (fixes from the SPICE simulations)
| Fix | Change | Why |
|---|---|---|
| A | Q207 CDI low side NGD8201N -> BT151S-800R SCR; new Q208 BC817-40 gate driver (R213 1k, R214 100R), R223 100R + C207 100 nF gate hold-off, D211 US1M anti-parallel | IGBT desaturated at 55-80 A; hold-off stops a dv/dt latch when CH1 runs as TCI |
| B | R202 2.2k -> 1.5k (1206), R203 4.7k -> 1k | Q201 had only 2.8 V VSG at 9 V: a short never tripped |
| C | Peak-hold D311 / C327 10 nF / R342 470k on I_HS; R313 1k -> 33k; C326 22 nF on HS_EN | HS trip released as soon as current fell: 20-30 us retry loop into a short |
| D | R121 36k -> 42.2k; R108 21.5k -> 19.6k, R104 10k -> 4.7M, C110 100n -> 1n; R113 10k -> 2.7k; R141 470R 1 W + C121 100 pF 1 kV snubber on D106 | 404 V overshoot, Q102 and D106 at their ratings |
| E | U306/U307/U308 VCC +3V3 -> VDRV; C321-C323 to VDRV; R326 20k -> 40.2k | LM339 input common-mode range at 3.3 V excluded the 1.6 V thresholds when hot |
| F | D116 SMBJ33CA on VBAT_F | ISO 7637-2 pulse 1 put Q101 at 60 V |
| G | JP302 + R341 10k (CRANK_F pull-down for Hall sensors) | Hall input never crossed the threshold |
| H | D110 US1M (SMA) -> ES3J (SMC) | 6-14 mJ per spark in a 1 A SMA diode |

Requirements: CDI coil primary >= 100 uH; firmware latches off (stops WDI) when ARM_OK drops unexpectedly; Hall sensor = close JP301 and JP302. Open limitation: 24 V jump start / ISO 16750-2 load dump (see `SIMULATION.md`).

## Rev D1 (datasheet checks)
U101 78L05 SOT-89 pinout fixed; real MP2459 3.3 V buck; Q102 -> CSD19537Q3; T102 -> Würth 750319331 (567 V rms working); C101 -> EEE-FK1V101P (8 x 10); BAT54WS / 1N4148WS part numbers; R201 -> Bourns CSS2H-2512K-2L00F (5 W); NTC B25/50 3380 K; ESP32-S3-MINI-1 with all 65 pads; footprints for SOT-23, SC-70-6, SOIC-8, 2512 shunts and SMC rebuilt from datasheet land patterns; VSON-8 NexFET pitch corrected.
