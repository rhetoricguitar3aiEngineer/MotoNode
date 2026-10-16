"""Procedural cedar-elm (Ulmus crassifolia) for the ECLIPSE Tree lamp.

The crown is grown with the space-colonisation algorithm (Runions et al. 2007): buds grow
toward attraction points scattered in a rounded cedar-elm crown envelope, so branches
compete for space, fork where the space divides and thin out naturally. Branch radii follow
the pipe model (a parent carries the cross-section of everything above it), so the wood
tapers continuously from the root flare to the finest twig.

Pure geometry (no CadQuery): branch polylines with radii, the 40 twigs where the LED sprigs
are grafted on, the sprig/leaf (LED) layout, the fibre-lit samaras and the leaf-film foliage.
Deterministic (seeded).

Electrical mapping (see electronics/hub): 40 sprigs x 20 LEDs (800 leaves). Sprigs are
numbered by azimuth around the crown and dealt to channels W1, C1, W2, C2 in turn, so warm and
cool leaves are interleaved everywhere in the crown.
"""
import math, os, random, sys
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "electronics", "tools"))
from sprig_layout import layout as sprig_layout  # noqa: E402

SEED = 7
N_SPRIGS = 40
SPRIG = sprig_layout()
LEDS_PER_SPRIG = len(SPRIG["leaves"])   # 20
CHANNELS = ("W1", "C1", "W2", "C2")

TRUNK_FOOT = (0.0, 36.0, 22.0)      # trunk foot on the base top (the 14 mm spigot sits at y = 58)
FORK = (0.0, 6.0, 158.0)            # where the trunk divides into its leaders
HUB_DROP = 12.0                     # hub light engine: this far below the fork, inside the swelling
HUB_R_MIN = 31.0                    # trunk radius needed there: Ø56 hub + 2.5 mm shell + clearance
TRUNK_D = 60.0                      # minimum trunk diameter profile; the pipe model (the cross-section
                                    # of the whole crown) makes the bole ~77 mm in practice
N_LEADERS = 3
LEADER_F = 0.76                     # leader radius at the fork / trunk radius
N_ROOTS = 7

# crown envelope (a broad, rounded cedar-elm dome) and growth parameters
CROWN_C = np.array([0.0, 2.0, 288.0])
CROWN_R = np.array([178.0, 166.0, 128.0])
N_ATTRACT = 4200
STEP = 5.0              # bud growth per iteration (mm)
D_INFL = 62.0           # an attraction point pulls the nearest bud within this distance
D_KILL = 9.0            # ... and is used up when a bud gets this close
R_TIP, R_K, R_EXP = 0.40, 0.255, 0.71    # pipe model: r = max(R_TIP, R_K * tips ** R_EXP)
SPRIG_BACK = 44.0       # a sprig is grafted this far (along the wood) behind a twig tip


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


def pipe_r(tips):
    return max(R_TIP, R_K * tips ** R_EXP)


def trunk_r(t):
    """Trunk radius along its length (t = 0 foot .. 1 fork): root flare, a long even bole,
    and the swelling where the leaders divide (it houses the hub)."""
    flare = 9.0 * math.exp(-t / 0.075)
    swell = 3.6 * (lambda s: s * s * (3 - 2 * s))(min(1.0, max(0.0, (t - 0.70) / 0.30)))
    return (TRUNK_D / 2 - 1.5 * t) + flare + swell


class Tree:
    def __init__(self, seed=SEED):
        self.rng = random.Random(seed)
        self.nrng = np.random.default_rng(seed)
        self.branches = []   # dict(points, radii, level, n)
        self.tips = []       # sprig grafts: dict(pos, dir, limb, channel, index, name)
        self.samaras = []    # fibre-lit seeds: dict(pos, dir, channel)
        self.roots = []
        self.foliage = []    # leaf-film leaves: dict(pos, axis, normal, size)
        self._trunk()
        self._colonise()
        self._smooth()
        self._radii()
        self._choose_sprigs()
        self._to_branches()
        self._roots()
        self._assign()
        self._sprigs()
        self._samaras()
        self._foliage()

    # -------------------------------------------------------------- trunk
    def _trunk(self):
        p0, c1, c2, p3 = TRUNK_FOOT, (0.0, 40.0, 78.0), (0.0, -4.0, 112.0), FORK
        self.pos, self.par, self.kind = [], [], []     # kind: 0 trunk, 1 crown
        n = 24
        for k in range(n + 1):
            t = k / n
            b = [(1 - t) ** 3 * p0[i] + 3 * (1 - t) ** 2 * t * c1[i] + 3 * (1 - t) * t ** 2 * c2[i]
                 + t ** 3 * p3[i] for i in range(3)]
            b[0] += 3.0 * math.sin(t * 4.2)
            self.pos.append(np.array(b))
            self.par.append(k - 1)
            self.kind.append(0)
        self.fork = n
        zs = [p[2] for p in self.pos]
        zh = FORK[2] - HUB_DROP
        k = max(i for i in range(n) if zs[i] <= zh)
        f = (zh - zs[k]) / (zs[k + 1] - zs[k])
        self.hub = tuple(float(v) for v in self.pos[k] * (1 - f) + self.pos[k + 1] * f)
        self._hub_k = k + f
        # leader stubs: a vase-shaped fork, the way an old elm divides. Each leader starts as
        # thick as LEADER_F x the trunk and offset outward so its surface is tangent to the
        # trunk's: the three lobes cover the trunk top and the fork has no shoulder.
        R = trunk_r(1.0)
        self.r_lead0 = LEADER_F * R
        a0 = self.rng.uniform(0, 2 * math.pi)
        for k in range(N_LEADERS):
            az = a0 + k * 2 * math.pi / N_LEADERS + self.rng.uniform(-0.25, 0.25)
            el = math.radians(self.rng.uniform(50, 58))
            d = np.array([math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)])
            h = np.array([math.sin(az), math.cos(az), 0.0])
            start = self.pos[self.fork] + h * (R - self.r_lead0) - np.array([0, 0, 0.35 * R])
            prev = self.fork
            for j in range(0, 7):
                self.pos.append(start + d * (STEP * 1.6 * j))
                self.par.append(prev)
                self.kind.append(1)
                prev = len(self.pos) - 1

    # -------------------------------------------------------------- space colonisation
    def _attractors(self):
        """Attraction points in a rounded crown whose surface is gently lobed (a few broad
        bumps), so the foliage forms the separate masses a real crown has."""
        rng = self.nrng
        bumps = []
        for k in range(11):
            v = rng.normal(0, 1, 3)
            v[2] = abs(v[2]) * 0.6 + 0.1 * v[2]
            bumps.append((v / np.linalg.norm(v), rng.uniform(0.07, 0.14)))

        def shell(u):
            return 1.0 + sum(a * max(0.0, float(u @ b)) ** 6 for b, a in bumps) - 0.06

        out = []
        while len(out) < N_ATTRACT:
            u = rng.uniform(-1, 1, 3)
            r = np.linalg.norm(u)
            if r > 1 or r < 1e-6:
                continue
            u = u / r
            p = CROWN_C + u * shell(u) * (0.40 + 0.60 * rng.uniform() ** 0.45) * CROWN_R
            rho = math.hypot(p[0] - FORK[0], p[1] - FORK[1])
            if p[2] < FORK[2] + 52 - 0.10 * rho:                  # open below the scaffold limbs
                continue
            out.append(p)
        return np.array(out)

    def _colonise(self):
        att = self._attractors()
        alive = np.ones(len(att), bool)
        grow_from = set(range(self.fork + 1, len(self.pos)))       # leader stubs only
        self._km = self._kidmap()
        for it in range(400):
            idx = list(grow_from)
            if not idx or not alive.any():
                break
            P = np.array([self.pos[i] for i in idx])
            tree = cKDTree(P)
            live = np.nonzero(alive)[0]
            dist, near = tree.query(att[live], distance_upper_bound=D_INFL)
            pulls = {}
            for a, dd, nn in zip(live, dist, near):
                if not np.isfinite(dd):
                    continue
                node = idx[nn]
                v = att[a] - self.pos[node]
                pulls.setdefault(node, []).append(v / (np.linalg.norm(v) + 1e-9))
            if not pulls:
                break
            new = []
            for node, vs in pulls.items():
                d = np.sum(vs, axis=0)
                if np.linalg.norm(d) < 0.3 * len(vs) ** 0.5:
                    continue                                   # pulled apart evenly: stall
                d /= np.linalg.norm(d)
                # tropisms: outer wood arches and the outermost twigs weep a little
                rho = math.hypot(self.pos[node][0] - CROWN_C[0], self.pos[node][1] - CROWN_C[1])
                d = d + np.array([0, 0, 0.10 - 0.42 * (rho / CROWN_R[0]) ** 2])
                d /= np.linalg.norm(d)
                q = self.pos[node] + d * STEP
                # never two buds in the same place
                if any(np.linalg.norm(self.pos[c] - q) < STEP * 0.4 for c in self._kids(node)):
                    continue
                self.pos.append(q)
                self.par.append(node)
                self.kind.append(1)
                new.append(len(self.pos) - 1)
                self._km.setdefault(node, []).append(new[-1])
            if not new:
                break
            grow_from.update(new)
            NP = cKDTree(np.array([self.pos[i] for i in new]))
            hit = NP.query_ball_point(att[live], D_KILL)
            for a, h in zip(live, hit):
                if h:
                    alive[a] = False
            if it % 8 == 0:   # buds that have had nothing for a while stop being searched
                grow_from = {i for i in grow_from if i in pulls or i in new or self.rng.random() < 0.5}

    def _kids(self, node):
        return self._kidmap().get(node, []) if not hasattr(self, "_km") else self._km.get(node, [])

    def _kidmap(self):
        m = {}
        for i, p in enumerate(self.par):
            if p >= 0:
                m.setdefault(p, []).append(i)
        return m

    def _smooth(self):
        """Relax the crown nodes (not the trunk or tips) so the wood curves instead of zig-zags."""
        kids = self._kidmap()
        P = np.array(self.pos)
        for _ in range(4):
            Q = P.copy()
            for i in range(self.fork + 1, len(P)):
                ks = kids.get(i, [])
                if not ks:
                    continue
                Q[i] = 0.5 * P[i] + 0.25 * P[self.par[i]] + 0.25 * np.mean(P[ks], axis=0)
            P = Q
        self.pos = list(P)
        self.kidmap = kids

    def _radii(self):
        n = len(self.pos)
        tips = np.zeros(n)
        order = sorted(range(n), key=lambda i: -self._depth(i))
        for i in order:
            if not self.kidmap.get(i) and i > self.fork:
                tips[i] = 1
            if self.par[i] >= 0:
                tips[self.par[i]] += tips[i]
        self.tipcount = tips
        self.rad = [pipe_r(t) for t in tips]
        for k in range(self.fork + 1):
            self.rad[k] = max(self.rad[k], trunk_r(k / self.fork))
        k = int(self._hub_k)
        f = self._hub_k - k
        self.hub_r = float(self.rad[k] * (1 - f) + self.rad[k + 1] * f)
        assert self.hub_r >= HUB_R_MIN, f"trunk too thin for the hub: r {self.hub_r:.1f}"
        # the leaders flare into the trunk top: a broad crotch instead of a shoulder
        r_top = trunk_r(1.0)
        for i in range(self.fork + 1, len(self.pos)):
            j, steps = i, 0
            while self.par[j] > self.fork:
                j, steps = self.par[j], steps + 1
            if self.par[j] != self.fork or steps > 9:
                continue
            f = (1 - steps / 10) ** 1.4
            self.rad[i] = max(self.rad[i], self.rad[i] + (LEADER_F * r_top - self.rad[i]) * f)

    def _depth(self, i):
        if not hasattr(self, "_dcache"):
            self._dcache = {}
        d, j, path = 0, i, []
        while j >= 0 and j not in self._dcache:
            path.append(j)
            j = self.par[j]
        base = self._dcache.get(j, -1) if j >= 0 else -1
        for k in reversed(path):
            base += 1
            self._dcache[k] = base
        return self._dcache[i]

    # -------------------------------------------------------------- sprig grafts
    def _choose_sprigs(self):
        """40 twigs around the outside of the crown carry the LED sprays. Each spray is grafted
        SPRIG_BACK mm behind a twig tip and runs out along it to the crown surface."""
        leaves = [i for i in range(len(self.pos)) if not self.kidmap.get(i) and i > self.fork]
        def shell(i):
            u = (self.pos[i] - CROWN_C) / CROWN_R
            return np.linalg.norm(u)
        cand = [i for i in leaves if shell(i) > 0.78 and self.pos[i][2] > FORK[2] + 70]
        P = np.array([self.pos[i] for i in cand])
        # farthest-point sampling, seeded at the top of the crown
        chosen = [int(np.argmax(P[:, 2]))]
        dmin = np.linalg.norm(P - P[chosen[0]], axis=1)
        while len(chosen) < N_SPRIGS:
            k = int(np.argmax(dmin))
            chosen.append(k)
            dmin = np.minimum(dmin, np.linalg.norm(P - P[k], axis=1))
        self.sprig_nodes = []
        for k in chosen:
            tip = cand[k]
            j, run = tip, 0.0
            while run < SPRIG_BACK and self.par[j] > self.fork:
                run += np.linalg.norm(self.pos[j] - self.pos[self.par[j]])
                j = self.par[j]
            d = self.pos[tip] - self.pos[j]
            self.sprig_nodes.append((j, tip, tuple(d / np.linalg.norm(d))))
        self.sprig_tip_set = {t for _, t, _ in self.sprig_nodes}

    # -------------------------------------------------------------- polylines
    def _to_branches(self):
        """Chain the node graph into branches: a branch continues into its thickest child;
        the other children start new branches (with the parent node as their first point)."""
        kids = self.kidmap
        leader_of = {}
        out = []

        def walk(start, prev, level, limb):
            pts, rad = ([self.pos[prev]], [self.rad[start]]) if prev is not None else ([], [])
            i = start
            while True:
                leader_of[i] = limb
                pts.append(self.pos[i])
                rad.append(self.rad[i])
                ks = sorted(kids.get(i, []), key=lambda c: -self.tipcount[c])
                if not ks:
                    break
                for c in ks[1:]:
                    walk(c, i, level + 1, limb)
                i = ks[0]
            out.append(dict(points=[tuple(map(float, p)) for p in pts], radii=[float(r) for r in rad],
                            level=level, n=0, end=i))

        # the trunk to the fork, then each leader is a limb
        out.append(dict(points=[tuple(map(float, self.pos[k])) for k in range(self.fork + 1)],
                        radii=[float(self.rad[k]) for k in range(self.fork + 1)], level=0, n=0, end=self.fork))
        trunk = out.pop()
        # round the top of the swelling over the leader roots (a dome, not a sawn-off stump)
        top, r = trunk["points"][-1], trunk["radii"][-1]
        ax = v_norm(v_sub(top, trunk["points"][-3]))
        for k in range(1, 6):
            f = k / 6
            trunk["points"].append(v_add(top, v_mul(ax, 0.30 * r * f)))
            trunk["radii"].append(r * math.sqrt(max(0.0, 1 - f ** 2)) * 0.9 + 0.1 * r * (1 - f))
        lead = [c for c in kids[self.fork] if c > self.fork]
        for li, c in enumerate(sorted(lead, key=lambda c: math.atan2(self.pos[c][0], self.pos[c][1]))):
            walk(c, None, 1, li)
        self.leader_of = leader_of
        out.sort(key=lambda b: (b["level"], -b["radii"][0]))
        self.branches = [trunk] + out
        # sprigs carried per branch (for the docs / wiring)
        for b in self.branches:
            b.pop("end")

    # -------------------------------------------------------------- roots
    def _roots(self):
        """Buttress roots: spread from the flare over the base top, clear of the touch window."""
        rng = self.rng
        x0, y0, z0 = TRUNK_FOOT
        for k in range(N_ROOTS):
            a = math.radians(-138 + k * 46 + rng.uniform(-8, 8))
            d = (math.sin(a), math.cos(a))
            L = rng.uniform(16, 30)
            pts, rad = [], []
            for j in range(9):
                tt = j / 8
                r_out = 16.0 + (L + 20.0) * tt
                px, py = x0 + d[0] * r_out, y0 + d[1] * r_out
                rr = math.hypot(px, py)
                if rr > 70.0:
                    px, py = px * 70.0 / rr, py * 70.0 / rr
                r = 13.0 * (1 - tt) ** 1.1 + 3.0
                # half buried: a low buttress ridge that dives into the ground (base top)
                pz = z0 + 0.30 * r + 7.0 * (1 - tt) ** 2 - 5.5 * tt ** 2
                pts.append((px, py, pz))
                rad.append(r)
            self.roots.append(dict(points=pts, radii=rad))
            self.branches.append(dict(points=pts, radii=rad, level=-1, n=0))

    # -------------------------------------------------------------- channels
    def _assign(self):
        self.tips = []
        for j, tip, d in self.sprig_nodes:
            self.tips.append(dict(pos=tuple(map(float, self.pos[j])), dir=d, limb=self.leader_of.get(j, 0),
                                  node=j, tip=tip))
        cx, cy = self.hub[0], self.hub[1]
        order = sorted(range(len(self.tips)),
                       key=lambda i: math.atan2(self.tips[i]["pos"][0] - cx, self.tips[i]["pos"][1] - cy))
        count = {c: 0 for c in CHANNELS}
        for rank, i in enumerate(order):
            ch = CHANNELS[rank % 4]
            self.tips[i]["channel"] = ch
            self.tips[i]["index"] = count[ch]      # position in the channel's series chain
            count[ch] += 1
            self.tips[i]["name"] = f"{ch}.{count[ch]:02d}"
        # sprigs carried by each branch (wood thickness check for the magnet wires)
        on = {}
        for t in self.tips:
            j = t["node"]
            while j >= 0:
                on[j] = on.get(j, 0) + 1
                j = self.par[j]
        self.sprigs_on_node = on

    # -------------------------------------------------------------- sprigs + LED leaves
    def _sprigs(self):
        """Map the planar flex sprig (sprig_layout) onto a gently arching 3D spray at each graft."""
        rng = self.rng
        self.sprig_paths, self.leaves = [], []
        for t in self.tips:
            d0 = t["dir"]
            side = v_norm(v_cross((0, 0, 1), d0)) if abs(d0[2]) < 0.95 else perp(d0)
            roll = rng.uniform(-0.4, 0.4)
            droop = rng.uniform(0.004, 0.010)        # rad/mm: the spray arches over like an elm spray
            cl, d = [t["pos"]], d0
            for k in range(60):
                d = v_norm(v_add(d, (0, 0, -droop)))
                cl.append(v_add(cl[-1], d))
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

    # -------------------------------------------------------------- samaras
    def _samaras(self):
        """Every other twig tip (not one carrying a sprig) gets an end-glow fibre and a samara:
        soft points of glow among the leaves."""
        tips = [i for i in range(self.fork + 1, len(self.pos))
                if not self.kidmap.get(i) and i not in self.sprig_tip_set]
        tips.sort(key=lambda i: math.atan2(self.pos[i][0] - self.hub[0], self.pos[i][1] - self.hub[1]))
        for k, i in enumerate(tips[::2]):
            d = self.pos[i] - self.pos[self.par[i]]
            self.samaras.append(dict(pos=tuple(map(float, self.pos[i])), dir=tuple(map(float, d / np.linalg.norm(d))),
                                     channel=CHANNELS[k % 4]))

    # -------------------------------------------------------------- foliage
    def _foliage(self):
        """Leaf-film foliage: small cedar-elm leaves set alternately (two ranks, in a nearly flat
        spray, as elms grow them) along the outer twigs. Laser-cut from light-diffusing olive
        film, so the LED leaves among them light them from inside the crown."""
        rng = self.rng
        P = self.pos
        for i in range(self.fork + 1, len(P)):
            if self.tipcount[i] > 4 or self.par[i] <= self.fork:
                continue
            a = P[self.par[i]]
            d = P[i] - a
            L = np.linalg.norm(d)
            if L < 1e-6:
                continue
            d = d / L
            # the spray plane: as horizontal as the twig allows
            side = np.cross(np.array([0, 0, 1.0]), d)
            side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-3 else np.array([1.0, 0, 0])
            nleaf = 4 if self.tipcount[i] > 1 else 5
            for k in range(nleaf):
                s = (k + rng.uniform(0.1, 0.9)) / nleaf
                base = a + d * L * s
                sgn = 1 if (i + k) % 2 else -1
                ang = math.radians(rng.uniform(35, 60))
                ax = d * math.cos(ang) + side * sgn * math.sin(ang)
                ax = ax + np.array([0, 0, rng.uniform(-0.25, 0.05)])
                ax /= np.linalg.norm(ax)
                nrm = np.cross(ax, side)
                if nrm[2] < 0:
                    nrm = -nrm
                nrm = nrm + np.array(self.nrng.normal(0, 0.25, 3))
                nrm /= np.linalg.norm(nrm)
                size = rng.uniform(4.6, 7.0)
                self.foliage.append(dict(pos=tuple(map(float, base)), axis=tuple(map(float, ax)),
                                         normal=tuple(map(float, nrm)), size=size))
            if not self.kidmap.get(i):   # a terminal leaf at every twig tip
                self.foliage.append(dict(pos=tuple(map(float, P[i])), axis=tuple(map(float, d)),
                                         normal=(0.0, 0.0, 1.0), size=rng.uniform(4.0, 5.4)))

    def summary(self):
        xs = [l["pos"][0] for l in self.foliage] + [l["pos"][0] for l in self.leaves]
        ys = [l["pos"][1] for l in self.foliage] + [l["pos"][1] for l in self.leaves]
        zs = [l["pos"][2] for l in self.foliage] + [l["pos"][2] for l in self.leaves]
        wood = [b for b in self.branches if b["level"] >= 1]
        return dict(nodes=len(self.pos), branches=len(wood), twig_tips=int(sum(1 for i in range(len(self.pos))
                    if not self.kidmap.get(i))), samaras=len(self.samaras), sprigs=len(self.tips),
                    leaves=len(self.leaves), foliage=len(self.foliage),
                    leader_d=[round(2 * b["radii"][min(9, len(b["radii"]) - 1)], 1) for b in self.branches if b["level"] == 1][:3],
                    hub=[round(v, 1) for v in self.hub], hub_r=round(self.hub_r, 1), trunk_d=round(2 * self.rad[self.fork // 2], 1),
                    x=(round(min(xs)), round(max(xs))), y=(round(min(ys)), round(max(ys))), z=(round(min(zs)), round(max(zs))))


if __name__ == "__main__":
    import time
    t0 = time.time()
    t = Tree()
    print(t.summary(), f"{time.time() - t0:.1f}s")
