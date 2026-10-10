# NodeIQ KiCad 10 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Execution method remains for the owner to choose.

**Goal:** Produce the approved subsystem designs as checked native KiCad 10 schematics and routed PCBs: one 101.6 x 76.2 mm central hub with RevD2 ignition and GNSS integrated, and 50.8 mm square supporting boards. Board03 is retained as a standalone GNSS RF test coupon, not installed hardware. Boards 02-19 have a combined single-prototype parts target strictly below $25 or an explicit, evidenced constraint failure. The owner raised board 01's cap without specifying a new number; its complete BOM must be quoted and reported.

**Architecture:** One ESP32-C6 hub with an on-board SAM-M10Q GNSS receiver and the full RevD2 four-TCI/one-CDI ignition control on the same PCB; CC2340R53 wireless sensing leaves; LIN front/rear load boards. Common leaf circuitry is counted in each sensor board; the two-wire charging backbone carries charging power only. Every field-wire connector is a no-crimp/no-solder press-latch or lever spring terminal.

**Tech Stack:** KiCad 10.0.6 or newer 10.x stable, native project libraries, manufacturer datasheets/reference layouts, Python for independent dimensional/netlist/BOM auditing, SPICE where a supported model establishes useful circuit behavior.

**Spec:** [Approved design brief](../NodeIQ_KiCad10_Design_Brief.md). Approved by the owner on 2026-10-02. No motorcycle/load answers have been supplied; no vehicle compatibility is assumed.

## Global Constraints

- Native KiCad 10 project, schematic sheets, PCB, local symbol/footprint libraries and required design-rule files.
- Board 01 has one closed 101.6 x 76.2 mm Edge.Cuts outline; boards 02-19 have closed 50.8 x 50.8 mm outlines.
- All field-wire PCB connectors accept stripped conductors by hand-operated spring/lever clamp, with no crimp or installation soldering. Include exact installed connector parts in the quantity-one BOM; check wire range, current/voltage, temperature, footprint and enclosure/strain relief needs.
- Supporting-board parts BOM strictly less than USD 25 per circuit at a purchasing quantity of one prototype; the hub cap was raised without a replacement number.
- PCB fabrication is excluded from the parts budget. Shipping, tax, assembly and tools are reported separately.
- Required off-board purchased hardware is shown in a complete-subsystem total; interface-only cost is never called complete sensor/display/radar cost.
- Routed PCB with filled zones and zero unconnected required pads.
- Fresh KiCad 10 ERC/DRC and schematic parity; every exclusion is disclosed and justified.
- No fabrication-ready status for unresolved electrical limits, required interfaces, transformer design, layout or clearance.
- Original archives and firmware remain unchanged. New work lives in outputs/boards; tools/scratch and copied references live in work.
- Plans 01-19 are physical-board plans. The former board-20 plan is retained only as RevD2 integration review/history; it creates no separate physical PCB or separate cost bucket. Its TCI and CDI functions belong to board 01.

## Review Focus

1. Vehicle transients and unpowered backfeed: selection calculations and per-board limits must establish safe domain behavior before capture.
2. Firmware reset/hang: output-disable and persistent trip paths must operate without firmware where required.
3. External sensor/interface mismatch: pin tables, voltage limits and declared input families must match connected equipment.
4. Routing and footprint mistakes: compare manufacturer pin numbers, exported schematic netlist and routed PCB pads, independently of drawing code.
5. Budget accounting: count the integrated hub and ignition parts together, plus every press-latch connector. Board 01 has no current numerical cap but still requires a complete quoted total. Count repeated leaf/power circuits and required sensors, batteries and antennas; missing quotes cannot yield PASS for boards 02-19 or a verified total for board 01.

Each board plan assigns these cases to its electrical, capture, layout and cost checks. Bench-only conditions are recorded as not physically tested.

## Files and interfaces

- Board directory: outputs/boards/<ID>_<slug>/.
- Native basename: NodeIQ_<ID>_<slug>.
- Each directory contains .kicad_pro, .kicad_sch, .kicad_pcb, local libraries/tables, electrical_spec.md, pin_contract.csv, bom.csv, external_parts.csv, validation.md, reports/, fabrication/ and previews/.
- pin_contract.csv columns: connector,pin,net,direction,domain,min_v,max_v,max_a,default_state,peer_board,peer_pin. Unknown limits prevent interface freeze.
- bom.csv columns: references,quantity,value,mpn,footprint,vendor,url,quote_date,currency,unit_usd,minimum_purchase,available,extended_usd,status.
- external_parts.csv uses the BOM fields plus inclusion_reason and existing_vehicle_equipment.
- work/tools/audit_board.py provides audit_board(project_dir: pathlib.Path) -> dict. It reads actual KiCad-exported netlist/PCB/BOM, checks dimensions, required connectivity, reference uniqueness and cost, and returns named checks without converting missing information into a pass.
- outputs/NodeIQ_Board_Status.csv columns: id,name,design_status,outline_width_mm,outline_height_mm,board_parts_usd,complete_subsystem_usd,price_status,erc_status,drc_status,unconnected,parity_status,bench_status,constraint_failures.
- Per-board statuses: planned, electrical_defined, schematic_checked, routed_checked, fabrication_exported, constraint_failure. These describe evidence, not overall vehicle readiness.
- Shared rail voltages, charging-current budget, connector pin assignments and LIN commander/responder roles are frozen in outputs/boards/02_vehicle_supply/electrical_spec.md and outputs/boards/01_main_hub/pin_contract.csv before dependent capture. The leaf connector contract is frozen in board 05. Later boards consume those exact tables.

## Task 0: Toolchain and independent checks

**Files:** work/tools/audit_board.py; work/tests/test_audit_board.py; outputs/toolchain.md; outputs/NodeIQ_Board_Status.csv.

- [ ] Establish KiCad 10 from the existing signed Downloads installer, using an isolated workspace tool location where practical. Verify the actual kicad-cli version begins with 10.; preserve KiCad 9 and its settings.
- [ ] Record install/runtime/library paths and CLI version. Verify schematic and PCB file compatibility using copied references; keep results distinct from fresh design validation.
- [ ] Write meaningful checker tests with malformed inputs: a 51 mm board, open outline, swapped connector pins, unrouted required pad, repeated reference, missing price, quantity-100-only quote and total equal to $25. They must all fail the relevant check.
- [ ] Implement the checker against parsed/exported artifacts and run those tests. A correct 50.8 mm square fixture with known netlist/pad correspondence and a $24.99 complete BOM must pass the applicable checks.
- [ ] Initialize the status table with 19 physical-board rows, blank price/check results and bench_status=not_tested. Record ignition integration findings with board 01, not as a fabricated board 20.

## Per-board task sequence

Every linked plan has four independently reviewable tasks: electrical definition and sourcing; pin-level schematic capture; placement/routing; final verification and release. Execute in dependency order:

- [01 Main hub and universal ignition](01_main_hub_plan.md) — consumes 02_vehicle_supply and D:/MotoNode_ignition_revD2.
- [02 Vehicle supply and charging backbone](02_vehicle_supply_plan.md) — consumes none.
- [03 GNSS RF test coupon](03_gnss_plan.md) — standalone comparison artifact; the installed GNSS is on 01_main_hub.
- [04 IMU and vibration](04_imu_plan.md) — consumes 01_main_hub,02_vehicle_supply.
- [05 Wireless leaf platform](05_wireless_leaf_plan.md) — consumes 02_vehicle_supply.
- [06 RPM and crank observation](06_rpm_crank_plan.md) — consumes 05_wireless_leaf.
- [07 Wheel speed](07_wheel_speed_plan.md) — consumes 05_wireless_leaf.
- [08 Engine temperature](08_engine_temperature_plan.md) — consumes 05_wireless_leaf.
- [09 Brake pressure](09_brake_pressure_plan.md) — consumes 05_wireless_leaf.
- [10 Throttle position](10_throttle_position_plan.md) — consumes 05_wireless_leaf.
- [11 Suspension travel](11_suspension_travel_plan.md) — consumes 05_wireless_leaf.
- [12 Fuel level](12_fuel_level_plan.md) — consumes 05_wireless_leaf.
- [13 Tire pressure integration](13_tpms_plan.md) — consumes 01_main_hub,05_wireless_leaf.
- [14 Haptic grip](14_haptic_grip_plan.md) — consumes 05_wireless_leaf.
- [15 Front lighting and horn](15_front_lighting_plan.md) — consumes 01_main_hub,02_vehicle_supply.
- [16 Rear lighting](16_rear_lighting_plan.md) — consumes 01_main_hub,02_vehicle_supply.
- [17 Display interface](17_display_interface_plan.md) — consumes 01_main_hub,02_vehicle_supply.
- [18 Universal expansion](18_universal_expansion_plan.md) — consumes 05_wireless_leaf.
- [19 Radar advisory interface](19_radar_interface_plan.md) — consumes 01_main_hub,02_vehicle_supply.
- [RevD2 ignition integration review](20_universal_ignition_plan.md) — evidence input to board 01; no separate board is authorized by the latest requirement. Input conditioning remains local to the integrated hub, and wireless RPM sensing is not a timing dependency.

Implement board 02 and the integrated board 01 contract together, then 03/04 and 05. Sensor variants consume the frozen leaf contract. Load boards consume the protected vehicle-supply contract. Ignition remains bench-only until its native bypass and coil limits are validated.

## Verification commands and acceptance

Run commands from each board directory with the recorded KiCad 10 executable. Replace <base> with the board's exact basename.

```text
kicad-cli sch erc --severity-all --exit-code-violations --output reports/erc.rpt <base>.kicad_sch
kicad-cli sch export netlist --output reports/netlist.xml <base>.kicad_sch
kicad-cli pcb drc --schematic-parity --all-track-errors --refill-zones --save-board --severity-all --exit-code-violations --output reports/drc.rpt <base>.kicad_pcb
python work/tools/audit_board.py <absolute-board-directory>
```

The audit command is run from the workspace root; it is shown separately from board-local CLI commands. Check the installed CLI help before first export for current output syntax/layer options. ERC and DRC must have zero unexplained violations, zero required unconnected pads and matching schematic/PCB nets. Audit must establish the board-specific exact outline and quote-backed cost below $25.

Only after these checks, export PDF, Gerbers and Excellon drill data with KiCad 10; inspect the actual exports for layer coverage, holes, outline and readable connector labels. Record SHA-256 of source and final manufacturing files. Render and inspect both PCB faces and every schematic sheet. Publish unresolved physical testing separately.

## Constraint failures and completion

If a required device cannot meet the cap, no single-unit source is available, or protection cannot be designed within the outline, preserve the engineering evidence and mark constraint_failure. Continue independent boards. Do not fabricate prices or silently replace a complete subsystem with an interface PCB.

Finish with a linked index, status table and one package containing actual native sources/reports/manufacturing outputs. Distinguish routed_checked from fabrication_exported and bench-tested from not_tested. Projectless work has no existing Git repository; preserve hashes and versions instead of claiming commits that did not occur.

## Execution handoff

The owner selected subagent-driven implementation. The owner's latest hub/ignition/connector amendments supersede conflicting older board-specific plan text; implementation and verification proceed within this same chat.

