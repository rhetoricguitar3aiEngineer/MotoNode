# SPICE validation - MotoNode ignition controller (Rev D1 -> Rev D2)

Every circuit block that carries energy or implements a safety function was simulated in
ngspice 42 (transient, gear integration). The decks, device models and scripts are in `spice/`;
`python3 spice/run_all.py` re-runs everything (about 3 minutes) and `python3 spice/make_report.py`
rebuilds this file. The simulations found **eight real design faults in Rev D1**. All eight are
fixed in the Rev D2 schematic, and every Rev D2 case below was re-simulated with the fix in place.

## Summary

| # | Block | Rev D1 (as drawn) | Rev D2 (fixed) | Verdict |
|---|---|---|---|---|
| A | CDI low side Q207 | NGD8201N carries 55 A with a 200 uH coil (50 A pulse rating), desaturates to 189 V, 29 mJ per spark | BT151S-800R SCR + BC817 gate driver: 63 A (ITSM 120 A), 3.4 mJ per spark | fixed |
| A2 | Q207 dv/dt in CH1 TCI mode | without a gate hold-off the SCR latches after the IGBT turns off (7.8 A held, no spark) | R223 100 R + C207 100 nF: 16 mA, no latch at 25 and 125 C | fixed |
| B | Q201 12 V high side | gate divider gives VSG 2.8 V at 9 V: a short self-limits at 19 A in the linear region and **never trips** | R202 1.5k / R203 1k: VSG 8.5 V; short trips, 77 A peak, off in 15 us, 8.2 mJ | fixed |
| C | HS trip latch | the trip only lasts while current flows, so HS_EN comes straight back: 189 short pulses in 35 ms, 1.15 J in Q201. An RC delay alone is not enough: with a low-Vth (1.0 V) Q202 it still retried after 0.3 ms | D311/C327/R342 peak-hold stretches the trip ~3 ms: VCP fully dumped, HS_EN <= 0.4 V, chain disarms. 2 pulses in 35 ms (2nd only because the test keeps pumping WDI), also with Vth 1.0 V | fixed (firmware should latch) |
| D | 350 V flyback | overshoots to 404 V (held by the OVP, loop too slow); Q102 104 V (100 V part); D106 rings to 1002 V (1000 V part) | U307C regulates 350 V, UC3845 loop is the 385 V backup; 358 V peak, Q102 68 V, D106 677 V with R141/C121 snubber; R119 open -> 389 V | fixed |
| E | Comparators on 3.3 V | LM339/LM393 input common-mode limit over temperature is VCC - 2 V = 1.3 V, below VTH_OC (1.62 V) and VTH_ARM (1.65 V): the trips are out of spec when hot | U306-U308 on VDRV (5 V), R326 40.2k from VDRV; S3/S4/S5 re-run on 5 V | fixed |
| H | D110 CDI freewheel | US1M (SMA, 1 A) takes 40-65 A peaks and 6-14 mJ per spark: ~1-2 W at 10 000 rpm | ES3J (SMC, 3 A): 81 A peak, 3.6 mJ per spark | fixed |
| F | ISO 7637-2 pulse 1 | Q101 VDS 60 V (60 V part, avalanche) | D116 SMBJ33CA on VBAT_F: 39 V | fixed |
| G | Hall crank sensor | Hall low level never reaches the 0.12 V threshold (R335 hysteresis adds 0.3 V): **0 edges** detected | JP302 + R341 10k (close with JP301 for Hall): all edges at 6 000 and 12 000 rpm | fixed |
| - | Load dump 5b (35 V) / 24 V jump start | SMCJ18A conducts 13 A / 14 A for 400 ms / 60 s (123 J in 400 ms) | unchanged | **open limitation**, see below |

Passed without changes: Q105 SCR discharge path and D109, D202/D203 isolation (175 V each on 600 V
parts), TCI over-current trip (8.1 A) and max-dwell limit (10.9 ms), IGBT clamp (389 V), the ARM safety chain
(arms in 18 ms, drops 275 ms after the watchdog stops, a stuck WDI never arms), flyback inhibit,
VR input from 0.25 V to 120 V amplitude, ISO 7637-2 pulses 2a / 3a / 3b, reverse battery.

## Models and their limits

- **Behavioural / fitted models** (`spice/models.lib`): diodes and MOSFETs fitted to datasheet curves (VDMOS);
  NGD8201N = logic-level VDMOS + 385 V gate clamp + 24 V reverse avalanche; BT151S = two-transistor SCR;
  LM339 = delayed open-collector comparator that goes open when unpowered and flags common-mode violation;
  INA180 / INA186 = gain + bandwidth + output limit; UC3845 = current-mode behavioural (oscillator, latch,
  error amp, 50 % max duty); 74LVC14 / 74AHCT = thresholds + delay. No vendor model was available offline
  for the MP2459 buck, so it is not simulated (checked by hand: VOUT 3.32 V, EN < 6 V).
- **Coils:** coupled inductors with a switch-modelled spark gap (7.5 kV TCI, 6 kV CDI breakdown, 400 R arc).
  CDI coils: 20 uH, 200 uH and a 4 mH TCI coil driven in CDI mode.
- **SCR dv/dt:** the SCR model's dv/dt behaviour comes from its junction capacitances, not a datasheet dv/dt
  figure. The R223/C207 values have margin in the model (gate peaks at 0.58 V, 40 mA displacement current
  for about 1 us, no latch at 25 or 125 C); confirm on the bench with the real coil.
- Thermal behaviour, layout parasitics and EMI are not modelled.

## Design requirements that came out of the simulations

1. **CDI coil primary >= 100 uH.** With a 20 uH primary the SCR di/dt reaches about 95 A/us (BT151S rating
   50 A/us) and peak current about 150 A. 200 uH gives 16 A/us and about 63 A.
2. **Firmware must stop toggling WDI when ARM_OK drops unexpectedly.** The hardware turns Q201 off in
   about 15 us and the peak-hold keeps the trip until the chain is disarmed, but an MCU that keeps
   pumping re-arms after about 19 ms. With a firmware latch there is one short pulse; without it, a hiccup below 1 W.
3. **Hall sensors:** close both JP301 (pull-up) and JP302 (pull-down). VR sensors: both open.
   Minimum VR amplitude is about 0.2 V peak (0.15 V is not detected, 0.25 V is).
4. **Crank input delay** is 13 us at 12 000 rpm (0.9 deg) and 0.7-1.6 ms at cranking (0.9 deg): firmware
   should subtract a fixed ~1 deg. C317 stays at 1 nF: 220 pF passed a 60 V / 1 us ignition spike as a false edge.

## Open limitation: 24 V jump start and ISO 16750-2 load dump

D102 (SMCJ18A) clamps +12V at about 23 V. A 24 V jump start or a 35 V suppressed load dump drives it at
14 A and 13 A for the whole event (123 J in 400 ms): far beyond an SMC
part, which will fail short and blow F101. The board is protected, but the engine stops. Fixing this needs a
front-end change, not a value change: a load-dump TVS (SM8S-class) or a series pre-regulator / surge stopper,
40 V-rated parts downstream (the 78L05 and UC3845 VCC are 30 V parts), and a UC3845 VCC clamp that does not
fight the cranking UVLO. This is left as an open item for Rev E; if the bike will never see a 24 V jump pack
and has a regulator/rectifier with built-in load-dump suppression, Rev D2 is adequate.

## S1 - CDI discharge (C113 350 V -> Q105 -> CH1 coil -> Q207)

| Q207 | Case | Q207 peak A | di/dt A/us | Q207 max V | Q207 mJ/event | COIL1_TOP min V | D110 peak A | D110 mJ/event | D202 V | C113 dv/dt V/us | sec kV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Q207 NGD8201N (D1) | CDI coil 20uH, spark gap | 81 | 96 | 257 | 44.5 | -6.2 | 40 | 1.3 | 169 | 81 | 12.0 |
| Q207 NGD8201N (D1) | CDI coil 20uH, open secondary | 64 | 96 | 152 | 42.7 | -7.5 | 51 | 6.9 | 169 | 62 | 30.7 |
| Q207 NGD8201N (D1) | CDI coil 200uH, spark gap | 55 | 16 | 189 | 28.9 | -6.2 | 40 | 2.7 | 173 | 55 | 12.0 |
| Q207 NGD8201N (D1) | CDI coil 200uH, open secondary | 32 | 16 | 3 | 9.4 | -5.5 | 34 | 13.5 | 173 | 32 | 41.6 |
| Q207 NGD8201N (D1) | TCI coil 4mH, spark gap | 16 | 1 | 2 | 4.7 | -3.4 | 17 | 6.6 | 174 | 16 | 12.0 |
| Q207 NGD8201N (D1) | TCI coil 4mH, open secondary | 10 | 1 | 1 | 7.2 | -2.5 | 10 | 8.1 | 174 | 9 | 50.9 |
| Q207 BT151S SCR (D2) | CDI coil 20uH, spark gap | 151 | 95 | 179 | 6.4 | -8.6 | 182 | 4.9 | 172 | 151 | 12.0 |
| Q207 BT151S SCR (D2) | CDI coil 20uH, open secondary | 85 | 111 | 389 | 43.0 | -4.6 | 83 | 0.3 | 172 | 84 | 36.2 |
| Q207 BT151S SCR (D2) | CDI coil 200uH, spark gap | 63 | 16 | 139 | 3.4 | -4.5 | 81 | 3.6 | 174 | 63 | 12.0 |
| Q207 BT151S SCR (D2) | CDI coil 200uH, open secondary | 36 | 16 | 172 | 6.4 | -3.1 | 46 | 8.3 | 174 | 36 | 41.5 |
| Q207 BT151S SCR (D2) | TCI coil 4mH, spark gap | 16 | 1 | 82 | 3.5 | -2.1 | 21 | 4.6 | 174 | 16 | 12.0 |
| Q207 BT151S SCR (D2) | TCI coil 4mH, open secondary | 10 | 1 | 82 | 4.7 | -1.6 | 10 | 5.9 | 174 | 10 | 50.9 |

Limits: BT151S ITSM 120 A (10 ms), dIT/dt 50 A/us, VDRM 800 V; NGD8201N 50 A pulse; ES2J 600 V;
C113 (TDK B32672P) dv/dt 180 V/us. D211 (new) returns the coil's reverse current to C113 so the SCR is
never reverse biased; the 20 uH coil is outside the new >= 100 uH requirement.

![Rev D1: NGD8201N low side, 200 uH coil - desaturation at 55 A](spice/plots/s1_igbt_200uH_spark.png)
*Rev D1: NGD8201N low side, 200 uH coil - desaturation at 55 A*

![Rev D2: BT151S low side, 200 uH coil](spice/plots/s1_scr_200uH_spark.png)
*Rev D2: BT151S low side, 200 uH coil*

## S1b - CH1 used as a TCI channel: can Q207 (SCR) false-trigger?

| Case | COIL1_BOT dv/dt V/us | clamp V | gate max V | SCR peak A | SCR A after turn-off | latched |
|---|---|---|---|---|---|---|
| CH1 in TCI mode, R223 470 R, C207 omitted, Tj 25 C | 1322 | 389 | 0.89 | 7.81 | 7.81 | yes |
| CH1 in TCI mode, R223 470 R, C207 10n, Tj 25 C | 1326 | 389 | 0.90 | 8.40 | 8.40 | yes |
| CH1 in TCI mode, R223 100 R, C207 47n, Tj 25 C | 1327 | 389 | 0.58 | 0.04 | 0.02 | no |
| CH1 in TCI mode, R223 100 R, C207 100n, Tj 25 C | 1327 | 389 | 0.58 | 0.04 | 0.02 | no |
| CH1 in TCI mode, R223 100 R, C207 100n, Tj 125 C | 1420 | 389 | 0.37 | 0.04 | 0.02 | no |
| CH1 in TCI mode, R223 47 R, C207 100n, Tj 125 C | 1420 | 389 | 0.39 | 0.04 | 0.02 | no |

![No gate hold-off: the SCR latches and carries the coil current, no spark](spice/plots/s1_tcimode_470_1p_25C.png)
*No gate hold-off: the SCR latches and carries the coil current, no spark*

![Rev D2 (R223 100 R, C207 100 nF): no latch](spice/plots/s1_tcimode_100_100n_25C.png)
*Rev D2 (R223 100 R, C207 100 nF): no latch*

## S2 - 350 V flyback charger

| Case | t to 340 V ms | peak V | steady V | Q102 VDS V | D106 reverse V | I batt avg A |
|---|---|---|---|---|---|---|
| Rev D1 as drawn, VBAT 14.4 V | 1.68 | 404 | 400 | 104 | 1002 | 1.92 |
| fixed: normal charge, VBAT 14.4 V | 2.00 | 358 | 354 | 68 | 677 | 3.03 |
| fixed: VBAT 9 V (cranking) | 4.67 | 354 | 351 | 60 | 593 | 2.08 |
| fixed: R105 open (UC3845 feedback lost -> OVP holds) | 2.00 | 358 | 354 | 68 | 677 | 3.03 |
| fixed: R119 open (comparator loop lost) | 2.00 | 389 | 386 | 68 | 774 | 3.03 |
| fixed: BOOST_RUN low (safety chain open) | - | 0 | 0 | 14 | 0 | 0.01 |

Q102 CSD19537Q3 100 V; D106 US1M 1000 V; C113 630 V. At 9 V (cranking) the charger reaches
336 V steady (max-duty limited): spark energy about 57 mJ instead of 61 mJ. The snubber resistor R141
dissipates about 0.9 W while charging, hence a 1 W 2512 part.

![Rev D1: overshoot to ~400 V (OVP holds it), Q102 avalanche](spice/plots/s2_case1.png)
*Rev D1: overshoot to ~400 V (OVP holds it), Q102 avalanche*

![Rev D2: U307C regulates at 350 V](spice/plots/s2_case2.png)
*Rev D2: U307C regulates at 350 V*

## S3 - TCI channel (CH2) end to end

| Case | on time ms | I at turn-off A | VCE max V | clamp energy mJ | sec kV |
|---|---|---|---|---|---|
| 4 mH / 0.6 R coil, 3 ms dwell, spark | 3.00 | 7.89 | 389 | 7.4 | 15.0 |
| 1 mH / 0.3 R coil, 3 ms dwell, spark | 0.69 | 8.14 | 389 | 1.7 | 15.0 |
| 5 mH / 3 R coil, GPIO stuck high | 10.92 | 4.35 | 389 | 2.7 | 15.0 |
| 4 mH / 0.6 R coil, open secondary (clamp) | 3.00 | 7.89 | 389 | 104.3 | 55.4 |

Comparators on VDRV (Rev D2). OC trip set 8 A (VTH_OC 1.62 V); the 10 ms dwell limiter cuts a stuck
GPIO. The open-secondary case puts about 104 mJ into the IGBT clamp per event: check this against the
NGD8201N self-clamped energy rating (ESCIS) for the coil actually used, and add an open-HT-lead check
(coil current without a spark) in firmware.

![4 mH coil, 3 ms dwell](spice/plots/s3_case1.png)
*4 mH coil, 3 ms dwell*

![GPIO stuck high: the C/R limiter ends the dwell at 10.9 ms](spice/plots/s3_case3.png)
*GPIO stuck high: the C/R limiter ends the dwell at 10.9 ms*

## S4 - ARM safety chain (WDI charge pump -> VCP -> U307B -> Q301 -> VDRV_SW)

| Variant | Case | armed after ms | off after event ms | VCP max V | VTH_ARM V |
|---|---|---|---|---|---|
| d1 | pump 1 kHz, then WDI stops (hang) at 300 ms | 18.0 | 276.8 | 3.05 | 1.63 |
| d1 | WDI stuck HIGH from start | - | - | 0.14 | 1.68 |
| d1 | pump 1 kHz, then +3V3 lost at 300 ms | 18.0 | 1.5 | 3.05 | 1.63 |
| d2 | pump 1 kHz, then WDI stops (hang) at 300 ms | 18.0 | 275.3 | 3.05 | 1.64 |
| d2 | WDI stuck HIGH from start | - | - | 0.14 | 1.70 |
| d2 | pump 1 kHz, then +3V3 lost at 300 ms | 18.0 | 275.3 | 3.05 | 1.64 |

d1 = Rev D1 (comparators + VTH_ARM on 3.3 V), d2 = Rev D2 (on VDRV). In d1 a lost 3.3 V rail
disarms at once (comparator unpowered); in d2 the comparator stays powered and the chain drops when the
pump stops (the MCU stops with 3.3 V), 275 ms, same as a firmware hang.

![Rev D2: arm, then firmware hang at 300 ms](spice/plots/s4_d2_1.png)
*Rev D2: arm, then firmware hang at 300 ms*

## S5 - 12 V high-side feed: hard short to chassis on V12_SW

| Case | VSG on V | peak A | trip after us | off after us | Q201 mJ |
|---|---|---|---|---|---|
| Rev D1: R202 2.2k / R203 4.7k, R313 1k, VBAT 14.4 V | 4.5 | 56 | 7.2 | 13.8 | 102.8 |
| Rev D1: R202 2.2k / R203 4.7k, R313 1k, VBAT 9.0 V | 2.8 | 19 | - | - | 24.6 |
| Rev D2: R202 1.5k / R203 1k, peak-hold, R313 33k + C326 22n, VBAT 14.4 V | 8.5 | 77 | 9.8 | 15.4 | 8.2 |
| Rev D2: R202 1.5k / R203 1k, peak-hold, R313 33k + C326 22n, VBAT 9.0 V | 5.3 | 49 | 16.5 | 20.4 | 4.6 |

30 mOhm + 0.5 uH short, battery 15 mOhm + 1 uH. SUD50P06-15: 50 A continuous, 100 A pulse.

## S5b - trip-and-hold through the whole chain (WDI keeps pumping)

| Case | pulses in 35 ms | pulse times ms | HS_EN max after trip V | VDRV_SW off ms | Q201 total mJ | peak A |
|---|---|---|---|---|---|---|
| Rev D1: R313 1k, no C326, no peak-hold | 189 | 0.00, 0.02, 0.04, 0.05, 0.07, 0.08 | 4.95 | 1.83 | 1154 | 68 |
| R313 100k + C326 22n, no peak-hold, Q202 Vth 2.1 V (typ) | 10 | 0.00, 6.10, 9.66, 12.50, 16.83, 20.74 | 2.04 | 1.83 | 93 | 73 |
| R313 100k + C326 22n, no peak-hold, Q202 Vth 1.0 V (min) | 9 | 0.00, 0.31, 0.79, 13.56, 13.79, 14.17 | 1.13 | 1.83 | 302 | 120 |
| Rev D2: peak-hold D311/C327/R342, R313 33k, C326 22n, Q202 Vth 2.1 V | 2 | 0.00, 19.49 | 0.36 | 1.83 | 16 | 77 |
| Rev D2: same, Q202 Vth 1.0 V (min) | 2 | 0.00, 19.20 | 0.37 | 1.83 | 39 | 123 |

![Rev D1: HS_EN comes straight back - a 20-30 us retry loop](spice/plots/s5b_case1.png)
*Rev D1: HS_EN comes straight back - a 20-30 us retry loop*

![RC delay only, low-Vth Q202: still retries](spice/plots/s5b_case3.png)
*RC delay only, low-Vth Q202: still retries*

![Rev D2 peak-hold, low-Vth Q202: one trip, re-arm only because the test keeps pumping WDI](spice/plots/s5b_case5.png)
*Rev D2 peak-hold, low-Vth Q202: one trip, re-arm only because the test keeps pumping WDI*

## S6 - crank input (VR / Hall)

| C317 | Config | Case | edges expected | edges seen | delay us | delay deg | CRANK_F min V | CRANK_F max V |
|---|---|---|---|---|---|---|---|---|
| 1n | VR (JP301/JP302 open) | VR cranking 200 rpm, +/-0.4 V (36-1 wheel, 120 Hz) | 6 | 6 | 729.2 | 0.87 | -0.11 | 0.66 |
| 1n | VR (JP301/JP302 open) | VR cranking 150 rpm, +/-0.25 V (weak sensor) | 6 | 6 | 1638.9 | 1.48 | -0.10 | 0.53 |
| 1n | VR (JP301/JP302 open) | VR cranking 150 rpm, +/-0.15 V (below spec) | 6 | 0 | - | - | 0.16 | 0.43 |
| 1n | VR (JP301/JP302 open) | VR 12 000 rpm, +/-120 V (7.2 kHz) | 6 | 6 | 13.0 | 0.93 | -0.29 | 3.59 |
| 1n | Hall, JP301 only (Rev D1) | Hall open-collector 36-1 wheel, 6 000 rpm (JP301 closed) | 6 | 0 | - | - | 0.41 | 3.30 |
| 1n | Hall, JP301 only (Rev D1) | Hall open-collector 36-1 wheel, 12 000 rpm (JP301 closed) | 6 | 0 | - | - | 0.77 | 3.30 |
| 1n | VR (JP301/JP302 open) | VR idle 1 200 rpm +/-2 V + 60 V / 1 us ignition spike | 6 | 6 | 64.6 | 0.47 | -0.17 | 2.13 |
| 220p | VR (JP301/JP302 open) | VR cranking 200 rpm, +/-0.4 V (36-1 wheel, 120 Hz) | 6 | 6 | 681.7 | 0.82 | -0.11 | 0.66 |
| 220p | VR (JP301/JP302 open) | VR cranking 150 rpm, +/-0.25 V (weak sensor) | 6 | 6 | 1601.8 | 1.44 | -0.10 | 0.53 |
| 220p | VR (JP301/JP302 open) | VR cranking 150 rpm, +/-0.15 V (below spec) | 6 | 0 | - | - | 0.16 | 0.43 |
| 220p | VR (JP301/JP302 open) | VR 12 000 rpm, +/-120 V (7.2 kHz) | 6 | 6 | 9.0 | 0.65 | -0.29 | 3.59 |
| 220p | Hall, JP301 only (Rev D1) | Hall open-collector 36-1 wheel, 6 000 rpm (JP301 closed) | 6 | 0 | - | - | 0.30 | 3.30 |
| 220p | Hall, JP301 only (Rev D1) | Hall open-collector 36-1 wheel, 12 000 rpm (JP301 closed) | 6 | 0 | - | - | 0.30 | 3.30 |
| 220p | VR (JP301/JP302 open) | VR idle 1 200 rpm +/-2 V + 60 V / 1 us ignition spike | 6 | 7 | 31.1 | 0.22 | -0.18 | 3.57 |
| 1n | Hall, JP301 + JP302 closed (Rev D2) | Hall open-collector 36-1 wheel, 6 000 rpm (JP301 closed) | 6 | 6 | - | - | 0.00 | 0.54 |
| 1n | Hall, JP301 + JP302 closed (Rev D2) | Hall open-collector 36-1 wheel, 12 000 rpm (JP301 closed) | 6 | 6 | - | - | 0.00 | 0.54 |

![Rev D1 Hall input: CRANK_F never goes below the threshold](spice/plots/s6_1n_0_case5.png)
*Rev D1 Hall input: CRANK_F never goes below the threshold*

![Rev D2 Hall input (JP301 + JP302), 12 000 rpm](spice/plots/s6_1n_1_case6.png)
*Rev D2 Hall input (JP301 + JP302), 12 000 rpm*

## S7 - supply entry transients (F101, Q101, D102, D116)

| Var | Case | Q101 VDS V | VBAT_F min V | +12V max V | +12V min V | UC_VCC max V | D102 A | D102 J | F101 peak A |
|---|---|---|---|---|---|---|---|---|---|
| d1 | ISO 7637-2 pulse 1 (-100 V, 10 R, 2 ms) | 60.3 | -61.6 | 14.4 | -1.7 | 13.9 | 0.0 | 0.0 | 11.4 |
| d1 | ISO 7637-2 pulse 2a (+50 V, 2 R, 50 us) | 0.1 | 12.4 | 16.3 | 12.4 | 15.2 | 0.0 | 0.0 | 24.0 |
| d1 | ISO 7637-2 pulse 3a (-150 V, 50 R, 0.1 us) | 0.0 | 14.4 | 14.4 | 14.4 | 14.0 | 0.0 | 0.0 | 2.9 |
| d1 | ISO 7637-2 pulse 3b (+100 V, 50 R, 0.1 us) | -0.0 | 14.4 | 14.4 | 14.4 | 14.0 | 0.0 | 0.0 | 2.1 |
| d1 | ISO 16750-2 load dump 5b (suppressed 35 V, 1 R, 400 ms) | -0.0 | 14.3 | 23.1 | 14.3 | 22.6 | 13.2 | 123.0 | 11.9 |
| d1 | Jump start 24 V for 60 s (first 200 ms) | -0.0 | 14.4 | 23.3 | 14.4 | 22.7 | 14.3 | 62.2 | 13.5 |
| d1 | Reverse battery -14.4 V | 15.4 | -14.4 | 14.4 | 0.4 | 14.0 | 0.0 | 0.0 | 4.1 |

| Var | Case | Q101 VDS V | VBAT_F min V | +12V max V | +12V min V | UC_VCC max V | D102 A | D102 J | F101 peak A |
|---|---|---|---|---|---|---|---|---|---|
| d2 | ISO 7637-2 pulse 1 (-100 V, 10 R, 2 ms) | 38.7 | -39.7 | 14.4 | -1.7 | 13.9 | 0.0 | 0.0 | 11.4 |
| d2 | ISO 7637-2 pulse 2a (+50 V, 2 R, 50 us) | 0.1 | 12.4 | 16.3 | 12.4 | 15.2 | 0.0 | 0.0 | 24.0 |
| d2 | ISO 7637-2 pulse 3a (-150 V, 50 R, 0.1 us) | 0.0 | 14.4 | 14.4 | 14.4 | 14.0 | 0.0 | 0.0 | 2.9 |
| d2 | ISO 7637-2 pulse 3b (+100 V, 50 R, 0.1 us) | -0.0 | 14.4 | 14.4 | 14.4 | 14.0 | 0.0 | 0.0 | 2.1 |
| d2 | ISO 16750-2 load dump 5b (suppressed 35 V, 1 R, 400 ms) | -0.0 | 14.3 | 23.1 | 14.3 | 22.6 | 13.2 | 123.0 | 11.9 |
| d2 | Jump start 24 V for 60 s (first 200 ms) | -0.0 | 14.4 | 23.3 | 14.4 | 22.7 | 14.3 | 62.2 | 13.5 |
| d2 | Reverse battery -14.4 V | 15.4 | -14.4 | 14.4 | 0.4 | 14.0 | 0.0 | 0.0 | 4.1 |

d1 = Rev D1, d2 = Rev D2 (+ D116). Pulses 2a/3a/3b use the ISO 7637-2 bench (artificial network 5 uH
|| 50 R, generator in parallel); pulse 1 disconnects the battery. 3a/3b are absorbed by C101/C102 (< 50 mV);
board-level ESL is not modelled.

![Rev D1, ISO 7637-2 pulse 1: Q101 at 60 V](spice/plots/s7_d1_1.png)
*Rev D1, ISO 7637-2 pulse 1: Q101 at 60 V*

![Rev D2 with D116: Q101 at 39 V](spice/plots/s7_d2_1.png)
*Rev D2 with D116: Q101 at 39 V*

![Load dump 5b: D102 conducts for the whole 400 ms (open limitation)](spice/plots/s7_d2_5.png)
*Load dump 5b: D102 conducts for the whole 400 ms (open limitation)*
