# ECLIPSE Tree: design notes

## 1. Concept

An old cedar elm (*Ulmus crassifolia*), the Texan elm with a stout trunk, a dense crown of
slender, drooping branchlets, tiny leaves and small winged seeds (samaras). The idea is that
**the tree is the luminaire**. Light comes out of four parts of it, each using a different
optical principle:

| Part | Optic | What you see |
|---|---|---|
| Leaves | 800 × 0402 LEDs on flex sprays, direct emission | Crisp sparkle across the crown, like sun on leaves |
| Seeds | 657 end-glow PMMA fibres into diffusing epoxy samaras | Soft points of glow deep among the twigs |
| Trunk | PMMA light-guide core (TIR), light extracted where the bronze bark is split | Amber light seeping out of the fissures, the burl's knot holes and the root buttresses |
| Roots | Opal PMMA band lit from a white light chamber in the base | A glowing ring at the foot, also used as the night-light |

All four are driven from the same four colour channels, so they dim and shift colour
together, and warm (2700 K) and cool (6500 K) sources are interleaved in every system.

## 2. The tree (procedural, `mechanical/tree_gen.py`)

* **Trunk.** A cubic-Bézier S-curve from the base to the burl, 44 mm at the foot tapering to
  ≈34 mm, with a slight gnarl (±5 % radius ripple, lateral wander). It has six buttress
  roots that spread over the base top, kept out of the touch window's sector.
* **Burl.** A Ø68 mm fork knot (two cast halves) that houses the hub light engine.
* **Limbs to twigs.** 4 limbs split sympodially (2-3 children) down to 40 sprig twigs. Each
  carries n sprigs and is sized by the pipe model, d = 2.6·n^0.62 mm (limbs ≈11 mm, twigs
  2.4 mm). Large limbs lift slightly while small ones droop.
* **Spur systems.** Every structural branch sprouts 5-12 spur twigs. Each spur forks again,
  up to two more levels (75 % chance of two children), and ends in a samara: 1,222 spur
  segments and 657 tips in total. That's 5× the previous crown.
* **Seeded and reproducible.** `SEED = 11`. The same skeleton drives the CAD, the renders,
  the bending jigs and the wiring map.

## 3. Mechanical architecture

| Part | Notes |
|---|---|
| Base (unchanged) | Graphite 6061 shell with touch glass, opal root-glow band, white steel weight/reflector, steel plinth, cork foot |
| Trunk shell | Lost-wax cast silicon bronze, 2.5 mm wall, two halves. The fissures are cast through the wall, following an artwork pattern derived from the render shader's Voronoi network, so they are real openings. A Ø14 brass spigot is brazed in and fits the base socket (M4 set screw) |
| Trunk core | Cast light-diffusing PMMA rod (LED grade, low haze) inside the shell, with a 6 mm bore for the harness. It is polished, with a white extraction-dot print behind each fissure and a mirrored foot |
| Burl | Ø68 silicon-bronze halves (2 × M2). Knot holes are open to a diffusing PMMA insert. It holds the hub on a ledge, and the hub's 4 fibre ferrules sit on top |
| Limbs | 10-11 mm brass tube (hollow, 55 % less mass). Branches below 6 mm and all spurs are solid brass rod or wire, jig-formed from `parts.json` and brazed |
| Optical fibres | 657 × 0.5 mm end-glow PMMA fibre in four bundles (one per channel, ≈164 each), laid in the branch grooves with the sprig wires. Each fibre end is cleaved and dip-moulded into a samara |
| Sprigs | 40 flex sprays (20 × 0402 LEDs), crimped and soldered to the twig tips |
| Finish | Liver-of-sulphur bark patina plus matte lacquer. The fissures are masked so the PMMA shows |

**Stability** (from the CAD skeleton, with tube and shell wall fractions): total ≈2.4 kg
(crown and trunk ≈1.2 kg). The centre of gravity is 12 mm from the base centre, 63 mm
inside the base edge.

## 4. Optics

### 4.1 Trunk light-guide

* **Source.** The hub's 8 bottom LEDs (2 per channel, 2835, 25 mA) sit on a ring at r = 12.6 mm,
  facing down onto the polished top face of the PMMA core (r ≈ 14 mm) through optical
  silicone gel.
* **Transport.** By total internal reflection: PMMA n = 1.49, critical angle 42°. Coupled
  light at up to ±60° in air is refracted to within ±35.5° in the rod and stays guided. The
  S-curve's bend radii are > 10× the rod radius, so bend loss is small.
* **Extraction.** Where the bronze is split, a matte white dot print on the rod surface
  scatters light out of TIR, and the light leaves through the opening. A diffusing (low-haze)
  core grade evens out the brightness from top to bottom. The mirrored foot sends the rest
  back up, and part of it spills into the roots.
* **Brightness.** The light engine delivers ≈16 × 12 lm ≈ 190 lm (an estimate), half into
  the core. With about 50 % extraction efficiency, that's ≈45 lm out of the fissures. That
  is a glow, not task light, as intended.

### 4.2 Fibres and samaras

* The hub's 8 top LEDs feed 4 ferrules (≈7 mm bundles, one over each channel's LED pair),
  with index gel. Each bundle carries ≈164 fibres, routed so every limb gets fibres from all
  four bundles, which interleaves warm and cool.
* An end-glow fibre puts out a 0.5 mm point, too harsh on its own. A 6 × 4 × 1.2 mm samara of
  diffusing epoxy (0.2 % TiO₂) moulded on the tip turns it into a soft, seed-shaped glow,
  visible from all sides.

### 4.3 Leaves

The 0402 LEDs are direct, point-like emitters with about 120° viewing angle, so they give the
crown its sparkle. They are the main source of light: ≈450-550 lm.

## 5. Electronics

### 5.1 Architecture (core board unchanged)

```
USB-C ─► PTC/TVS ─► VIN 9 V ─┬─► TPS61165 ─► W1: [hub engine 4×2835] ─► 10 sprigs ─┐
 (CH224K asks for 9 V)       ├─► TPS61165 ─► C1: [hub engine]        ─► 10 sprigs  │  all in series,
                             ├─► TPS61165 ─► W2: [hub engine]        ─► 10 sprigs  │  100 mA per channel
                             ├─► TPS61165 ─► C2: [hub engine]        ─► 10 sprigs ─┘
                             └─► AMS1117 ─► ATtiny1616 (touch, PWM_W/PWM_C, GLOW_PWM, NTC)
```

### 5.2 String budget

* Elements per channel: 1 hub group (4 × 2835 in parallel, 25 mA each, Vf ≈ 2.95 V) plus
  10 sprigs (20 × 0402 in parallel, 5 mA each, Vf ≈ 2.85 V). That is ≈31.5 V typical and
  ≈33.5 V worst case, inside the TPS61165's 38 V OVP.
* Boost at 9 V in: D ≈ 0.76, I_in ≈ 0.41 A per channel, inductor peak ≈0.70 A, within the
  1.2 A switch limit and the 1.6 A Isat.
* Power: 4 × 0.1 A × 31.5 V ≈ 12.6 W maximum, capped at ≈8.5 W by firmware. The total from
  a 9 V / 2 A (18 W) charger is ≈1.1 A.

### 5.3 Hub light engine (Ø56, 2 layers, white mask)

* **Sprig lands.** 44 angular slots; each channel owns 10 consecutive sprig land pairs
  (A outer at r 25.0, K inner at r 21.3) plus a gap slot.
* **Light-engine group.** Each channel's group sits in the middle of its sector: 2 LEDs on
  top and 2 on the bottom at r 12.6, ±11°. Between them are an anode arc at r 8.6 (fed from
  the trunk land) and a cathode arc at r 17.5, which returns to the gap slot and out to the
  first sprig. Vias at r 9.4 and r 15.6 join the two faces.
* **Routing.** The chain diagonals run between the land rings, and the chain returns run
  inward at the last slot. Nothing crosses.
* **Trunk side.** The 10 trunk lands sit around a Ø5 hole. The NTC is at r 4.1.
* **Finish.** White solder mask turns the inside of the burl into a reflector.

### 5.4 Sprig flex (×40)

These are unchanged from the previous revision: 2-layer polyimide, a cedar-elm spray with 20
× 0402 LED leaves, the outline grown 0.5 mm around the copper, and the same `sprig_layout.py`
used by the PCB and the 3D model.

### 5.5 MCU pin map and trunk harness

Both are unchanged; see the core schematic. The harness is 10 × AWG30 PTFE running up the
trunk core's bore, pin for pin (1:1) from core J2 to hub J1. The sprig-to-hub mapping is
in [WIRING.md](WIRING.md).

### 5.6 Thermal

* The heat sources are spread out: 800 leaves at ≈14 mW, and 16 light-engine LEDs at
  ≈75 mW each inside a 180 g bronze burl. The burl rises well under 10 K.
* The PMMA core sees only guided light, and its temperature tracks the burl.
* The crown NTC sits on the hub and derates above 50 °C.

## 6. Firmware behaviour (to implement)

* **Basic controls.** Tap the key to toggle, with a 600 ms fade. Slide the wheel for
  brightness. Hold the key and slide for colour temperature (warm/cool mix at constant flux).
* **Twinkle.** Very slow, slightly different breathing on the four channels, so the crown
  shimmers and the trunk seems to pulse faintly.
* **Night.** The crown dims to embers and the root band breathes. Double-tap the key to
  enter it.
* **Fault handling.** If a channel opens (OVP), blink the glow dot and keep the other three
  running. A 5 V-only supply caps output at 25 %. The NTC derates above 50 °C.

## 7. Assembly sequence

1. **Electronics.** SMT the core board and the hub (two-sided). Build, test and singulate the
   40 sprigs.
2. **Trunk.** Cast the trunk and burl halves. Cast and polish the PMMA core, print its
   extraction dots, then fit the core and the spigot into the trunk shell.
3. **Crown structure.** Jig-form the limbs, branches and spurs from `parts.json`, then braze
   them into the burl seat.
4. **Wires and fibres.** Lay the 80 magnet wires and the 657 fibres in the branch grooves,
   following [WIRING.md](WIRING.md) and the bundle map. Fix them with lacquer.
5. **Tips.** Mould a samara onto each fibre tip. Crimp and solder the sprigs to their twig
   tips.
6. **Hub.** Fit the hub in the burl, solder the sprig and trunk wires, polish and gel the four
   ferrules over the top LEDs, then close the burl halves. Pot the back side and gel the LED
   faces.
7. **Test.** Check each chain on the bench at 34 V with a 100 mA limit: all four optical
   systems of that channel should light.
8. **Finish and install.** Patina and lacquer, masking the leaves, samaras and fissures. Fit
   the trunk into the base and plug the harness into J2.

## 8. Verification status and open items

Done and checked automatically:

* All three boards (core, hub, sprig) pass ERC and DRC with 0 violations, 0 unrouted and
  clean schematic/PCB parity.
* The netlists match the design descriptions.
* Every schematic connection is a drawn wire, with no net labels.
* The CAD solids are valid.

Before building:

* **Optics on a mock-up.** Measure the core coupling and fissure extraction (and tune the
  dot print density), the fibre-bundle coupling efficiency, and how evenly the samaras glow.
  The lumen figures here are estimates.
* **Leaf LEDs.** Choose the exact 0402 and 2835 parts and bins. Check current sharing in the
  parallel groups (one Vf bin per group).
* **Casting.** Fissure apertures as small as 1 mm in a 2.5 mm bronze wall need a casting
  trial. The alternative is to laser-cut a sheet shell after casting.
* **Fibres.** Check that 657 fibres plus 80 wires fit the grooves, and the minimum bend
  radius of 0.5 mm PMMA fibre (about 5 mm) on the tightest twigs.
* **Cost.** This is a hand-built object: the crown forming, fibre laying and casting
  dominate the ≈$123 material BOM and need real quotes and assembly-time estimates.
* The core board datasheet checks from the earlier revisions still apply (CH224K VDD/VBUS,
  TPS61165 pinout).
