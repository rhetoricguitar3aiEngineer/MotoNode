# ECLIPSE Tree: design notes

## 1. Concept

An old cedar elm (*Ulmus crassifolia*), the Texan elm with a stout trunk and a dense, rounded
crown of small leaves and winged seeds (samaras). The idea is that **the tree is the
luminaire**: it should read as a real tree in daylight, and fill with light at night. Light
comes out of four parts of it, each using a different optical principle:

| Part | Optic | What you see |
|---|---|---|
| Leaves | 800 × 0402 LEDs on flex sprays, inside 21,770 leaves of light-diffusing film | Points of light deep in the foliage, and the leaves around them glowing green-gold |
| Seeds | 567 end-glow PMMA fibres into diffusing epoxy samaras | Soft points of glow among the twigs |
| Trunk | PMMA light-guide tube (TIR), light extracted where the bronze bark is split | Amber light seeping out of the bark furrows and the root buttresses |
| Roots | Opal PMMA band lit from a white light chamber in the base | A glowing ring at the foot, also used as the night-light |

All four are driven from the same four colour channels, so they dim and shift colour
together, and warm (2700 K) and cool (6500 K) sources are interleaved in every system.

## 2. The tree (procedural, `mechanical/tree_gen.py`)

The previous revision built the crown top-down (limbs radiating from one knot, then
recursive splits and spurs). It read as a broom on a ball. This revision grows the tree the
way trees grow:

* **Space colonisation** (Runions et al., 2007). 4,200 attraction points fill a rounded,
  gently lobed crown envelope (≈360 × 330 mm, 200-430 mm above the desk), denser toward the
  outside, and open underneath the scaffold limbs. Buds grow 5 mm per step toward the points
  that are nearest to them (influence radius 62 mm), and a point is used up when a bud gets
  within 9 mm. Branches therefore compete for space, fork where the space divides, and fill
  the crown evenly without crossing. 6,200 nodes, 1,174 twig tips.
* **Tropism.** Wood near the crown axis grows slightly upward. Outer wood arches over, and
  the outermost twigs weep a little, as cedar-elm branchlets do.
* **Pipe-model taper.** Every node's radius comes from the number of twig tips it carries,
  r = max(0.4, 0.255 · n^0.71) mm. Wood tapers continuously from the 77 mm bole to 0.8 mm
  twigs, and a fork is always as thick as what grows out of it.
* **Trunk and fork.** A leaning S-curve trunk (centre of the crown over the base centre)
  with a root flare, a slight swelling at the top, and seven half-buried buttress roots kept
  out of the touch window's sector. It divides into three leaders (≈30-37 mm). Each leader
  starts 0.76 × the trunk radius and offset outward, tangent to the trunk surface, so the
  three lobes cover the trunk top: the fork has a natural crotch with no shoulder.
* **Blended wood (renders).** The trunk, roots and every branch thicker than 4.4 mm are
  voxel-remeshed into one body and relaxed, so each branch grows out of its parent with a
  smooth collar.
* **Foliage.** Leaves are set alternately in two ranks, in a nearly flat spray (as elms grow
  them), along every twig that carries up to 4 tips, plus one at each tip: 21,770 leaves,
  4.6-7 mm long, in two tones.
* **Seeded and reproducible.** `SEED = 7`. The same skeleton drives the CAD, the renders,
  the bending jigs, the leaf-cutting file and the wiring map.

## 3. Mechanical architecture

| Part | Notes |
|---|---|
| Base (unchanged) | Graphite 6061 shell with touch glass, opal root-glow band, white steel weight/reflector, steel plinth, cork foot |
| Trunk shell | Lost-wax cast silicon bronze, 2.5 mm wall, two halves, including the root flare, buttress roots and the fork swelling. The fissures are cast through the wall, following an artwork pattern derived from the render shader's Voronoi network (long, narrow furrows along the grain), so they are real openings. A Ø14 brass spigot is brazed in and fits the base socket (M4 set screw) |
| Trunk core | Cast light-diffusing PMMA tube (LED grade, low haze), 8 mm wall, inside the shell. The trunk harness runs up its bore. It is polished, with a white extraction-dot print behind each fissure and a mirrored foot |
| Hub seat | The hub sits on a cast ledge in the fork swelling, 12 mm below the fork, where the trunk is Ø77. The two trunk halves close over it (2 × M2) |
| Leaders and limbs | Wood thicker than Ø12 (3 leaders + 4 scaffold limbs) is cast silicon bronze, 2 mm wall, brazed to the trunk casting |
| Branches and twigs | 21 brass tubes (Ø4-12) and 1,146 solid brass rods and wires (Ø0.8-4), jig-formed from `parts.json` and brazed. About 29 m of wood in total |
| Foliage | 21,770 leaves cut as ≈1,170 twig sprays from 0.125 mm light-diffusing olive PET film (two tones) and bonded to the twigs. The cutting file is `mechanical/out/foliage.stl` |
| Optical fibres | 567 × 0.5 mm end-glow PMMA fibre in four bundles (one per channel, ≈142 each), laid along the wood with the sprig wires. Each fibre end is cleaved and dip-moulded into a samara |
| Sprigs | 40 flex sprays (20 × 0402 LEDs), each grafted onto a branchlet 44 mm behind a twig tip on the outside of the crown, so it runs out along the twig to the crown surface |
| Finish | Grey-brown liver-of-sulphur bark patina plus matte lacquer. The fissures are masked so the PMMA shows |

**Stability** (from the CAD skeleton, with the wall fractions above): total ≈4.1 kg. The
centre of gravity is 8.5 mm from the base centre, 66 mm inside the base edge.

## 4. Optics

### 4.1 Trunk light-guide

* **Source.** The hub's 8 bottom LEDs (2 per channel, 2835, 25 mA) sit on a ring at r = 12.6 mm,
  facing down onto the polished top end of the PMMA tube (bore r ≈ 27 mm, outer r ≈ 35 mm)
  through optical silicone gel. A short PMMA coupling ring under the LED ring carries
  their light out to the tube wall.
* **Transport.** By total internal reflection: PMMA n = 1.49, critical angle 42°. Coupled
  light at up to ±60° in air is refracted to within ±35.5° in the tube wall and stays guided.
  The trunk's bend radii are large compared with the 8 mm wall, so bend loss is small.
* **Extraction.** Where the bronze is split, a matte white dot print on the rod surface
  scatters light out of TIR, and the light leaves through the opening. A diffusing (low-haze)
  core grade evens out the brightness from top to bottom. The mirrored foot sends the rest
  back up, and part of it spills into the roots.
* **Brightness.** The light engine delivers ≈16 × 12 lm ≈ 190 lm (an estimate), half into
  the core. With about 50 % extraction efficiency, that's ≈45 lm out of the fissures. That
  is a glow, not task light, as intended.

### 4.2 Fibres and samaras

* The hub's 8 top LEDs feed 4 ferrules (≈6.5 mm bundles, one over each channel's LED pair),
  with index gel. Each bundle carries ≈142 fibres, routed so every leader gets fibres from
  all four bundles, which interleaves warm and cool.
* An end-glow fibre puts out a 0.5 mm point, too harsh on its own. A 3.6 × 2.4 × 0.9 mm
  samara of diffusing epoxy (0.2 % TiO₂) moulded on the tip turns it into a soft,
  seed-shaped glow, visible from all sides. Every other twig tip carries one.

### 4.3 Leaves

* The 0402 LEDs are direct, point-like emitters with about 120° viewing angle. They are the
  main source of light (≈450-550 lm) and give the crown its sparkle.
* Each LED spray sits inside the leaf film. The film is a light-diffusing (bulk-scattering)
  PET, so the leaves near an LED transmit and scatter part of its light: the foliage glows
  green-gold from inside around every spray, and the crown reads as a lit tree, not a cloud
  of points. In daylight the same film reads as ordinary glossy leaves.

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

### 5.3 Hub light engine (Ø56, 2 layers, white mask, in the trunk fork)

* **Sprig lands.** 44 angular slots; each channel owns 10 consecutive sprig land pairs
  (A outer at r 25.0, K inner at r 21.3) plus a gap slot.
* **Light-engine group.** Each channel's group sits in the middle of its sector: 2 LEDs on
  top and 2 on the bottom at r 12.6, ±11°. Between them are an anode arc at r 8.6 (fed from
  the trunk land) and a cathode arc at r 17.5, which returns to the gap slot and out to the
  first sprig. Vias at r 9.4 and r 15.6 join the two faces.
* **Routing.** The chain diagonals run between the land rings, and the chain returns run
  inward at the last slot. Nothing crosses.
* **Trunk side.** The 10 trunk lands sit around a Ø5 hole. The NTC is at r 4.1.
* **Finish.** White solder mask turns the inside of the fork swelling into a reflector.

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
  ≈75 mW each inside the fork of a ≈1 kg bronze casting. The fork rises well under 10 K.
* The PMMA core sees only guided light, and its temperature tracks the casting.
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
2. **Trunk.** Cast the trunk halves and the leader/limb pieces. Cast and polish the PMMA
   tube, print its extraction dots, then fit the tube and the spigot into one trunk half.
3. **Crown structure.** Jig-form the branch tubes and twig rods from `parts.json` and braze
   them onto the leader castings.
4. **Wires and fibres.** Lay the 80 magnet wires and the 567 fibres along the wood,
   following [WIRING.md](WIRING.md) and the bundle map. Fix them with lacquer.
5. **Tips.** Mould a samara onto each fibre tip. Crimp and solder the sprigs onto their
   branchlets.
6. **Hub.** Seat the hub on its ledge in the fork, solder the sprig and trunk wires, polish
   and gel the four ferrules over the top LEDs, then braze on the leaders and close the trunk
   halves. Pot the back side and gel the LED faces.
7. **Test.** Check each chain on the bench at 34 V with a 100 mA limit: all four optical
   systems of that channel should light.
8. **Finish, foliage and install.** Patina and lacquer, masking the leaves, samaras and
   fissures. Bond on the leaf-film sprays. Fit the trunk into the base and plug the harness
   into J2.

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
* **Hub fit.** The hub (Ø56) sits in a Ø77 trunk with a 2.5 mm wall, which leaves ≈8 mm per
  side for the ledge and the wires. Check this on the casting model.
* **Foliage.** Bonding ≈1,170 leaf sprays is the longest hand step. Trial the film (haze,
  colour, heat ageing next to the LEDs) and a spray-per-twig bonding jig.
* **Fibres.** Check how 567 fibres plus 80 wires lie along the wood, and the minimum bend
  radius of 0.5 mm PMMA fibre (about 5 mm) on the tightest twigs.
* **Cost.** This is a hand-built object: the crown forming, foliage, fibre laying and
  casting dominate the ≈$147 material BOM and need real quotes and assembly-time estimates.
* The core board datasheet checks from the earlier revisions still apply (CH224K VDD/VBUS,
  TPS61165 pinout).
