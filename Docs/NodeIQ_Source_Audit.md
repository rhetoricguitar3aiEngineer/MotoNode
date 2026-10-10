# NodeIQ source audit

2026-10-02. Read-only investigation of local and connected project sources. This report does not certify any imported circuit or firmware.

## Sources found and inspected

| Source | Observed evidence | Limits |
| --- | --- | --- |
| Downloads/MotoNode_ignition_revD2_kicad10.zip and duplicate _1.zip | Identical SHA-256; editable schematics, placed PCB, project libraries, generation scripts, simulation decks and historical reports | README says simulated, not built; PCB unrouted; quantity-100 BOM |
| Downloads/MotoNode_ignition_schematic.pdf | File present | Visual review not yet performed; conclusions here use editable source and README, not PDF rendering |
| Drive front RevG KiCad 10 ZIP | Downloaded and extracted; 3 child sheets, root schematic, BOM, local LIN symbol and README | No PCB in package; no build/bench test; imported ERC excludes several library/footprint checks |
| Drive NotebookLM handoff dated September 25 | Read architecture, subsystem list, firmware/app history, reported defects, product principles | Reconstructed context; not proof of hardware implementation |
| Drive front-module handoff dated October 2 | Read low-side outputs, dedicated brake/kill, LIN, charging/power/harness decisions and remaining design work | Refers to concept RevF; RevG is a later editable reference |
| Drive archive index updated October 2 | Reviewed version and provenance entries; 106 categorized files listed | An index is not a complete content audit of its 106 files |
| OneDrive/Desktop/MotoNodeTelemetry source tree | Read README and firmware initialization/pin map; local Android source and build artifacts found | Older 56-byte telemetry branch; no compile, flash or field test performed |
| Node IQ chat context | Read Create ESP32 GPS Code, Summarize front module, and NodeIQ Drive Archive Index | Chat claims are context, not fresh validation; no messages sent to other chats |
| KiCad installation | KiCad 9.0 found under Program Files; signed KiCad 10.0.6 installer found in Downloads | KiCad 10 has not been installed or run in this investigation |

Initial search covered project-name filenames in Documents, Downloads and OneDrive, including the redirected Desktop, plus selected text files and visible project chats. Following the owner's direction, a D: filename search found D:/MotoNode_ignition_revD2 and D:/MotoNodeIQ. The latter contains routed hub/front/rear projects and generator sources. Their README describes an ESP32-S3/CAN design sized for a 2003 Suzuki Katana 600, with large board outlines and historical zero-violation check claims. These are additional reference artifacts; those checks have not been independently rerun here. The D: ignition README/verification were read and its native source compared with the downloaded reference. No exhaustive all-drive/all-file audit, phone inspection or content audit of all 106 archived assets is claimed. Marketing images and videos are not electrical specifications.

The owner selected the D: RevD2 ignition as the baseline for one universal ignition module. The implementation plan now keeps four TCI channels and the CDI-capable channel on one physical board, with a combined BOM. Documented modes and restrictions must be distinguished from unsupported ignition families.

## Cost audit

The ignition CSV has 102 component rows representing 215 parts. Of those rows, 96 label their price source as `est`. Quantity times listed unit price totals $23.615, rounded to $23.62. The sum of already-rounded/truncated line-extension values is $23.52. The README instead states $23.59. All are quantity-100 figures and cannot establish the requested quantity-one cap.

The front RevG BOM has part names, MPNs, footprints and quantities but no prices. It includes range-style reference fields and a `CTH?` entry, which should be reconciled against a fresh schematic-derived BOM before ordering.

No newly designed circuit has a verified cost below $25. No production or single-prototype quote has been fabricated for this report.

## Electrical and layout findings

Front RevG retains a firmware-owned fault latch after comparator gate shutdown. Its README explicitly leaves lamp inrush, short-circuit MOSFET SOA, PCB Kelvin routing, MOSFET characteristics and bike kill behavior open. Its 30 A nominal trip and 1 ms filtering are not established as suitable for actual loads. Its low-side topology requires isolated returns.

The front package's historical ERC says zero messages but lists ignored library-symbol, symbol-library mismatch, footprint-link and footprint-filter checks, among others. That result is not a footprint or layout verification and is not a fresh run on a new board.

Ignition RevD2 has a placed/netted but unrouted PCB. Its historical report says 493 unconnected items. Its simulation report explicitly leaves load dump and 24 V jump start unresolved, and says real transformer design, thermal behavior and EMC have not been verified. The CDI design restricts coil primary inductance and requires firmware action after loss of ARM_OK. Supplied behavioral simulations are not vendor-model or bench proof of a replacement ignition controller.

The power components of any new load board require a complete rating audit. The front reference names a 36 V-input buck and 40 V output MOSFETs. TVS selection, pulse duration, clamp tolerance, wiring overshoot and capacitor ratings must be coordinated before copying that circuit into a compact PCB.

## Version findings

The target low-power architecture differs from the local ESP32/NEO-6M/MPU6050 prototype. Local firmware describes GPS GPIO16/17 and I2C GPIO21/22, with a 56-byte packet. Chat and archive sources separately describe 48-byte and 80-byte telemetry branches. Shared BLE UUIDs do not make those packet formats compatible.

The archive identifies Android v2 as the authoritative lineage and flags reported IMU calibration, route-map, SD logging and GPS startup defects. Hardware drawings do not prove those software defects resolved. Any new MCU pin assignment needs a matching firmware plan.

## Required next evidence

Actual bike/test fixture, native kill topology, ignition family/coil limits, steady and inrush load currents, connector/harness ratings, pressure and travel ranges, chosen TPMS/display/radar interfaces, cell chemistry and charging temperature limits, and purchasable quantity-one parts prices.

Fresh KiCad 10 capture/ERC, PCB routing/DRC, schematic parity, dimensional checks and electrical review remain future work. No new Gerbers or fabrication-ready PCB are being claimed.

## References

- [Project archive](https://drive.google.com/file/d/1k5VXgUaw4gKJ3OmYuqNenXqX9OFneh4l/view)
- [Technical handoff](https://drive.google.com/file/d/1Dcx_r-sB0pFiu1tLedW1sezz_WBa8BXu/view)
- [Front source ZIP](https://drive.google.com/file/d/157c9rE8rzImjD9naf93F87BDqy76aOqv/view)
- [Front handoff](https://drive.google.com/file/d/1HTxPmxi8xRE64GdaBCNbQ89VgpI0TqED/view)

