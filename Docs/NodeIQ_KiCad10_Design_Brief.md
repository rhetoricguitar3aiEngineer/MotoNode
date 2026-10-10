# NodeIQ / MotoNode circuit and PCB design brief

Date: 2026-10-02. Status: architecture approved and amended by the owner. KiCad capture is in progress. The central hub now incorporates the D:/MotoNode_ignition_revD2 ignition architecture.

## Requirements supplied by the owner

- Research the MotoNode/NodeIQ project using the context available on this computer.
- Deliver full circuits for each subsystem in KiCad 10.
- Deliver a 101.6 x 76.2 mm (4 x 3 inch) central hub PCB; each other physical circuit remains exactly 50.8 x 50.8 mm (2 x 2 inches).
- Integrate the full four-channel TCI and one-channel CDI RevD2 ignition function into the central hub architecture on its one PCB. There is no separately budgeted ignition PCB.
- Use field-wire press-latch connections that need no crimping or soldering during installation. PCB connector attachment during manufacturing is still part of board assembly.
- Parts BOM strictly less than USD 25 for each supporting circuit (boards 02-19) at a purchasing quantity of one prototype. The owner raised the cap for the combined central hub/ignition circuit (board 01) on 2026-10-03; no numerical replacement ceiling was specified. Price and report its complete quantity-one BOM without pruning RevD2 functionality to meet the former cap.
- PCB fabrication is excluded from the parts budget. Shipping, tax, assembly and tools are reported separately.
- Include connectors, required protection, decoupling, programmed MCU/radio hardware, and required on-board sensors in the parts BOM. No quantity-100 prices may stand in for quantity-one prices.

The user has not yet supplied the motorcycle model, actual loads, ignition interface, sensor ranges or environmental limits. These are electrical requirements, not permission questions.

## Design direction

Use the September 6 target architecture recorded in the project handoff: ESP32-C6 hub, CC2340-class battery-powered wireless leaves, raw 2.4 GHz IEEE 802.15.4 star, BLE/Wi-Fi at the hub, and two-wire charging while the motorcycle is off. Preserve the dual-ESP32 GPS/IMU arrangement as a development reference. It is not the target product topology.

Use the exact CC2340R53 device variant and TI reference layout when developing a bare-chip 802.15.4 leaf. Family-level claims or a BLE-only module are insufficient evidence of compatibility. Exact purchasable MPN, pinout and SDK support must be checked before capture.

Front and rear vehicle load controllers communicate over LIN, consistent with the later front-module work. Kill and raw brake functions have dedicated hardwired paths; radio, phone and cloud do not carry those control functions. The wireless leaf network is for sensing and advisory functions. This mixed architecture preserves both documented workstreams.

GPS is physically integrated on the 4 × 3 inch central hub alongside the RevD2 ignition circuitry. Board03 is retained only as a separate 2-inch GNSS RF test prototype. IMU remains a separate 2-inch board. Changing MCU families will require firmware changes; existing GPIO numbers and binaries do not transfer automatically.

## Approaches considered

| Approach | Benefit | Consequence |
| --- | --- | --- |
| Reuse the older ESP32 test topology for all nodes | Closer to existing sketches | Does not implement the decided low-power 802.15.4 leaf architecture |
| Modular C6 hub, R53 leaves, LIN load boards (recommended) | Matches the documented target and separates power/RF/high voltage | Requires firmware ports and explicit board interfaces |
| Integrate the complete RevD2 ignition function with the C6 hub on one 4 x 3 inch PCB (owner direction) | One central control assembly | Fit, insulation, current paths and the full quantity-one cost remain unproven |

The owner-selected integrated hub is one physical board with one combined BOM. Its cap has been raised without a replacement number; quote the complete board and required external parts transparently. The other circuits retain independent $25 caps. Splitting the combined hub BOM into schematic sheet names does not create separate budgets.

## Circuit inventory and functional boundaries

This inventory covers the physical electronics named in the technical handoff. Android, cloud, ride analyzer, educational material and marketing assets are software/content dependencies, not additional circuits. Common circuitry must be counted on every board that uses it.

| ID | Physical circuit | Required function and interface | Cost/size issue to resolve |
| --- | --- | --- | --- |
| 01 | Main hub plus universal ignition and GPS | ESP32-C6 coordination, on-board SAM-M10Q GNSS, LIN, IMU interface and RevD2-based four TCI channels, one CDI channel, Hall/VR conditioning, deterministic ignition controller, HV supply and safety chain | 101.6 x 76.2 mm fit, GNSS/ignition RF coexistence, combined quantity-one cost, protected 12 V ignition feed, insulation, custom transformer, coil compatibility, press-latch harness |
| 02 | Vehicle supply and charging backbone | Protected 12 V input, logic rails, ignition-state sensing, hardware charging inhibit while running, undervoltage battery protection | Transient envelope, connected leaf count, total charge current and standby drain |
| 03 | GNSS RF test prototype | Separate SAM-M10Q comparison board with lever terminal | Test coupon only; installed receiver is part of Board01 |
| 04 | IMU / vibration | Six-axis acquisition, rigid orientation-marked mounting, I2C/SPI, interrupt, filtering | Sensor selection and bandwidth; no claim that schematic fixes calibration algorithms |
| 05 | Wireless leaf platform | CC2340R53 radio, clocks, RF matching, antenna, debug, regulated battery power, local charger and battery sensing | Reference-layout stackup, antenna clearance, battery protection and battery cost |
| 06 | RPM / crank observation | High-impedance local Hall/VR conditioning or separate pickup, timestamp edges without loading OEM circuit | Hall, VR and coil-primary are different interfaces; no universal unqualified tap |
| 07 | Wheel speed | Protected Hall/reed/local pickup input, edge acquisition and wireless leaf | Sensor supply, edge rate, pull-up polarity and cable protection |
| 08 | Engine temperature | Local NTC or existing-sensor observation, excitation/filtering and wireless leaf | Temperature range, probe cost, loading of existing ECU input |
| 09 | Brake pressure | Local pressure-transducer excitation and conditioning, wireless measurement | Hydraulic pressure range, pressure-rated transducer and fittings may dominate budget |
| 10 | Throttle position | High-impedance existing TPS observation or independent position sensor, local wireless acquisition | 0-5 V versus other interfaces; loading and input-fault isolation |
| 11 | Suspension travel | Local position transducer conditioning, wireless acquisition | Stroke, transducer technology and mounting; sensor cost must be shown |
| 12 | Fuel level | Defined sender conditioning, local wireless acquisition, protection | Sender resistance range, shared gauge loading, fuel-area installation limits |
| 13 | Tire pressure integration | Identified commercial TPMS protocol receiver/interface or pressure-sensor test leaf | 433 MHz TPMS is not received by a 2.4 GHz radio. A 2-inch PCB is not a validated valve-mounted sensor |
| 14 | Haptic grip | Current-limited motor driver, flyback, local control, fault-off behavior | Actuator voltage/current and actual actuator cost |
| 15 | Front lighting / horn | High/low beam, left/right indicator and horn control; current diagnostics; LIN; dedicated brake/kill paths | Five connectors, common bus current, inrush, thermal performance, hardware trip latch |
| 16 | Rear lighting | Tail/brake/left/right outputs and LIN diagnostics; hardwired brake behavior | Output ground topology and safe operation on loss of module power |
| 17 | Display interface | Protected supply, UART level interface and connector for selected rider display | A Nextion interface PCB cost is distinct from the purchased display cost |
| 18 | Universal expansion | Defined local analog/digital/I2C interfaces with protection and wireless leaf | Limits must be explicit; connector labels cannot imply arbitrary-voltage compatibility |
| 19 | Radar advisory interface | Supply and digital interface for a selected mmWave sensor, advisory data only | Module, antenna and field of view must be specified and costed; interface-only is not a complete radar |
| 20 | Ignition integration review (documentation, not another circuit) | RevD2 function and pin/compatibility matrix incorporated in board 01 | No separate PCB or budget; review combined hub fit, cost and safety |

Boards 05-12 and 18 are related design variants: each final wireless sensor PCB must contain or explicitly mate to its radio/power circuit. A carrier plus daughterboard must list the total required parts and separately identify both board outlines. The common leaf is not free circuitry omitted from sensor budgets.

Board 01 uses the owner's specified D:/MotoNode_ignition_revD2 native project as its ignition baseline. TCI and CDI remain functional sections of that one physical hub board and its one combined BOM. Do not remove modes or output channels for cost. Universal compatibility requires a documented interface and configuration matrix; AC-CDI exciter input, smart coils, points, missing-tooth patterns and additional OEM families are not inferred from the existing module name.

Newly discovered D:/MotoNodeIQ contains routed ESP32-S3/CAN hub, front and rear projects, unlike the C6/R53/LIN target architecture. Preserve and audit those sources for reusable power/output designs; their existence does not silently replace the approved radio/bus architecture. Their recorded outlines (135 x 98, 120 x 88 and 115 x 85 mm) exceed the requested size.

## Shared electrical and mechanical contract

1. Board 01 has one closed 101.6 x 76.2 mm Edge.Cuts outline; boards 02-19 each have one closed 50.8 x 50.8 mm outline. Connector-body overhang, antenna placement and off-board parts are dimensioned separately. Mounting and assembly clearances are checked against footprints.
1a. Every field-wire connection uses a specified lever or press-latch spring terminal accepting stripped solid or stranded wire without crimping or installation soldering. Exact MPN, pin count, pitch, footprint, wire gauge, temperature and current/voltage rating are checked. The PCB connection itself is soldered during assembly. No connector is assumed sealed or vibration-qualified without evidence; the enclosure and strain relief remain explicit installation requirements.
2. Select layer count per board after routing-density and return-path review. RF and high-current boards must not be forced into a two-layer assumption merely because the outline is small. Fabrication costs are reported separately.
3. Route current-carrying conductors from calculated simultaneous load, copper thickness, temperature rise and connector derating. A MOSFET's headline current is not a board or harness rating.
4. Battery input protection must specify continuous voltage, cranking, reverse polarity, jump-start and transient envelope. TVS pulse rating does not establish sustained load-dump capability. No vehicle-transient compliance claim without the appropriate energy and test evidence.
5. Wireless leaves use CHG+ and CHG- only for charging. Local sensor wiring stays at the leaf. Charging-disable hardware, cell chemistry, temperature inhibit, charge current and supply-return behavior must be explicit. Do not charge a protected Li-ion cell with an unspecified rail.
6. Isolated load returns are mandatory for low-side outputs. A chassis-grounded lamp bypasses a low-side switch. Bike compatibility and harness changes must be documented.
7. Overcurrent trip hardware must turn the affected output off and hold it off independently of a stalled/reset MCU. Deliberate reset/re-enable is defined. Backup protection must address a failed-short power switch and upstream harness fault.
8. Kill and brake connector topology must match a real electrical interface. Plain pass-through conductors do not themselves implement an ignition kill or fail-passive replacement controller.
9. Radio antenna keepouts, reference stackup and return vias follow the manufacturer's layout guidance. RF layout/ERC do not establish RF performance or certification.
10. Thermal, sensor calibration, hydraulic mounting, environmental sealing and ignition bench performance remain physical validation tasks after ECAD checks.

## Specific corrections required before reusing references

- Front RevG: reassess the 30 A nominal trip, 1 ms input filtering and slow gate ramp against measured short-circuit SOA and lamp inrush. Replace firmware-only fault persistence with a defined hardware latch where required by the contract.
- Front RevG: verify TVS clamp against every downstream absolute maximum and operating rating; LMR51430 is specified for up to 36 V operation and the power MOSFET is 40 V. Account for wiring overshoot, component tolerance and capacitor rating.
- Front RevG: replace the old battery-input arrangement with the documented hub-fed architecture and coordinate backup protection at the power source. Confirm copper and connector allocation on the new outline.
- Ignition RevD2: design the custom flyback transformer, close load-dump/jump-start limitations, verify CDI pulse current/di-dt, implement firmware fault response and confirm real coil compatibility. The supplied board has no routed tracks.
- Firmware: reconcile the 56-, 48- and 80-byte branches before assigning GPIOs. Existing Android v2 baseline is preserved; protocol compatibility is not inferred from shared UUIDs.

## Budget method and current feasibility status

The strict $25 cap applies to boards 02-19; board 01 has no numerical ceiling until the owner supplies one. Every physical board still needs a complete, auditable quantity-one parts total. Each BOM line records exact MPN, vendor, currency, available unit quantity, actual minimum purchase, quote date, unit price and extended price. Bulk pack outlay is reported separately from theoretical per-piece allocation. Missing prices, estimated prices and out-of-stock substitutions cannot produce a verified total.

Required off-board items have a second table: antenna, battery, actuator, pressure transducer, external sensor, display and harness. Existing motorcycle lamps/coils/senders are identified as existing vehicle equipment, with their electrical limits. If a board depends on a newly purchased off-board item, both board-only and complete-subsystem totals are shown. Board-only compliance must not be advertised as complete-subsystem compliance.

Current state (2026-10-03): board 02 has a verified quantity-one $22.18 installed-parts BOM, press-latch connectors and a checked routed prototype PCB. It still needs physical bench and vehicle-envelope validation. The integrated hub's selected S3/C6/transformer/HV-terminal subset costs $25.96 before most components; the former $25 cap is lifted for this board, but the complete total remains unknown. The selected wireless-leaf connector/cell/radio/charger/RF subset is $27.11 before the remaining circuitry; its $25 cap still requires redesign or a changed constraint. The historical ignition CSV is quantity-100 and mostly estimated, and the front BOM has no price columns.

If a complete subsystem cannot meet cost, size or protection limits, identify the exact conflict and alternatives. Do not silently omit protection, use a larger board, change quantities, remove a required transducer or claim finished manufacturing files for an unresolved design.

## Deliverables and acceptance for each implemented circuit

- Native KiCad 10 project, schematic sheets, PCB, local symbol/footprint libraries and required design-rule files.
- Pin-level netlist, exact populated BOM and separate optional/DNP variants; source links for selected parts.
- Readable schematic PDF and board images, plus dimensions and connector pinouts.
- Routed PCB with filled zones and zero unconnected required pads; current/return-path and critical-loop review.
- Fresh KiCad 10 ERC and DRC reports, schematic-to-board parity check, documented disposition of every exclusion. Imported historical reports are clearly marked historical.
- Gerber and drill outputs exported from the final checked board; schematic and PCB version/hash association recorded.
- For boards 02-19, cost total strictly < $25 at the agreed quantity or explicit constraint-failure status. For board 01, report a complete quantity-one cost without an arbitrary ceiling.
- No fabrication-ready status for a board with unresolved electrical ratings, interfaces, transformer design, clearance or routing problems.

## Execution order

Use the verified D:/Documents/bin KiCad 10.0.6 runtime. Complete the supply and integrated hub contracts first, then the common leaf, sensor variants, load controllers and advisory interfaces. Board 20 is an ignition integration review attached to board 01, with no fabrication package of its own.

The owner approved the brief and selected subagents for implementation. The amendments above supersede the earlier square-hub and separate-ignition instructions wherever the individual plans have not yet been refreshed.

## Evidence links

- [NodeIQ project archive index](https://drive.google.com/file/d/1k5VXgUaw4gKJ3OmYuqNenXqX9OFneh4l/view)
- [NotebookLM technical handoff](https://drive.google.com/file/d/1Dcx_r-sB0pFiu1tLedW1sezz_WBa8BXu/view)
- [Front-module handoff](https://drive.google.com/file/d/1HTxPmxi8xRE64GdaBCNbQ89VgpI0TqED/view)
- [Front RevG KiCad 10 source archive](https://drive.google.com/file/d/157c9rE8rzImjD9naf93F87BDqy76aOqv/view)
- [KiCad 10.0.6 release](https://www.kicad.org/blog/2026/08/KiCad-10.0.6-Release/)
- [TI CC2340R5 family](https://www.ti.com/product/CC2340R5)
- [TI R53 reference design](https://www.ti.com/tool/LP-EM-CC2340R53)
- [TI LMR51430](https://www.ti.com/product/LMR51430)
- [Infineon IPD50N04S4L-08](https://www.infineon.com/part/IPD50N04S4L-08)
- [Seeed XIAO ESP32-C6 and listed accessories](https://www.seeedstudio.com/Seeed-Studio-XIAO-ESP32C6-p-5884.html)

