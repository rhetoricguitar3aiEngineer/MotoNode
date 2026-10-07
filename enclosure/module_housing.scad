// MotoNode: parametric module housing, diffuser lid and controller box.
// Render one part at a time for printing:  part = "housing" | "diffuser" | "controller" | "all"
part = "all";

/* [Module] */
leds_per_module = 8;
led_pitch       = 16.67;  // 60 LED/m strip. Use 6.94 for 144 LED/m
strip_w         = 12.4;   // strip width incl. silicone sleeve (measure yours)
strip_h         = 4.5;    // strip height incl. sleeve
end_margin      = 9;      // room at each end for solder joints + heat-shrink
cable_d         = 4.8;    // pigtail cable diameter
wall            = 1.8;
floor_t         = 1.6;
headroom        = 2.0;    // air gap between LEDs and diffuser (more = smoother light)
lid_t           = 1.6;    // diffuser thickness. 1.6 mm natural PETG diffuses well
lip_h           = 2.0;    // diffuser lip that presses inside the walls
fit             = 0.25;   // clearance per side for press fits
tab_len         = 10;     // mounting tab length at each end (0 = no tabs, use VHB tape)
hole_d          = 4.4;    // M4 clearance

/* [Controller box] */
board_w = 50;
board_l = 70;
box_h   = 26;
glands  = 3;             // cable holes on one end: power+signals, bus out, spare
gland_d = 6;

$fn = 48;

// ---------------------------------------------------------------- derived
inner_l = leds_per_module * led_pitch + 2 * end_margin;
inner_w = strip_w + 2 * fit;
inner_h = strip_h + headroom;
outer_l = inner_l + 2 * wall;
outer_w = inner_w + 2 * wall;
outer_h = floor_t + inner_h;

module rounded_box(l, w, h, r = 1.5) {
  hull()
    for (x = [r, l - r], y = [r, w - r])
      translate([x, y, 0]) cylinder(r = r, h = h);
}

// Cable exit: a U-slot through an end wall with the cable resting on the floor.
module cable_slot(x) {
  translate([x, outer_w / 2, floor_t + cable_d / 2]) {
    rotate([0, 90, 0]) cylinder(d = cable_d, h = wall * 3, center = true);
    translate([-wall * 1.5, -cable_d / 2, 0]) cube([wall * 3, cable_d, outer_h]);
  }
}

module housing() {
  difference() {
    union() {
      rounded_box(outer_l, outer_w, outer_h);
      if (tab_len > 0)
        translate([-tab_len, 0, 0]) rounded_box(outer_l + 2 * tab_len, outer_w, floor_t + 1);
    }
    // strip channel
    translate([wall, wall, floor_t]) cube([inner_l, inner_w, outer_h]);
    cable_slot(wall / 2);
    cable_slot(outer_l - wall / 2);
    if (tab_len > 0)
      for (x = [-tab_len / 2, outer_l + tab_len / 2])
        translate([x, outer_w / 2, -1]) cylinder(d = hole_d, h = 10);
  }
}

// Printed upside down (flat face on the bed). The lip runs along the long
// sides only, so it clears the cables at the ends. The groove over the walls
// takes a bead of silicone for sealing.
module diffuser() {
  groove_w = 0.9;
  difference() {
    rounded_box(outer_l, outer_w, lid_t);
    translate([wall / 2 - groove_w / 2, wall / 2 - groove_w / 2, lid_t - 0.8])
      difference() {
        cube([outer_l - wall + groove_w, outer_w - wall + groove_w, 1]);
        translate([groove_w, groove_w, -1])
          cube([outer_l - wall - groove_w, outer_w - wall - groove_w, 3]);
      }
  }
  // lip rails
  for (y = [wall + fit, outer_w - wall - fit - 1.2])
    translate([wall + end_margin, y, lid_t]) cube([inner_l - 2 * end_margin, 1.2, lip_h]);
  // tongues that drop into the cable slots to close the gap above the cable
  for (x = [0, outer_l - wall])
    translate([x + fit, outer_w / 2 - cable_d / 2 + fit, lid_t])
      cube([wall - 2 * fit, cable_d - 2 * fit, outer_h - floor_t - cable_d]);
}

module controller_box() {
  cw = board_w + 2 * 2 + 2 * 3;  // board + slack + walls
  cl = board_l + 2 * 2 + 2 * 3;
  difference() {
    rounded_box(cl, cw, box_h, 3);
    translate([3, 3, 2]) rounded_box(cl - 6, cw - 6, box_h, 1.5);
    // cable holes, bus/harness end
    for (i = [0 : glands - 1])
      translate([-1, cw / (glands + 1) * (i + 1), 12])
        rotate([0, 90, 0]) cylinder(d = gland_d, h = 5);
    // USB-C access for flashing, other end
    translate([cl - 4, cw / 2 - 5, 8]) cube([6, 10, 5]);
  }
  // board standoffs
  for (x = [5 + 2, cl - 5 - 2], y = [5 + 2, cw - 5 - 2])
    translate([x, y, 0]) difference() {
      cylinder(d = 5, h = 6);
      cylinder(d = 1.8, h = 7);  // M2 self-tapping
    }
  // lid, printed alongside
  translate([0, cw + 8, 0]) difference() {
    union() {
      rounded_box(cl, cw, 2, 3);
      translate([3 + fit, 3 + fit, 2]) difference() {
        rounded_box(cl - 6 - 2 * fit, cw - 6 - 2 * fit, 3, 1.5);
        translate([1.2, 1.2, -1]) rounded_box(cl - 8.4 - 2 * fit, cw - 8.4 - 2 * fit, 5, 1);
      }
    }
    // mode-button hole: press SW1 through a vinyl sticker or silicone dab
    translate([cl / 2, cw / 2, -1]) cylinder(d = 4, h = 5);
  }
}

if (part == "housing") housing();
else if (part == "diffuser") diffuser();
else if (part == "controller") controller_box();
else {
  housing();
  translate([0, outer_w + 10, 0]) diffuser();
  translate([0, 2 * outer_w + 30, 0]) controller_box();
}

echo(str("Module housing outer: ", outer_l, " x ", outer_w, " x ", outer_h + lid_t, " mm"));
