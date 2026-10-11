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

TRUNK_FOOT = (0.0, 48.0, 22.0)      # trunk foot on the base top (the 14 mm spigot sits at y = 58)
BURL = (0.0, 14.0, 168.0)           # fork knot: hides the hub light engine
BURL_R = 34.0                       # burl half-width
TIP_D = 2.4                         # twig diameter where a sprig is soldered on
TRUNK_D = 44.0                      # at the foot (tapers to ~34 at the burl)
N_ROOTS = 6


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
    return max(TIP_D, 2.6 * n ** 0.62)


class Tree:
    def __init__(self, seed=SEED):
        self.rng = random.Random(seed)
        self.branches = []   # list of dict(points=[...], radii=[...], level=int, n=int)
        self.tips = []       # list of dict(pos, dir, limb)
        self.samaras = []    # fibre-lit seed tips: dict(pos, dir)
        self.roots = []      # buttress roots over the base top
        self._build()
        self._assign()
        self._sprigs()
        self._samara_bundles()

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
        # trunk: thick S-curve from the foot to the burl, slightly gnarled
        p0 = TRUNK_FOOT
        pts, rad = [], []
        for k in range(17):
            tt = k / 16
            c1 = (0.0, 50.0, 70.0)
            c2 = (0.0, 6.0, 112.0)
            b = [(1 - tt) ** 3 * p0[i] + 3 * (1 - tt) ** 2 * tt * c1[i] + 3 * (1 - tt) * tt ** 2 * c2[i]
                 + tt ** 3 * BURL[i] for i in range(3)]
            b[0] += 4.0 * math.sin(tt * 5.0)
            pts.append(tuple(b))
            r = (TRUNK_D / 2) * (1.0 - 0.25 * tt ** 0.6) * (1.0 + 0.05 * math.sin(tt * 23.0))
            rad.append(r)
        self.branches.append(dict(points=pts, radii=rad, level=0, n=40))
        self._roots()
        # limbs fan out from the burl
        az0 = rng.uniform(0, 360)
        for li in range(N_LIMBS):
            az = math.radians(az0 + li * 90 + rng.uniform(-18, 18))
            elev = math.radians(rng.uniform(38, 55))
            d = v_norm((math.cos(elev) * math.sin(az), math.cos(elev) * math.cos(az), math.sin(elev)))
            start = v_add(BURL, v_mul(d, BURL_R * 0.55))
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
        """Fine side-branch systems (no LEDs). Every terminal tip carries an end-glow optical
        fibre that lights a diffusing samara (seed); together they make the crown intricate."""
        rng = self.rng
        for _ in range(rng.randint(5, 8) + (4 if n > 4 else 0)):
            k = rng.randint(1, len(pts) - 2)
            d = v_norm(v_sub(pts[k + 1], pts[k - 1]))
            ax = rotate(perp(d), d, rng.uniform(0, 2 * math.pi))
            sd = v_norm(rotate(d, ax, math.radians(rng.uniform(35, 70))))
            length = rng.uniform(10, 20) + 0.9 * n
            r0 = max(0.7, min(rad[k] * 0.38, 2.2))
            self._spur(pts[k], sd, length, r0, 0)

    def _spur(self, p, d, length, r0, depth):
        rng = self.rng
        r1 = max(0.35, r0 * 0.55)
        spts, srad, sdir = self._curve(p, d, length, r0, r1, 3, 0.22, 0.55)
        self.branches.append(dict(points=spts, radii=srad, level=9 + depth, n=0))
        kids = 0
        if depth < 2 and length > 9:
            kids = 2 if rng.random() < 0.75 else 1
        for c in range(kids):
            q = spts[rng.randint(1, 2)] if c else spts[-1]
            fd = v_norm(rotate(sdir, rotate(perp(sdir), sdir, rng.uniform(0, 6.3)),
                               math.radians(rng.uniform(25, 50))))
            self._spur(q, fd, length * rng.uniform(0.5, 0.7), max(0.35, srad[-1] * 0.95), depth + 1)
        if kids == 0:
            self.samaras.append(dict(pos=spts[-1], dir=sdir))

    def _roots(self):
        """Buttress roots: spread from the trunk foot over the base top, clear of the touch window."""
        rng = self.rng
        x0, y0, z0 = TRUNK_FOOT
        for k in range(N_ROOTS):
            # plan angle (0 = rear, clockwise); keep out of the front sector where the glass is
            a = math.radians(-140 + k * 56 + rng.uniform(-10, 10))
            d = (math.sin(a), math.cos(a))
            L = rng.uniform(26, 44)
            pts, rad = [], []
            for j in range(7):
                tt = j / 6
                r_out = TRUNK_D / 2 * 0.75 + L * tt
                px, py = x0 + d[0] * r_out, y0 + d[1] * r_out
                # stay on the base disc
                rr = math.hypot(px, py)
                if rr > 70.0:
                    px, py = px * 70.0 / rr, py * 70.0 / rr
                pz = z0 + 7.0 * (1 - tt) ** 1.6 + 1.2
                pts.append((px, py, pz))
                rad.append(max(1.2, 8.0 * (1 - tt) ** 1.2 + 1.2))
            self.roots.append(dict(points=pts, radii=rad))
            self.branches.append(dict(points=pts, radii=rad, level=-1, n=0))

    def _samara_bundles(self):
        """Deal the samaras round the crown to the 4 fibre bundles (= colour channels) in turn."""
        cx, cy = BURL[0], BURL[1]
        order = sorted(range(len(self.samaras)),
                       key=lambda i: math.atan2(self.samaras[i]["pos"][0] - cx, self.samaras[i]["pos"][1] - cy))
        for rank, i in enumerate(order):
            self.samaras[i]["channel"] = CHANNELS[rank % 4]

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
        return dict(branches=len(self.branches), samaras=len(self.samaras), sprigs=len(self.tips),
                    leaves=len(self.leaves),
                    x=(min(xs), max(xs)), y=(min(ys), max(ys)), z=(min(zs), max(zs)))


if __name__ == "__main__":
    t = Tree()
    print(t.summary())
