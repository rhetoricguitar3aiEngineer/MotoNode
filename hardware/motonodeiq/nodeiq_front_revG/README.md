# NodeIQ Front Module, Rev G (schematic)

This is the editable KiCad schematic for the front module described in the
NodeIQ archive's **RevF** functional schematic (`NodeIQ_Front_Module_RevF.pdf`,
NODEIQ-FM-01 / FM-02, 2026-09-29), with RevF's TBD items closed. The archive
noted that RevF had no editable ECAD source; this is that source.

**Status:** schematic only, no PCB. KiCad ERC reports 0 violations. The KiCad
netlist was exported and compared net by net with the generator's model, and
they match exactly. Nothing is built or tested.

## Current paths on the schematic

The two power sheets are hand-laid with real wires, so the current paths can
be followed by eye:

* **Power outputs:**
  * **Thick red** is the supply current path: J1-1 BATT+ → F1 → Q6
    (reverse-battery FET) → the +12V PROT bus → each load connector's pin 1.
  * **Thick blue** is the return current path: load → SW RETi (Ji pin 2) →
    Qi drain-source → RSHi shunt → GND bus → J1-2.
  * **Dashed grey** boxes are the off-board lamps and horn (E1-E4, H1) and
    their harness. Green stubs are the ISi sense taps.
* **Logic supply:** red is the 12 V input, orange the 5 V buck output, purple
  the 3.3 V LDO output, and blue the ground return.
* **Control and protection** carries signal-level nets only and still uses
  labelled stubs.

## What RevF defined (kept unchanged)

* Five low-side N-MOSFET channels, Q1-Q5. Each one switches the **return** of
  a two-wire load. Loads plug into J2-J6, with pin 1 = +12V_PROT and
  pin 2 = SW_RETi.
  * CH1 HEAD HI
  * CH2 HEAD LO
  * CH3 TURN LEFT
  * CH4 TURN RIGHT
  * CH5 HORN
* Each load needs an isolated return lead. A chassis-grounded lamp bypasses
  the switch.
* Per channel: shunt RSHi, gate resistor RGi, gate pull-down RPDi.
* Per channel, a comparator (U2A-U2D, U3A) with an open-collector output on
  GATEi / OCPi#. When ISi rises above VTH (set by RTH1 / RTH2), it pulls the
  gate low and forces Qi off. U1 then latches CMDi low.
* Battery path: F1 fuse, D1 clamp, C1 bus decoupling.
* U1 ESP32-C3 BLE MCU.
* U4 TLIN1021-Q1 LIN transceiver, with J10 carrying LIN + GND to the hub.
* J11 → J12 hardwired KILL A, KILL B and BRAKE RAW. These are plain copper,
  with no MCU, LIN or output stage in the path.

## What Rev G decides (RevF left these TBD)

| Item | Rev G choice | Why |
|---|---|---|
| Q1-Q5 | Infineon IPD50N04S4L-08: 40 V, 8.8 mΩ max at V_GS 4.5 V, AEC-Q101, DPAK | Logic-level part, automotive qualified, avalanche rated |
| Gate drive | 74AHCT125 + 74AHCT1G125 buffers on 5 V, between CMDi and RGi | A 3.3 V GPIO leaves the MOSFET partly on. 5 V gives the rated R_DS(on) |
| RGi / CGi / RPDi | 10 k / 47 nF / 100 k | Soft turn-on (~0.5 ms) eases lamp inrush and slows retry after a trip. The comparator discharges the gate directly, so turn-off is fast |
| RSHi | 5 mΩ, 3 W, 2512 (WSLP2512R0050FEA) | 0.125 W at 5 A |
| VTH | RTH1 100 k / RTH2 4.7 k from 3V3 = 148 mV | Trips at about 30 A per channel |
| Blanking | RFi 1 k + CFi 1 µF (~1 ms) at each comparator input | Rides through cold-filament inrush. The firmware still owns the fault latch |
| Comparators | LM2901 (quad, CH1-4) + LM2903 (dual, CH5) on 5 V | LM339-class open collector, automotive temperature range. Inputs work down to ground |
| Current to ADC | INA4180A2 (gain 50) gives 0.25 V/A on CH1-4 | Shunt millivolts are too small for the ESP32-C3 ADC. CH5 (horn) has trip protection but no ADC reading, because the C3 has only four free ADC1 pins |
| Reverse battery | Q6 SUD50P06-15 P-MOSFET, 15 V gate zener D3, R1 | This is RevE's "QRP" |
| D1 | SMCJ24A (1500 W) after Q6 | Vehicle transient clamp |
| Horn | D2 SS34 flyback diode, SW_RET5 → +12V_PROT | RevE action item |
| LIN | Responder: 220 pF bus capacitor, no 1 k pull-up (the hub is the commander) | Per the TLIN1021-Q1 datasheet. RXD is open drain, pulled up to 3V3 with 4.7 k |
| Logic supply | LMR51430 buck to 5 V, then AP2112K to 3V3 | — |
| Sleep | The buck's EN comes from TLIN1021 **INH** | The module powers down when the transceiver sleeps and wakes on LIN traffic. Draw on the battery input in sleep is roughly the transceiver's ~10 µA plus leakage |
| Connectors | Mini-Fit Jr 1x2 for power, loads and LIN; Micro-Fit 2x2 for the safety pass-through | — |

## ESP32-C3 pin map

The ESP32-C3-WROOM-02 has exactly enough pins. IO2, IO8 and IO9 are boot
straps, so they hold the signals that must be high at reset.

| Pin | Net | Pin | Net |
|---|---|---|---|
| IO0 | IS1_MON (ADC) | IO7 | CMD3 |
| IO1 | IS2_MON (ADC) | IO8 | LIN_TXD (10 k pull-up) |
| IO3 | IS3_MON (ADC) | IO9 | BOOT button (10 k pull-up) |
| IO4 | IS4_MON (ADC) | IO10 | CMD4 |
| IO2 | LIN_EN (10 k pull-up) | IO20 | CMD5 |
| IO5 | CMD1 | IO21 | LIN_RXD through 1 k (IO21 prints the boot log) |
| IO6 | CMD2 | IO18 / IO19 | USB D- / D+ (programming via Tag-Connect J13) |

CMD1-CMD5 each have a 100 k pull-down, so no output turns on while U1 boots.

## Still open (carried from RevF / RevE)

1. **Thresholds and blanking:** characterise real lamp inrush and horn
   current. A cold 55 W headlight peaks near 40 A, which is above the 30 A
   trip. The 1 ms filter and soft start should ride through it, but this
   needs a bench test. Firmware should allow a limited retry on lamp channels.
2. **MOSFET SOA** during a hard short, for the time the 1 ms filter takes to
   trip (about 0.3 ms at 100 A). Check against the datasheet SOA curve.
3. **PCB:** Kelvin-route each INA and comparator input to its shunt. Each
   channel's power ground must return to J1-2 without passing under the logic.
4. **IPD50N04S4L-08 figures** were taken from a datasheet summary. Confirm
   R_DS(on) at V_GS = 5 V and the avalanche rating.
5. **Kill / brake behaviour:** J11 → J12 is a pass-through only. The bike's
   validated ignition-kill circuit must still do the actual kill.

## Files

* `NodeIQ_Front_RevG.kicad_pro` / `.kicad_sch`: root sheet plus three sub-sheets
  * `outputs.kicad_sch`: battery input, QRP, clamp, CH1-CH5
  * `control.kicad_sch`: MCU, gate buffers, comparators, current monitor, LIN, pass-through
  * `supply.kicad_sch`: 5 V buck and 3.3 V LDO
* `NodeIQ.kicad_sym` + `sym-lib-table`: the project symbol for TLIN1021-Q1
* `NodeIQ_Front_RevG_schematic.pdf`, `NodeIQ_Front_RevG_BOM.csv`
* Source: `../generator/nodeiq_front.py`. Regenerate with
  `python build_sch.py nodeiq_front_revG`, then `python parity.py nodeiq_front_revG`.
