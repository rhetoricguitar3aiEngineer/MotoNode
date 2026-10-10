# MotoNode project overview

This is a summary of the MotoNode work as it stood on 2026-10-04, assembled from the project
folders on Google Drive (a backup of the design PC). Each board folder has its own detailed README;
this page explains how they relate and what is still open.

## 1. The pieces and their history

| When | What | Where now |
|---|---|---|
| Aug 2026 | Bike-Telemetry concept (sensor list) | GitHub `Bike-Telemetry` repo |
| 2026-08-24 | **MotoNode Telemetry**: ESP32 + NEO-6M + MPU-6050 BLE node and Android app (several iterations; `_FIXED` is the last) | `telemetry/` |
| 2026-09-11 → 09-28 | **NodeIQ** prototype line: v2 single-ESP32 is the baseline; dual-ESP32 gateway/IMU is a side branch; app v3–v6 ZIPs are earlier, divergent work. GPS acquisition, SD mounting and IMU calibration were still reported broken after the Sep 11 builds. | Drive: *NodeIQ Project Archive — 2026-09-12* |
| 2026-09-29 | NodeIQ front module **RevF** functional schematic (PDF only, no ECAD) | Drive archive |
| 2026-10-02 | **NodeIQ front module Rev G**: editable KiCad schematic of RevF with the TBDs closed | `hardware/motonodeiq/nodeiq_front_revG/` |
| 2026-10-02 | **Ignition controller Rev D → D1 → D2**: datasheet checks, then eight faults found and fixed by SPICE | `hardware/ignition/REVISION_HISTORY.md` |
| 2026-10-03 | **MotoNodeIQ Rev B**: Hub / Front / Rear shrunk to 2 × 3 in, Micro-Fit connectors, routed | `hardware/motonodeiq/` |
| 2026-10-03 | **Ignition controller Rev E**: hub sensors merged in, push-in terminals, routed 6-layer board | `hardware/ignition/` |
| 2026-10-04 | `MotoNode_MainHub` backup: the early KiCad stub, not the Rev B hub | `hardware/archive/early-mainhub/` |

## 2. How the boards fit together

- **Power and network:** the MotoNodeIQ **Hub** takes the battery (XT60, 30 A fuse). It feeds the
  Front and Rear modules through PROFET smart switches and talks to them over **CAN 2.0B at 500 kbit/s**.
  The Front and Rear modules are the bus ends (JP251 bridged on both); the hub, mid-bus, leaves it open.
- **Ignition:** the Hub's J4 supplies `IGN_FEED` and a CAN tap to the ignition controller. The
  ignition board does not use CAN yet; the tap is reserved "for a future CAN rev".
- **Kill switch:** this is hardware only. Handlebar switch → front module → hub, where Q401B pulls the
  IGN_FEED switch off whenever the loop is open. A broken wire stops the engine.
- **Every board** uses an ESP32-S3 (WROOM-1-N8 on MotoNodeIQ, MINI-1-N8 on the ignition board), the
  same supply chain (TVS → reverse block → 5 V buck → 3.3 V LDO), and Tag-Connect TC2030 native-USB
  programming.
- **Telemetry** is a stand-alone node today: a classic ESP32 dev board on GPIO 16/17 (GPS) and
  21/22 (I2C). The protocol is documented in `telemetry/README.md` (service
  `6f9a0001-…`, 56-byte little-endian frame, 20 Hz).

## 3. Ignition controller, the short version

- 4 TCI channels (NGD8201N ignition IGBTs) and 1 CDI channel on CH1 (350 V flyback charger UC3845 +
  CSD19537Q3, C113 1 µF 630 V, BT151S SCR discharge).
- **Safety chain:** every power-stage drive runs from `VDRV_SW`, which is on only while the MCU pumps a
  watchdog (WDI charge pump). High-side over-current (U308A) and over-temperature (U308B) also cut it.
  Model-checked over 65 536 states × 16 invariants, and fault-injected (346 single faults).
- **Firmware obligations that came out of simulation:** latch off (stop WDI) when `ARM_OK` drops
  unexpectedly; subtract ~1° crank-input delay; check `V_COIL_MON` / `I_HS` before each SCR trigger;
  detect an open HT lead (coil current with no spark).
- **Install obligations:** CDI coil primary ≥ 100 µH; for Hall crank sensors close JP301 *and* JP302
  (VR: both open); use a NEO-6M breakout that runs from 3.3 V.

## 4. Open issues worth knowing about

These are collected from the per-board READMEs plus inconsistencies between the folders.

**Design limits (documented, not fixed)**
1. **24 V jump start / ISO 16750-2 load dump** fails on the ignition board: D102 (SMCJ18A) takes
   123 J and will short, blowing F101. The fix is a front-end change (load-dump TVS or surge stopper,
   40 V downstream parts). MotoNodeIQ boards are also only rated to the 35 V suppressed load dump.
2. **Ignition BOM is $30.08** against a $25 target (push-in terminals ~$4.80, IMU).
3. **T101 flyback transformer** is custom-wound and unverified; the simulation assumes 10 µH, 1:15, k 0.99.
4. **MotoNodeIQ brake/turn lights depend on firmware.** Modules should fall back to tail + brake ON
   when hub CAN goes silent; that firmware does not exist yet.
5. **MUN5211DW1 pinout** (every MotoNodeIQ input depends on it) needs confirming against the onsemi
   datasheet.

**Things that disagree between folders (decisions needed)**
1. **Two front-module architectures.** MotoNodeIQ Rev B Front uses ESP32-S3 + PROFET *high-side*
   switches + CAN. NodeIQ Rev G (and the Sep 28 handoff) uses ESP32-C3 + *low-side* MOSFETs with
   isolated load returns + LIN. These are mutually exclusive; pick one before more layout work.
2. **IMU and GNSS appear twice.** Rev E moved an MPU-6050 and a NEO-6M port onto the ignition board,
   while the MotoNodeIQ Hub also carries a MAX-M10S GNSS and an IMU. Decide which board owns motion
   data, or keep both on purpose (for example, ignition-local tilt cut-off).
3. **The ignition revision the Hub expects.** The MotoNodeIQ README refers to "MotoNode Rev D2" on J4.
   Rev E changed the coil connector to push-in terminals (J201 pin 6 is now the feed), so check the Hub J4 →
   ignition wiring against Rev E.
4. **Telemetry MCU.** The telemetry node targets a classic ESP32 dev board. The production boards are
   ESP32-S3, and the S3 has no GPIO 16/17 UART2 default, so porting the sketch needs a pin map.

## 5. Where the generated / source-of-truth code lives

| Board | Source of truth | Regenerate with |
|---|---|---|
| Ignition Rev E schematic | `netlist.py` (+ `kfinal.py`, `check_netlist.py`, `kparity.py`, `fpcheck.py`, `kbom.py`, `kengine.py`) | `python kfinal.py` |
| Ignition Rev E layout | the routed `.kicad_pcb` (master); scripts in `pcb_layout/` | edit in KiCad; "Update PCB from Schematic" |
| Ignition SPICE | `spice/` (`run_all.py`, `make_report.py`, `models.lib`) | `python3 spice/run_all.py` |
| MotoNodeIQ Hub/Front/Rear | `generator/hub.py`, `front.py`, `rear.py`, `blocks.py` | `cd generator && python build.py hub front rear` |
| NodeIQ Front Rev G | `generator/nodeiq_front.py` | `python build_sch.py nodeiq_front_revG` |

None of these scripts are in the repo yet. See [`FILES_TO_ADD.md`](FILES_TO_ADD.md).
