# Project instructions

## Schematics (permanent rule — applies to ANY and ALL schematic work)
- Every connection in a schematic must be drawn as a visible wire between the pins it connects.
- Net labels, global labels or "label-per-pin" stubs must NOT be used to make signal connections.
- The only exceptions are:
  - power rails, which may use power symbols / power-rail labels (GND, +3V3, VIN, VBUS, ...);
  - genuine off-page connections (hierarchical sheet pins / connectors to another sheet or board).
- Generated schematics must be checked for this (and pass ERC) before they are delivered.
