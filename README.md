# MotoNode

A cheap, modular, 12 V addressable LED lighting system. You chain identical
light **modules** off one small **controller**. Add, remove or rearrange
modules without rewiring: every module uses the same 3-wire plug.

Built for motorcycles (it can read the bike's brake and turn-signal wires), and
it runs just as well on a car, a bicycle with a 3S battery, or a 12 V wall
adapter.

```
 12V ──fuse──► [ CONTROLLER ] ──3-wire──► [MODULE 1] ──► [MODULE 2] ──► ... ──► [MODULE N]
                 ▲  ▲  ▲  ▲                 8 LEDs         8 LEDs                 8 LEDs
             brake L  R  button
```

| | Cost (approx., 2026 AliExpress/LCSC pricing) |
|---|---|
| One light module (8 LEDs, printed housing, plugs) | **≈ $1.30** |
| Controller (ESP32-C3, buck, protection, 3 signal inputs) | **≈ $4.30** |
| Starter kit: controller + 6 modules | **≈ $12** |

## Why it's cheap

* **No custom PCB needed for modules.** Each module is an 8-LED piece cut from
  a stock **WS2815 12 V** strip roll and pressed into a 3D-printed housing.
* **One controller for everything.** A $2 ESP32-C3 SuperMini drives up to ~60
  modules on one data wire.
* **12 V LEDs.** WS2815 runs straight off the vehicle supply. You don't need a
  heavy 5 V regulator or power injection, and if one LED's data line dies the
  next one keeps working (backup data line).
* **Commodity parts only.** Every part is a generic jellybean part with many
  sellers.

## Repository layout

| Path | What's in it |
|---|---|
| [`docs/DESIGN.md`](docs/DESIGN.md) | Full design: architecture, module spec, controller schematic, power budget, wiring, build steps |
| [`hardware/bom.csv`](hardware/bom.csv) | Bill of materials with unit costs |
| [`enclosure/module_housing.scad`](enclosure/module_housing.scad) | Parametric OpenSCAD housing + diffuser + controller box |
| [`firmware/`](firmware/) | PlatformIO / Arduino firmware for the ESP32-C3 controller |

## Quick start

1. Print `N` module housings and diffusers (`enclosure/module_housing.scad`).
2. Cut the WS2815 strip into 8-LED pieces, solder a 3-pin pigtail to each end,
   then seal and close each module ([build steps](docs/DESIGN.md#7-build-steps)).
3. Build the controller ([schematic](docs/DESIGN.md#4-controller)).
4. Set your module count and roles in `firmware/include/config.h`, then
   `cd firmware && pio run -t upload`.

> **Road legality:** Rules on lighting colour, position and flashing differ by
> country and state. Never show red to the front or flashing red/blue, and
> treat the turn and brake functions as *supplements* to your legal lamps
> unless the lamps are certified. Checking your local rules is up to you.
