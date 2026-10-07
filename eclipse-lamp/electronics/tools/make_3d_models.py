"""Simple 3D model for the 3030 mid-power LED (KiCad ships none for this footprint)."""
import os
import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "eclipse.3dshapes")
os.makedirs(OUT, exist_ok=True)
body = cq.Workplane("XY").box(3.0, 3.0, 0.52, centered=(True, True, False)).edges("|Z").chamfer(0.15)
cup = cq.Workplane("XY").workplane(offset=0.12).circle(1.25).extrude(0.6)
housing = body.cut(cup)
phosphor = cq.Workplane("XY").workplane(offset=0.12).circle(1.25).extrude(0.36)
# package is centred on the footprint origin
asm = cq.Assembly()
asm.add(housing, name="housing", color=cq.Color(0.96, 0.96, 0.94))
asm.add(phosphor, name="phosphor", color=cq.Color(0.98, 0.86, 0.35))
asm.save(os.path.join(OUT, "LED_3030.step"))
print("ok")

# JST PH 10-pin side-entry SMD (S10B-PH-SM4-TB): KiCad has no model for it either
hous = (cq.Workplane("XY").box(24.0, 6.6, 6.0, centered=(True, False, False)).translate((0, -1.6, 0))
        .faces(">Y").workplane().rect(21.0, 4.0).cutBlind(-5.0))
pins = None
for k in range(10):
    p = cq.Workplane("XY").box(0.64, 3.0, 0.3, centered=(True, False, False)).translate((-9 + 2 * k, -4.4, 0))
    pins = p if pins is None else pins.union(p)
asm = cq.Assembly()
asm.add(hous, name="housing", color=cq.Color(0.93, 0.92, 0.86))
asm.add(pins, name="pins", color=cq.Color(0.85, 0.75, 0.45))
asm.save(os.path.join(OUT, "JST_PH_S10B-PH-SM4-TB.step"))
print("ok jst")

# HRO TYPE-C-31-M-12 USB-C receptacle (mid-size simplified shell, mouth at +Y)
shell = (cq.Workplane("XZ").center(0, 1.63).slot2D(8.94, 3.26).extrude(-7.3).translate((0, -3.65, 0)))
mouth = (cq.Workplane("XZ").workplane(offset=-3.66).center(0, 1.63).slot2D(8.34, 2.56).extrude(6.0))
tongue = cq.Workplane("XY").box(6.6, 4.5, 0.6).translate((0, 1.3, 1.63))
asm = cq.Assembly()
asm.add(shell.cut(mouth), name="shell", color=cq.Color(0.78, 0.78, 0.80))
asm.add(tongue, name="tongue", color=cq.Color(0.1, 0.1, 0.1))
asm.save(os.path.join(OUT, "USB_C_HRO_TYPE-C-31-M-12.step"))

# 1812 PTC fuse
body = cq.Workplane("XY").box(3.6, 3.2, 1.1, centered=(True, True, False))
asm = cq.Assembly()
asm.add(body, name="body", color=cq.Color(0.55, 0.45, 0.25))
for sx in (-1, 1):
    asm.add(cq.Workplane("XY").box(0.5, 3.2, 1.15, centered=(True, True, False)).translate((sx * 2.0, 0, 0)),
            name=f"term{sx}", color=cq.Color(0.8, 0.8, 0.82))
asm.save(os.path.join(OUT, "Fuse_1812.step"))
print("ok usb/fuse")
