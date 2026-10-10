"""Procedural cedar-elm (Ulmus crassifolia) skeleton for the ECLIPSE Tree lamp.

Pure geometry (no CadQuery): returns branch polylines with radii, the 40 twig tips
where the LED sprigs attach, and the sprig/leaf (LED) layout.  Deterministic (seeded).

Electrical mapping (see electronics/hub): 40 sprigs x 20 LEDs (800 leaves). Sprigs are numbered by
azimuth around the crown and dealt to channels W1, C1, W2, C2 in turn, so warm and cool
leaves are interleaved everywhere in the crown.
"""
import math, os, random, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "electronics", "tools"))
from sprig_layout import layout as sprig_layout  # noqa: E402

SEED = 11
N_LIMBS = 4
SPRIGS_PER_LIMB = 10
SPRIG = sprig_layout()
LEDS_PER_SPRIG = len(SPRIG["leaves"])   # 20
CHANNELS = ("W1", "C1", "W2", "C2")

TRUNK_FOOT = (0.0, 58.0, 22.0)      # socket in the base (rear), top of the base
BURL = (0.0, 18.0, 158.0)           # fork knot: hides the hub PCB
TIP_D = 1.6                         # brass twig diameter where a sprig is soldered on
TRUNK_D = 14.0


def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def v_len(a): return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
def v_norm(a):
    l = v_len(a) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)
def v_cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def rotate(v, axis, ang):
    """Rodrigues rotation of v about unit axis by ang (rad)."""
    axis = v_norm(axis)
    c, s = math.cos(ang), math.sin(ang)
    d = sum(v[i] * axis[i] for i in range(3))
    cr = v_cross(axis, v)
    return tuple(v[i] * c + cr[i] * s + axis[i] * d * (1 - c) for i in range(3))


def perp(v):
    a = (1.0, 0.0, 0.0) if abs(v[0]) < 0.9 else (0.0, 1.0, 0.0)
    return v_norm(v_cross(v, a))


def diam(n):
    """Pipe-model diameter for a branch that carries n sprigs."""
    return max(TIP_D, 2.1 * n ** 0.52)


class Tree:
    def __init__(self, seed=SEED):
        self.rng = random.Random(seed)
        self.branches = []   # list of dict(points=[...], radii=[...], level=int, n=int)
        self.tips = []       # list of dict(pos, dir, limb)
        self._build()
        self._assign()
        self._sprigs()

    # -------------------------------------------------------------- skeleton
    def _curve(self, p0, d0, length, r0, r1, steps, bend, droop):
        """A gently wandering branch; returns points, radii, end dir."""
        pts, rad = [p0], [r0]
        d = d0
        seg = length / steps
        for k in range(1, steps + 1):
            # wander + gravitropism (droop > 0 pulls toward -Z, < 0 lifts)
            ax = perp(d)
            ax = rotate(ax, d, self.rng.uniform(0, 2 * math.pi))
            d = v_norm(rotate(d, ax, self.rng.gauss(0, bend)))
            d = v_norm(v_add(d, (0, 0, -droop * seg / 40.0)))
            pts.append(v_add(pts[-1], v_mul(d, seg)))
            rad.append(r0 + (r1 - r0) * k / steps)
        return pts, rad, d

    def _build(self):
        rng = self.rng
        # trunk: S-curve from the rear socket to the burl
        p0 = TRUNK_FOOT
        pts, rad = [], []
        for k in range(9):
            t = k / 8
            # cubic Bezier: foot -> lean forward -> burl
            c1 = (0.0, 58.0, 72.0)
            c2 = (0.0, 2.0, 108.0)
            b = [(1 - t) ** 3 * p0[i] + 3 * (1 - t) ** 2 * t * c1[i] + 3 * (1 - t) * t ** 2 * c2[i] + t ** 3 * BURL[i]
                 for i in range(3)]
            b[0] += 3.0 * math.sin(t * 5.0)
            pts.append(tuple(b))
            rad.append((TRUNK_D / 2) * (1.0 - 0.12 * t))
        self.branches.append(dict(points=pts, radii=rad, level=0, n=40))
        # limbs fan out from the burl
        az0 = rng.uniform(0, 360)
        for li in range(N_LIMBS):
            az = math.radians(az0 + li * 90 + rng.uniform(-18, 18))
            elev = math.radians(rng.uniform(38, 55))
            d = v_norm((math.cos(elev) * math.sin(az), math.cos(elev) * math.cos(az), math.sin(elev)))
            start = v_add(BURL, v_mul(d, 9.0))
            self._grow(start, d, SPRIGS_PER_LIMB, 1, li)

    def _grow(self, p, d, n, level, limb):
        rng = self.rng
        r0 = diam(n) / 2
        if n == 1:
            # terminal brass twig: slightly drooping
            length = rng.uniform(16, 26)
            pts, rad, dend = self._curve(p, d, length, r0, TIP_D / 2, 3, 0.18, 0.35)
            self.branches.append(dict(points=pts, radii=rad, level=level, n=1))
            self.tips.append(dict(pos=pts[-1], dir=dend, limb=limb))
            return
        # split n into 2 (sometimes 3) children
        if n >= 5 and rng.random() < 0.35:
            a = max(1, round(n * rng.uniform(0.25, 0.4)))
            b = max(1, round((n - a) * rng.uniform(0.4, 0.6)))
            parts = [a, b, n - a - b]
        else:
            a = max(1, min(n - 1, round(n * rng.uniform(0.35, 0.65))))
            parts = [a, n - a]
        parts = [x for x in parts if x > 0]
        length = 14 + 15 * n ** 0.55 * rng.uniform(0.8, 1.2)
        r1 = diam(max(parts)) / 2
        pts, rad, dend = self._curve(p, d, length, r0, max(r1, TIP_D / 2), 4, 0.10,
                                     -0.25 if n > 3 else 0.15)
        self.branches.append(dict(points=pts, radii=rad, level=level, n=n))
        self._spurs(pts, rad, n)
        end = pts[-1]
        roll = rng.uniform(0, 2 * math.pi)
        for k, m in enumerate(parts):
            # bigger child stays closer to the parent direction (sympodial look)
            spread = math.radians(rng.uniform(22, 34) if m == max(parts) else rng.uniform(34, 52))
            ax = rotate(perp(dend), dend, roll + k * 2.4)
            cd = v_norm(rotate(dend, ax, spread))
            # keep the crown open: push children away from the trunk axis a little
            out = v_norm((end[0] - BURL[0], end[1] - BURL[1], 0.0001))
            cd = v_norm(v_add(cd, v_mul(out, 0.25)))
            self._grow(end, cd, m, level + 1, limb)

    def _spurs(self, pts, rad, n):
        """Decorative brass spur twigs (no LEDs): what makes the crown read as intricate."""
        rng = self.rng
        for _ in range(rng.randint(2, 4) + (2 if n > 4 else 0)):
            k = rng.randint(1, len(pts) - 2)
            p = pts[k]
            d = v_norm(v_sub(pts[k + 1], pts[k - 1]))
            ax = rotate(perp(d), d, rng.uniform(0, 2 * math.pi))
            sd = v_norm(rotate(d, ax, math.radians(rng.uniform(40, 70))))
            length = rng.uniform(7, 16) + 0.6 * n
            r0 = max(0.55, min(rad[k] * 0.45, 1.3))
            spts, srad, sdir = self._curve(p, sd, length, r0, 0.4, 3, 0.25, 0.5)
            self.branches.append(dict(points=spts, radii=srad, level=9, n=0))
            if length > 12 and rng.random() < 0.6:   # a second, finer fork on longer spurs
                q = spts[2]
                fd = v_norm(rotate(sdir, perp(sdir), math.radians(rng.uniform(30, 50))))
                fp, fr, _ = self._curve(q, fd, length * 0.45, 0.4, 0.3, 2, 0.3, 0.6)
                self.branches.append(dict(points=fp, radii=fr, level=10, n=0))

    # -------------------------------------------------------------- channels
    def _assign(self):
        cx, cy = BURL[0], BURL[1]
        order = sorted(range(len(self.tips)),
                       key=lambda i: math.atan2(self.tips[i]["pos"][0] - cx, self.tips[i]["pos"][1] - cy))
        count = {c: 0 for c in CHANNELS}
        for rank, i in enumerate(order):
            ch = CHANNELS[rank % 4]
            self.tips[i]["channel"] = ch
            self.tips[i]["index"] = count[ch]      # position in the channel's series chain
            count[ch] += 1
            self.tips[i]["name"] = f"{ch}.{count[ch]:02d}"

    # -------------------------------------------------------------- sprigs + leaves
    def _sprigs(self):
        """Map the planar flex sprig (sprig_layout) onto a drooping 3D spray at every twig tip."""
        rng = self.rng
        self.sprig_paths, self.leaves = [], []
        for t in self.tips:
            d0 = t["dir"]
            side = v_norm(v_cross((0, 0, 1), d0)) if abs(d0[2]) < 0.95 else perp(d0)
            roll = rng.uniform(-0.5, 0.5)            # the flex twists a little on its twig
            droop = rng.uniform(0.012, 0.022)        # rad/mm sag along the stem
            # centre-line of the stem in 3D, sampled every 1 mm of u
            cl, dirs = [t["pos"]], [d0]
            d = d0
            for k in range(60):
                d = v_norm(v_add(d, (0, 0, -droop)))
                cl.append(v_add(cl[-1], d))
                dirs.append(d)
            up = v_norm(v_cross(side, d0))

            def m(u, v):
                u = max(0.0, min(59.0, u))
                i = int(u)
                f = u - i
                c = v_add(v_mul(cl[i], 1 - f), v_mul(cl[i + 1], f))
                lat = v_norm(v_add(side, v_mul(up, roll)))
                return v_add(v_add(c, v_mul(lat, v)), (0, 0, -0.004 * v * v))

            stems = [[m(u, v) for (u, v) in s] for s in SPRIG["stems"]]
            pets = []
            for lf in SPRIG["leaves"]:
                b, p = m(*lf["base"]), m(*lf["pos"])
                pets.append((b, p))
                self.leaves.append(dict(pos=p, dir=v_norm(v_sub(p, b)), channel=t["channel"], sprig=t["name"]))
            self.sprig_paths.append(dict(stems=stems, petioles=pets, channel=t["channel"], name=t["name"]))

    def summary(self):
        xs = [l["pos"][0] for l in self.leaves]
        ys = [l["pos"][1] for l in self.leaves]
        zs = [l["pos"][2] for l in self.leaves]
        return dict(branches=len(self.branches), sprigs=len(self.tips), leaves=len(self.leaves),
                    x=(min(xs), max(xs)), y=(min(ys), max(ys)), z=(min(zs), max(zs)))


if __name__ == "__main__":
    t = Tree()
    print(t.summary())
