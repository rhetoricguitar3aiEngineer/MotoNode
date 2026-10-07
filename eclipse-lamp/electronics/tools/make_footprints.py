"""Write the custom touch-electrode footprints into ../lib/eclipse.pretty."""
import math, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "eclipse.pretty")
R_IN, R_OUT, HALF = 9.5, 22.5, 58.0   # wheel segment: radii and half-angle (deg)


def key():
    return """(footprint "TouchKey_D14"
	(version 20241229)
	(generator "eclipse-gen")
	(layer "F.Cu")
	(descr "Self-capacitance touch key, 14 mm round electrode under 3 mm glass")
	(attr smd exclude_from_pos_files exclude_from_bom)
	(property "Reference" "REF**" (at 0 -8.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
	(property "Value" "TouchKey_D14" (at 0 8.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
	(fp_circle (center 0 0) (end 7.5 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
	(pad "1" smd circle (at 0 0) (size 14 14) (layers "F.Cu") (zone_connect 0))
)
"""


def wheel():
    pts = []
    n = 24
    for k in range(n + 1):
        a = math.radians(-HALF + 2 * HALF * k / n)
        pts.append((R_OUT * math.sin(a), -R_OUT * math.cos(a)))
    for k in range(n + 1):
        a = math.radians(HALF - 2 * HALF * k / n)
        pts.append((R_IN * math.sin(a), -R_IN * math.cos(a)))
    ax, ay = 0.0, -(R_IN + R_OUT) / 2
    xy = " ".join("(xy %.4f %.4f)" % (x - ax, y - ay) for x, y in pts)
    crt = " ".join("(xy %.4f %.4f)" % (x * 1.0, y * 1.0) for x, y in pts)
    return f"""(footprint "TouchWheel_Seg120"
	(version 20241229)
	(generator "eclipse-gen")
	(layer "F.Cu")
	(descr "One 116 deg segment of a 3-segment self-capacitance touch wheel, OD 45 / ID 19 mm. Origin = wheel centre; place 3x at 0/120/240 deg")
	(attr smd exclude_from_pos_files exclude_from_bom)
	(property "Reference" "REF**" (at 0 -24.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
	(property "Value" "TouchWheel_Seg120" (at 0 -26 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
	(fp_poly (pts {crt}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
	(pad "1" smd custom (at {ax:.4f} {ay:.4f}) (size 1 1) (layers "F.Cu") (zone_connect 0)
		(options (clearance outline) (anchor circle))
		(primitives (gr_poly (pts {xy}) (width 0) (fill yes)))
	)
)
"""


os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "TouchKey_D14.kicad_mod"), "w").write(key())
open(os.path.join(OUT, "TouchWheel_Seg120.kicad_mod"), "w").write(wheel())
print("ok")
