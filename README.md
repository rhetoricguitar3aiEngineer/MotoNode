# MotoNodeIQ

Motorcycle electronics for the 2003 Suzuki Katana 600: CAN body-electronics boards, an
ignition controller, and an Android telemetry app. Reorganized 2026-10-10. This repo mirrors the
`MotoNodeIQ` folder on the design PC, which is the source of truth for the current hardware.

**Status: designed and checked in software (KiCad 10 ERC/DRC clean), nothing built or bench-tested.**

| Folder | What | Status |
|---|---|---|
| [`Boards/`](Boards/) | **Current 3-board CAN system**: `hub/`, `front/`, `rear/` (Rev B, 76.2 x 50.8 mm) plus `generator/` that rebuilds them (`generator/build.py <board>`). [`Boards/README.md`](Boards/README.md) has the details and the "before you order" list. | Live |
| [`Boards/nodeiq_front_revG/`](Boards/nodeiq_front_revG/) | Hand-built Front Module Rev G, kept beside the generated `front/` | Reference |
| [`Ignition/RevE/`](Ignition/RevE/) | **Ignition controller Rev E**: 4 TCI + 1 CDI, ESP32-S3, hub functions (IMU/GPS/sensor inputs) merged in, 6-layer 100 x 70 mm, fully routed, DRC clean | Live |
| [`Telemetry/MotoNodeTelemetry/`](Telemetry/MotoNodeTelemetry/) | Android telemetry app + `esp32/` firmware (Gradle build output stripped; Android Studio regenerates it) | Live |
| [`Docs/`](Docs/) | Design brief, implementation plan, connector selection, source audit, board status (from the Codex NodeIQ work), plus [`OVERVIEW.md`](Docs/OVERVIEW.md) | Reference |
| [`Archive/`](Archive/) | Superseded material, see [`Archive/README.md`](Archive/README.md) | Archived |

`_Keys/keyMN1` (the Android app-signing keystore) lives beside these folders on the PC and is
**deliberately not in this repo**. It is irreplaceable: back it up off the PC, and never commit it.
`.gitignore` blocks `_Keys/` and keystore files.

## Not yet in the repo

Docs, BOMs, check reports and the telemetry source are here. The KiCad design files (`.kicad_*`,
libraries, `fab/`) and the Python generators (`Boards/generator/`, `Ignition/RevE/pcb_layout/`,
`Ignition/RevE/spice/`) still need to be pushed from the PC. See
[`Docs/FILES_TO_ADD.md`](Docs/FILES_TO_ADD.md).

## Google Drive

My Drive/**MotoNodeIQ** (<https://drive.google.com/drive/folders/14qOt1xsgB9vhRgdrsN2DCoWwWa2cDshs>)
holds what is *not* here: NodeIQ Android app releases (App/), ESP32 firmware (Firmware/), marketing
images/videos (Marketing/), reports, AI handoffs, and pre-Rev-B hardware (Archive/). "My Computer (1)"
on Drive is a stale backup of the old PC layout.

## Open decisions

- **Hub board vs Ignition Rev E.** Rev E puts the GPS/IMU/sensor inputs on the ignition board, which
  overlaps with `Boards/hub/`. Undecided whether the 3-board system keeps its own hub.

## Tools

- KiCad 10.0.6. Its Python (`D:\Documents\bin\python.exe` on the PC) is needed by `pcbgen.py` / `pcbfinish.py`.
- Router and other generator scripts use system Python (numpy, scipy, shapely, PIL).
- ngspice 42 for `Ignition/RevE/spice/`.
- Android Studio (Gradle 9.5, JDK 17) and the Arduino ESP32 core for `Telemetry/`.

## Safety

The ignition board generates ~350 V on the CDI bus. Treat an assembled board as live and lethal, and
bench-test with current-limited supplies before it goes near a bike.
