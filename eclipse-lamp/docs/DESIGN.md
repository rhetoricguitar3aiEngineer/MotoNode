# ECLIPSE Tree: design notes

## 1. Concept

A desk lamp grown as a cedar elm (*Ulmus crassifolia*), the Texan elm with a small crown,
slender drooping branchlets and tiny leaves. **Every leaf is an LED.**

* **An intricate, believable tree.** The skeleton is generated procedurally
  (`mechanical/tree_gen.py`, seeded, so it can be reproduced):
  * An S-curved trunk rises from the rear of the base to a burl at 158 mm.
  * Four limbs grow from the burl, and each splits recursively (sympodial, with 2-3 children)
    down to its twigs.
  * Diameters follow the pipe model (d ∝ n^0.52 for n carried sprigs), from a 14 mm trunk to
    1.6 mm twigs.
  * Large limbs lift slightly while small twigs droop (gravitropism), and each segment
    wanders a little.
  * 189 spur twigs (0.4-1.3 mm, some forked again) make the crown read as dense and finely
    divided.
  * In total: 75 structural branches, 189 spurs and 4.7 m of formed brass.
* **Leaves as light.** Each of the 40 twig tips carries a cedar-elm spray: a 2-layer
  polyimide flex with a 44 mm main stem, three alternate side shoots and 20 petioles. Each
  petiole ends in an 0402 LED (1.0 × 0.5 mm). The sprays sag naturally under their own
  weight, and every leaf glows.
* **Warm and cool everywhere.** Sprigs are dealt round the crown to channels W1, C1, W2, C2 in
  turn. Warm (2700 K) and cool (6500 K) leaves are therefore interleaved throughout, and the
  colour temperature mixes evenly with no visible patches.
* **Roots of light.** The opal band at the foot of the base glows from an internal light
  chamber, as a breathing night-light and as touch feedback.

## 2. Mechanical architecture

| Part | Notes |
|---|---|
| Base (unchanged) | Graphite 6061 shell with the 3 mm touch glass, opal root-glow band, white steel weight/reflector, steel plinth, cork foot. The trunk socket (M4 set screw) is at the rear |
| Trunk | 14 × 2 mm brass tube, S-bent, with a spun root flare brazed on. The 10-wire harness runs inside |
| Burl | Two lost-wax silicon-bronze halves (2 × M2) around the fork. They house the hub PCB, which is potted in flexible epoxy |
| Limbs → twigs | Solid brass rod from 6 mm down to 1.6 mm. Bent on a jig printed from the CAD skeleton (`parts.json`) and brazed at the forks. A 0.3 mm groove along the underside carries the sprig wires |
| Spurs | 0.8-2.6 mm brass wire, brazed on. Decorative only |
| Sprigs | 40 flex sprays. Each root is crimped to its twig tip with a 0.3 mm brass sleeve, and the twig-tip wire pair is soldered to its A/K pads |
| Finish | Liver-of-sulphur patina (grey-brown bark) plus matte lacquer over the whole tree, which also seals the wire grooves |

**Stability** (from CAD volumes): total ≈1.67 kg. The crown (≈0.46 kg including trunk and
burl) is balanced around the trunk, so the centre of gravity sits only 8 mm from the base
centre (66 mm inside the base edge). Tipping it takes ≈11 N pressed down on the outermost
twig (≈95 mm beyond the base edge), or a sideways push of ≈3.5 N at crown height. That is
typical for a desk lamp of this size.

## 3. Electronics

### 3.1 Architecture

```
USB-C ─► PTC/TVS ─► VIN 9 V ─┬─► TPS61165 #1 ─► W1 chain: 10 sprigs in series ─┐
 (CH224K asks for 9 V)       ├─► TPS61165 #2 ─► C1 chain                       │  hub board in the
                             ├─► TPS61165 #3 ─► W2 chain                       ├─ burl: 40 land pairs,
                             ├─► TPS61165 #4 ─► C2 chain                       │  chaining traces, NTC
                             └─► AMS1117 ─► ATtiny1616 (touch, PWM_W/PWM_C, GLOW_PWM, NTC)
                                                     │
      each sprig = 20 × 0402 LED in parallel ◄───────┘  80 magnet wires along the branches
```

The **core board is electrically unchanged.** The hub reproduces the old 10-pin harness
pinout (§3.6), so the drivers, the touch MCU and the routed core PCB carry over. Only the
connector's silkscreen and value changed ("TO TREE HUB").

### 3.2 LED drive

* Leaf: 0402 white, If ≈ 5 mA, Vf ≈ 2.8-2.9 V, about 14 mW per leaf.
* Sprig: 20 leaves in parallel share 100 mA. With LEDs from one Vf bin (±25 mV), the leaf
  currents stay within about ±15 %, which you can't see across a dense crown. If one LED
  fails open, its 19 neighbours each carry about 5 % more current. If one fails short, that
  sprig goes dark but the chain keeps working.
* Chain: 10 sprigs in series give ≈28-29.5 V, below the TPS61165's 38 V OVP. A broken wire
  or sprig opens the chain, which the OVP catches; the firmware sees the dropout and keeps
  the other channels running.
* Power: 4 × 0.1 A × ≈29 V ≈ 11.4 W max, capped at ≈8.5 W by firmware. At about 60 lm/W for
  the 0402 parts that gives ≈450-550 lm in total (an estimate that needs measuring).
* The boost numbers are the same as before: at 9 V in, D ≈ 0.74 and the inductor peak is
  ≈0.66 A, within the 1.2 A switch limit.

### 3.3 Hub board (Ø36 mm, in the burl)

* 44 angular slots, with 10 consecutive slots per channel plus one empty gap slot. Each slot
  has an outer A land and an inner K land.
* Each sprig's K land connects to the next sprig's A land with a short diagonal trace.
* The channel's anode feed runs inward through the gap slot, and its cathode return runs
  inward from the last slot. Ten trunk-wire lands sit around a Ø4 hole that the harness comes
  up through.
* Everything is on one copper layer and nothing crosses. The NTC (10 k, B3380) sits on the
  hub and reports the crown temperature.

### 3.4 Sprig flex (40 per lamp)

* 2-layer polyimide, 0.11 mm, ½ oz, bronze-coloured coverlay, ENIG. The outline is grown 0.5 mm
  around the copper (shapely buffer), so the flex *is* the twig: about 1 mm wide.
* Top copper carries the anode bus along every stem to each LED's inner pad. Bottom copper
  carries the cathode bus along the same paths, coming up through a 0.45/0.2 mm via just
  beyond each LED's outer pad. Tracks are 0.15 mm.
* The leaf layout (`electronics/tools/sprig_layout.py`) is shared by the PCB generator and the
  3D tree, so the model and the board match exactly. The minimum spacing between LEDs is
  2.5 mm.
* One design, two builds: 20 sprigs with 2700 K LEDs and 20 with 6500 K. Panelise them, then
  laser-cut the outline.

### 3.5 MCU pin map (ATtiny1616-S, unchanged)

| Pin | Function | Notes |
|---|---|---|
| PA0 | UPDI | pogo pads J3 (DNP header) |
| PA1 | VSENSE | VIN × 15k/(100k+15k); 9 V → 1.17 V (2.5 V internal ref) |
| PA2 | PD_PG | CH224K power-good |
| PA3 | NTC | crown NTC on the hub, 10 k pull-up, 100 nF |
| PA4 | Touch key | PTC, 1 k series |
| PA5-PA7 | Touch wheel A/B/C | PTC, 1 k series |
| PB0 | PWM_W (TCA0 WO0) | CTRL of the W1 and W2 drivers |
| PB1 | PWM_C (TCA0 WO1) | CTRL of the C1 and C2 drivers |
| PB2 | Glow dot (TCA0 WO2) | 0603 LED under the glass |
| PC0 | GLOW_PWM (TCD0 WOC) | AO3400A → 8 rim LEDs → root-glow band |

### 3.6 Trunk harness (10 × AWG30 PTFE, 1:1: core J2 ↔ hub J1)

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | C1 chain return | 6 | NTC return (GND) |
| 2 | C1 chain feed | 7 | W2 chain return |
| 3 | W1 chain feed | 8 | W2 chain feed |
| 4 | W1 chain return | 9 | C2 chain feed |
| 5 | NTC | 10 | C2 chain return |

The sprig-to-hub assignment (which twig, which channel, which chain position, which hub
slot) is in [WIRING.md](WIRING.md), generated from the seeded tree.

### 3.7 Thermal

The heat is spread across 800 tiny sources at about 14 mW each, plus the brass. Each leaf
sits only a few kelvin above ambient and the tree stays cool to the touch. The hottest parts
are the boost converters in the base, which is unchanged. The crown NTC is kept as a
safeguard (derate above 50 °C).

## 4. Firmware behaviour (to implement)

* Tap the key to toggle, with a 600 ms fade. Slide the wheel for brightness (logarithmic). Hold
  the key and slide for colour temperature (warm/cool mix at constant flux).
* "Twinkle" option: slow, slightly different breathing on the four channels, so the crown
  shimmers like leaves moving.
* Night: the crown dims to embers (≈1 %), and the root-glow band breathes. Double-tap the key
  to toggle.
* Open-chain detection: if one channel's FB drops out, show a short blink pattern on the glow dot and carry on with the other three.
* Protection: a 5 V-only supply caps output at 25 %. The crown NTC derates above 50 °C.

## 5. Assembly sequence

1. SMT the core board and the hub board. Assemble the sprig panels (0402 LEDs, reflow), test
   each sprig at 100 mA, then laser-singulate them.
2. Bend the limbs, branches and spurs on jigs printed from `parts.json`, then braze them to
   the trunk at the burl.
3. Lay the 80 magnet wires in the branch grooves from each twig tip to the burl, following
   [WIRING.md](WIRING.md). Tack them with lacquer.
4. Crimp and solder each sprig to its twig tip. Run a continuity and polarity test per chain
   on the hub lands before soldering (a bench supply at 30 V with 100 mA current limit
   lights the whole chain).
5. Solder the wires to the hub, solder the 10 trunk wires, close the burl halves and pot the
   hub.
6. Patina and lacquer the whole tree. Mask the LED leaves, or use a lacquer that is safe on
   the LED lenses.
7. Fit the trunk into the base socket, plug the harness into J2, and close the base.

## 6. Verification status and open items

Done and checked automatically:

* All three boards (core, hub, sprig) pass ERC and DRC with 0 violations, 0 unrouted and
  clean schematic/PCB parity.
* The KiCad netlists equal the design descriptions (`verify_netlist.py`).
* Every schematic connection is a drawn wire, with no net labels.
* The CAD solids are valid, and the shared sprig layout guarantees model/PCB agreement.

Before building:

* **Leaf LEDs.** Choose the exact 0402 warm and cool parts and their Vf/flux bins, and measure
  the current sharing on a real sprig.
* **Flex.** Check the bend radius at the sprig root and the fatigue of the 0.15 mm traces
  where it drapes (consider a stiffener at the root tab). Confirm the fab can laser-cut the
  ~1 mm outline.
* **Wire routing.** Check that 80 × 0.15 mm wires plus the patina fit the branch grooves.
  Check how well the enamel survives brazing heat; wiring is done after brazing for this
  reason.
* **Light output.** The ≈450-550 lm is an estimate. Verify desk illuminance, since this is
  more of an ambient/accent lamp than a task lamp.
* **Lacquer.** It must stay clear on the LEDs over the long term (no yellowing).
* **Craft cost.** Forming the crown is hand work. The $18 in the BOM assumes jig bending and
  needs real quotes.
* The core board datasheet checks from the earlier revision still apply (CH224K VDD/VBUS,
  TPS61165 pinout).
