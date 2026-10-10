"""Planar layout of one LED sprig (flex PCB), shared by the PCB generator and the 3D tree.

Coordinates in mm, sprig root at (0, 0), main stem along +x, +y to the left.
A cedar-elm spray: a main stem with three alternate side shoots; every leaf is a short
petiole ending in an 0402 LED (the LED *is* the leaf).  20 leaves, all in parallel.
"""
import math

PETIOLE = 2.4          # stem -> LED centre
PET_ANGLE = 55.0       # petiole angle to its stem (deg)


def _pt(o, ang, d):
    a = math.radians(ang)
    return (o[0] + d * math.cos(a), o[1] + d * math.sin(a))


def layout():
    """Return dict(stems=[[p0, p1, ...], ...], leaves=[dict(base, pos, ang, stem)])."""
    stems, leaves = [], []

    def stem(origin, ang, length, leaf_at, first_side, curve=0.0, steps=6):
        pts = [origin]
        a = ang
        for k in range(1, steps + 1):
            a += curve / steps
            pts.append(_pt(pts[-1], a, length / steps))
        sid = len(stems)
        stems.append(pts)
        side = first_side
        for item in leaf_at:
            s, side = item if isinstance(item, tuple) else (item, side)
            # point at arc length s along the polyline + local direction
            acc = 0.0
            for p, q in zip(pts, pts[1:]):
                l = math.dist(p, q)
                if acc + l >= s - 1e-9:
                    t = (s - acc) / l
                    base = (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
                    da = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
                    break
                acc += l
            la = da + side * PET_ANGLE
            leaves.append(dict(base=base, pos=_pt(base, la, PETIOLE), ang=la, stem=sid))
            side = -side
            if isinstance(item, tuple):
                side = item[1]
        return pts

    # main-stem leaves placed clear of the side shoots and their inward leaves (shoots: 8 L, 15 R, 24 L)
    main = stem((0.0, 0.0), 0.0, 44.0, [(10.5, -1), (17.0, +1), (19.5, +1), (25.5, -1), (28.5, -1), (34.0, +1),
                                        (36.0, -1), (44.0 - 0.01, +1)], +1, curve=-8)
    # side shoots leave the main stem alternately
    def at(s):
        acc = 0.0
        for p, q in zip(main, main[1:]):
            l = math.dist(p, q)
            if acc + l >= s:
                t = (s - acc) / l
                return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t), \
                    math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
            acc += l
    for s, side, length in ((8.0, +1, 15.0), (15.0, -1, 14.0), (24.0, +1, 12.0)):
        o, a = at(s)
        # first leaf of a shoot points away from the main stem
        stem(o, a + side * 38.0, length, [3.5, 6.5, 9.5, length - 0.01], side, curve=-side * 10)
    return dict(stems=stems, leaves=leaves)


N_LEAVES = len(layout()["leaves"])

if __name__ == "__main__":
    L = layout()
    print(len(L["stems"]), "stems,", len(L["leaves"]), "leaves")
