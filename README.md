# MotoNode

Open motorcycle electronics, built around a 2003 Suzuki Katana 600 and usable on most 12 V bikes:
an ignition controller, a CAN-networked body-electronics system and a BLE telemetry dashboard.

**Status: designed and checked in software, nothing built or bench-tested.** Every board below has
passed KiCad ERC/DRC; none has been fabricated. Read each board's "before you order" section first.

## What's here

| Path | What it is | State |
|---|---|---|
| [`hardware/ignition/`](hardware/ignition/) | **MotoNode ignition controller + hub, Rev E.** 4 × TCI + 1 × CDI (350 V flyback), ESP32-S3, hardware safety chain, MPU-6050 + GPS port, push-in terminals. 100 × 70 mm, 6 layers, 241 parts. | Routed, DRC clean. Docs, BOM, check reports in repo; KiCad files still to add (see below) |
| [`hardware/motonodeiq/`](hardware/motonodeiq/) | **MotoNodeIQ, Rev B.** Central Hub + Front + Rear modules, 76.2 × 50.8 mm each, ESP32-S3 + CAN 2.0B, PROFET+2 smart high-side outputs. Boards are generated from Python (`generator/`). | Routed, DRC clean. Docs in repo; generator + KiCad files still to add |
| [`hardware/motonodeiq/nodeiq_front_revG/`](hardware/motonodeiq/nodeiq_front_revG/) | **NodeIQ front module, Rev G.** Alternative front-module branch: ESP32-C3, low-side MOSFETs, LIN. | Schematic only |
| [`hardware/archive/early-mainhub/`](hardware/archive/early-mainhub/) | First KiCad stubs of the MainHub and Universal Ignition (KiCad 9 era). | Superseded, kept for history |
| [`telemetry/`](telemetry/) | **MotoNode Telemetry.** ESP32 + NEO-6M GPS + MPU-6050 firmware streaming a 56-byte frame over BLE at 20 Hz, plus a Kotlin/Compose Android dashboard (lean angle, G, speed). | Source complete |
| [`docs/`](docs/) | System overview, open issues, and the list of files still to bring over from your PC / Drive. | — |

Start with [`docs/OVERVIEW.md`](docs/OVERVIEW.md) for how the pieces fit together.

## System at a glance

```
 battery ── 30 A fuse ──► MotoNodeIQ HUB ── FRONT_FEED + CAN + KILL_HW ──► FRONT module (lights, horn, switches)
                              │   └──────── REAR_FEED  + CAN ─────────────► REAR module  (tail, brake, fuel, speed)
                              └─ IGN_FEED ──► MotoNode ignition controller (TCI/CDI, coils)
                                 STARTER  ──► OEM starter relay
 phone (Android) ◄── BLE 20 Hz ── telemetry node (ESP32 + GPS + IMU)
```

## Tools

- **KiCad 10.0.x** for all hardware (MotoNodeIQ schematics are KiCad 9 format; KiCad 10 upgrades them on save).
- **Python 3** + KiCad's bundled Python for the board generators / layout scripts; **ngspice 42** for `hardware/ignition/spice/`.
- **Arduino IDE / arduino-cli** with the ESP32 core for `telemetry/esp32/` (libraries: TinyGPSPlus, Adafruit MPU6050, Adafruit Unified Sensor).
- **Android Studio** (Gradle 9.5, JDK 17) for `telemetry/`.

## Safety

The ignition board generates **~350 V** on the CDI bus and drives ignition coils. HV clearances are
enforced in the design rules, but treat any assembled board as live and lethal, and bench-test with
current-limited supplies before it goes near a bike.
