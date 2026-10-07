"""Tiny KiCad 9 schematic generator with a built-in orthogonal wire router.

Rule (see /CLAUDE.md): every signal connection is drawn as a visible wire.
Only power rails use power symbols.  The design lives in a plain Python
description (design_*.py); the PCB generators consume the netlist that
KiCad exports from the resulting schematic, so schematic and layout always
share one netlist.
"""
import heapq, math, uuid as _uuid
from kisexpr import Q, dump, lib_symbol, symbol_pins, find, find1

SYMDIR = "/usr/share/kicad/symbols"
VERT2 = {"Device:R", "Device:C", "Device:L", "Device:Polyfuse", "Device:Thermistor_NTC"}
# net -> (power symbol, body direction "down" for ground style / "up" for supply style)
POWER_SYMS = {"GND": ("power:GND", "down"), "+3V3": ("power:+3V3", "up"),
              "VBUS": ("power:VBUS", "up"), "VIN": ("power:+VDC", "up")}
NS = _uuid.UUID("6f1b0c64-2b3e-4f3a-9a51-6c1d6e0a7a11")
GRID = 1.27
PAPER = {"A2": (594, 420), "A3": (420, 297), "A1": (841, 594)}


def uid(*key):
    return Q(str(_uuid.uuid5(NS, "/".join(map(str, key)))))


def rot(px, py, deg):
    a = math.radians(deg)
    return (px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a))


def outward(angle):
    return {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[angle % 360]


def gi(v):
    return int(round(v / GRID))


class Part:
    def __init__(self, ref, lib_id, value, footprint, pos, nets, rot=0, fields=None,
                 in_bom=True, on_board=True, dnp=False, hide_value=False, **_):
        self.ref, self.lib_id, self.value, self.footprint = ref, lib_id, value, footprint
        self.pos, self.nets, self.rot = pos, nets, rot
        self.fields = fields or {}
        self.in_bom, self.on_board, self.dnp = in_bom, on_board, dnp
        self.hide_value = hide_value


class RouteError(RuntimeError):
    pass


class Schematic:
    def __init__(self, project, title, rev, paper="A2", comments=()):
        self.project, self.title, self.rev, self.paper = project, title, rev, paper
        self.comments = comments
        self.parts, self.texts, self.rects = [], [], []
        self.wires, self.junctions, self.items = [], [], []
        self.root = uid(project, "root")
        self.libs = {}
        self.npwr = 0
        self.flags = []
        self.failed = []

    def add(self, part):
        self.parts.append(part)
        return part

    def text(self, s, x, y, size=1.8, bold=False):
        self.texts.append((s, x, y, size, bold))

    def box(self, x0, y0, x1, y1, title=None):
        self.rects.append((x0, y0, x1, y1))
        if title:
            self.text(title, x0 + 2, y0 + 4, 2.5, True)

    def flag(self, net, x, y):
        """PWR_FLAG on a net; routed with a wire unless the net is a power rail."""
        self.flags.append((net, x, y))

    # ------------------------------------------------------------------ geometry
    def _sym(self, lib_id):
        if lib_id not in self.libs:
            self.libs[lib_id] = lib_symbol(SYMDIR, lib_id)
        return self.libs[lib_id]

    def pins_world(self, part):
        out, seen = [], set()
        pins = symbol_pins(self._sym(part.lib_id))
        pins.sort(key=lambda p: p["hidden"])
        for p in pins:
            dx, dy = rot(p["x"], p["y"], part.rot)
            x, y = part.pos[0] + dx, part.pos[1] - dy
            key = (gi(x), gi(y))
            stacked = key in seen
            seen.add(key)
            out.append((p, x, y, outward((p["angle"] + part.rot) % 360), stacked))
        return out

    def pin_xy(self, part, number):
        for p, x, y, d, st in self.pins_world(part):
            if p["number"] == number:
                return x, y
        raise KeyError(number)

    def body_bbox(self, lib_id, pos, r):
        sym = self._sym(lib_id)
        pts = []
        for sub in find(sym, "symbol"):
            parts = sub[1].rsplit("_", 2)
            if int(parts[-2]) not in (0, 1) or int(parts[-1]) not in (0, 1):
                continue
            for g in sub:
                if not isinstance(g, list):
                    continue
                if g[0] == "rectangle":
                    for k in ("start", "end"):
                        e = find1(g, k)
                        pts.append((float(e[1]), float(e[2])))
                elif g[0] in ("polyline", "bezier"):
                    for xy in find(find1(g, "pts"), "xy"):
                        pts.append((float(xy[1]), float(xy[2])))
                elif g[0] == "circle":
                    c = find1(g, "center")
                    rr = float(find1(g, "radius")[1])
                    pts += [(float(c[1]) - rr, float(c[2]) - rr), (float(c[1]) + rr, float(c[2]) + rr)]
                elif g[0] == "arc":
                    for k in ("start", "mid", "end"):
                        e = find1(g, k)
                        pts.append((float(e[1]), float(e[2])))
        if not pts:
            return None
        w = []
        for px, py in pts:
            dx, dy = rot(px, py, r)
            w.append((pos[0] + dx, pos[1] - dy))
        xs, ys = [p[0] for p in w], [p[1] for p in w]
        return min(xs), min(ys), max(xs), max(ys)

    # ------------------------------------------------------------------ router
    def _power_symbol(self, net, x, y, d):
        lib, style = POWER_SYMS[net]
        self._sym(lib)
        if style == "down":
            r = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[d]
        else:
            r = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}[d]
        self.npwr += 1
        self.items.append(("power", lib, net, x, y, r, "#PWR%03d" % self.npwr))
        # block the symbol area (about 2.5 mm beyond the pin point)
        cx, cy = gi(x), gi(y)
        for k in range(1, 5):
            for s in (-2, -1, 0, 1, 2):
                ox, oy = cx + d[0] * k + (s if d[1] else 0), cy + d[1] * k + (s if d[0] else 0)
                self.hard.add((ox, oy))

    def build(self):
        W, H = PAPER[self.paper]
        self.xmin, self.ymin, self.xmax, self.ymax = gi(12), gi(12), gi(W - 12), gi(H - 12)
        self.hard = set()          # blocked cells
        self.soft = {}             # extra cost per cell
        self.node = {}             # cell -> net (endpoints, bends, pins: exclusive)
        self.occ = {}              # cell -> {net: set('H','V')}
        self.edges = {}            # ((cell),(cell)) sorted -> net
        terms = {}                 # net -> list of terminal cells
        pin_cells = self.pin_cells = set()

        # FLAGS -> pseudo parts
        for net, x, y in self.flags:
            self._sym("power:PWR_FLAG")
            self.npwr += 1
            ref = "#FLG%03d" % self.npwr
            self.parts.append(Part(ref, "power:PWR_FLAG", "PWR_FLAG", "", (x, y), {"1": net},
                                   in_bom=False, on_board=False))

        # bodies, fields
        for part in self.parts:
            self._sym(part.lib_id)
            bb = self.body_bbox(part.lib_id, part.pos, part.rot)
            if bb:
                x0, y0, x1, y1 = bb
                for i in range(gi(x0) - 0, gi(x1) + 1):
                    for j in range(gi(y0) - 0, gi(y1) + 1):
                        self.hard.add((i, j))
                for i in range(gi(x0) - 1, gi(x1) + 2):
                    for j in range(gi(y0) - 1, gi(y1) + 2):
                        self.soft[(i, j)] = self.soft.get((i, j), 0) + 1.0

        for part in self.parts:
            pins = self.pins_world(part)
            numbers = {p["number"] for p, *_ in pins}
            missing = numbers - set(part.nets)
            if missing:
                raise ValueError(f"{part.ref}: unassigned pins {sorted(missing)}")
            for p, x, y, d, stacked in pins:
                # pin line itself is blocked (between the connection point and the body)
                L = gi(p["length"])
                for k in range(1, L + 1):
                    self.hard.add((gi(x) - d[0] * k, gi(y) - d[1] * k))
            for p, x, y, d, stacked in pins:
                if stacked:
                    continue
                net = part.nets[p["number"]]
                c = (gi(x), gi(y))
                pin_cells.add(c)
                if net is None:
                    self.items.append(("nc", x, y))
                    self.hard.add(c)
                    continue
                if net in POWER_SYMS and not part.lib_id.startswith("power:"):
                    s = (c[0] + 2 * d[0], c[1] + 2 * d[1])
                    self._add_path(net, [c, (c[0] + d[0], c[1] + d[1]), s])
                    self._power_symbol(net, s[0] * GRID, s[1] * GRID, d)
                    continue
                if part.lib_id == "power:PWR_FLAG" and net in POWER_SYMS:
                    self._power_symbol(net, x, y, (0, 1))
                    self.node[c] = net
                    continue
                s = (c[0] + d[0], c[1] + d[1])
                self._add_path(net, [c, s])
                terms.setdefault(net, []).append(s)
        # field text areas -> soft cost
        for part in self.parts:
            for (px, py, length) in self._field_boxes(part):
                for i in range(gi(px) - 1, gi(px + length) + 1):
                    for j in range(gi(py) - 1, gi(py) + 1):
                        self.soft[(i, j)] = self.soft.get((i, j), 0) + 2.5
        for s, x, y, size, bold in self.texts:
            for i in range(gi(x), gi(x + len(s) * size * 0.95) + 1):
                for j in range(gi(y - size * 1.2), gi(y) + 1):
                    self.soft[(i, j)] = self.soft.get((i, j), 0) + 2.0

        # route nets, shortest first
        def hpwl(cells):
            xs, ys = [c[0] for c in cells], [c[1] for c in cells]
            return (max(xs) - min(xs)) + (max(ys) - min(ys))
        order = sorted([n for n in terms if len(terms[n]) > 1], key=lambda n: hpwl(terms[n]))
        for net in order:
            ts = sorted(terms[net], key=lambda c: (c[0], c[1]))
            # start from the terminal nearest the centroid
            cx = sum(c[0] for c in ts) / len(ts)
            cy = sum(c[1] for c in ts) / len(ts)
            ts.sort(key=lambda c: abs(c[0] - cx) + abs(c[1] - cy))
            tree = {ts[0]}
            rest = ts[1:]
            while rest:
                # connect the remaining terminal closest to the tree
                rest.sort(key=lambda c: min(abs(c[0] - t[0]) + abs(c[1] - t[1]) for t in tree))
                t = rest.pop(0)
                if t in tree:
                    continue
                path = self._astar(net, t, tree)
                if path is None:
                    self.failed.append((net, t))
                    continue
                self._add_path(net, path)
                tree |= set(path)
                for c in path:
                    pass
        self._emit(pin_cells)
        if self.failed:
            raise RouteError("unrouted: %s" % self.failed)

    def _field_boxes(self, part):
        out = []
        for name in ("Reference", "Value"):
            if name == "Value" and part.hide_value:
                continue
            if part.lib_id.startswith("power:"):
                continue
            for node in self._props(part.lib_id, part.ref, part.value, part.footprint, part.pos[0], part.pos[1],
                                    part.rot, part.fields, part.ref, hide_val=part.hide_value):
                if str(node[1]) == name:
                    at = node[3]
                    s = str(node[2])
                    just_left = any(isinstance(e, list) and e[0] == "justify" for e in node[4])
                    ln = len(s) * 1.1
                    x = at[1] if just_left else at[1] - ln / 2
                    out.append((x, at[2], ln))
        return out

    def _add_path(self, net, path):
        for a, b in zip(path, path[1:]):
            key = (min(a, b), max(a, b))
            self.edges[key] = net
            o = "H" if a[1] == b[1] else "V"
            for c in (a, b):
                self.occ.setdefault(c, {}).setdefault(net, set()).add(o)
        # nodes: endpoints and bends
        self.node[path[0]] = net
        self.node[path[-1]] = net
        for a, b, c in zip(path, path[1:], path[2:]):
            if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
                self.node[b] = net

    def _astar(self, net, start, tree):
        tx0 = min(c[0] for c in tree); tx1 = max(c[0] for c in tree)
        ty0 = min(c[1] for c in tree); ty1 = max(c[1] for c in tree)

        def h(c):
            dx = tx0 - c[0] if c[0] < tx0 else (c[0] - tx1 if c[0] > tx1 else 0)
            dy = ty0 - c[1] if c[1] < ty0 else (c[1] - ty1 if c[1] > ty1 else 0)
            return dx + dy

        def joinable(c):
            o = self.occ.get(c, {})
            return all(n == net for n in o)

        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        best = {}
        pq = [(h(start), 0.0, start, None)]
        prev = {}
        hard, node, occ, edges, soft = self.hard, self.node, self.occ, self.edges, self.soft
        n_exp = 0
        while pq:
            f, g, c, d = heapq.heappop(pq)
            if best.get((c, d), 1e18) < g:
                continue
            if c in tree and c != start and joinable(c):
                # reconstruct
                path = [c]
                st = (c, d)
                while st in prev:
                    st = prev[st]
                    path.append(st[0])
                return path[::-1]
            n_exp += 1
            if n_exp > 400000:
                return None
            crossing = c != start and any(n != net for n in occ.get(c, {}))
            for nd in dirs:
                if crossing and nd != d:
                    continue
                if d is not None and nd == (-d[0], -d[1]):
                    continue
                nc = (c[0] + nd[0], c[1] + nd[1])
                if not (self.xmin <= nc[0] <= self.xmax and self.ymin <= nc[1] <= self.ymax):
                    continue
                if nc in hard and nc not in tree:
                    continue
                if nc in self.pin_cells:
                    continue
                nn = node.get(nc)
                if nn is not None and nn != net:
                    continue
                key = (min(c, nc), max(c, nc))
                en = edges.get(key)
                if en is not None and en != net:
                    continue
                o = "H" if nd[1] == 0 else "V"
                cost = 1.0 + soft.get(nc, 0)
                other = {n: s for n, s in occ.get(nc, {}).items() if n != net}
                if other:
                    if nc in tree:
                        continue
                    os_ = set().union(*other.values())
                    if o in os_ or len(os_) > 1:
                        continue
                    cost += 3.0
                else:
                    # discourage running right next to other nets
                    for ad in ((nd[1], nd[0]), (-nd[1], -nd[0])):
                        a2 = (nc[0] + ad[0], nc[1] + ad[1])
                        if any(n != net for n in occ.get(a2, {})):
                            cost += 1.5
                            break
                if d is not None and nd != d:
                    cost += 4.0
                    if c in node and node[c] != net:
                        continue
                ng = g + cost
                if ng < best.get((nc, nd), 1e18):
                    best[(nc, nd)] = ng
                    prev[(nc, nd)] = (c, d)
                    heapq.heappush(pq, (ng + h(nc), ng, nc, nd))
        return None

    def _emit(self, pin_cells):
        per_net = {}
        for (a, b), net in self.edges.items():
            adj = per_net.setdefault(net, {})
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
        for net, adj in per_net.items():
            def is_break(c):
                nb = adj.get(c, ())
                if len(nb) != 2 or c in pin_cells:
                    return True
                a, b = list(nb)
                return not (a[0] == b[0] == c[0] or a[1] == b[1] == c[1])

            done = set()
            for a in list(adj):
                for b in adj[a]:
                    k0 = (min(a, b), max(a, b))
                    if k0 in done:
                        continue
                    done.add(k0)
                    run = [a, b]
                    for end in (0, 1):
                        while True:
                            c = run[-1] if end else run[0]
                            p = run[-2] if end else run[1]
                            if is_break(c):
                                break
                            nxt = [n for n in adj[c] if n != p][0]
                            k = (min(c, nxt), max(c, nxt))
                            if k in done:
                                break
                            done.add(k)
                            if end:
                                run.append(nxt)
                            else:
                                run.insert(0, nxt)
                    self.wires.append((run[0][0] * GRID, run[0][1] * GRID, run[-1][0] * GRID, run[-1][1] * GRID))
            for c, nb in adj.items():
                if len(nb) >= 3:
                    self.junctions.append((c[0] * GRID, c[1] * GRID))
        self._check_crossings(per_net)

    def _check_crossings(self, per_net):
        """No wire endpoint of one net may touch another net's wire or pin."""
        cells = {}
        for net, adj in per_net.items():
            for c in adj:
                cells.setdefault(c, set()).add(net)
        ends = {}
        for x0, y0, x1, y1 in self.wires:
            for c in ((gi(x0), gi(y0)), (gi(x1), gi(y1))):
                ends.setdefault(c, 0)
                ends[c] += 1
        bad = [c for c, ns in cells.items() if len(ns) > 1 and c in ends]
        if bad:
            raise RouteError("endpoint on foreign wire at %s" % bad[:5])

    # ------------------------------------------------------------------ output
    def _props(self, lib_id, ref, value, footprint, x, y, r, fields, key, hide_ref=False, hide_val=False):
        sym = self._sym(lib_id)
        out = []
        base = {str(p[1]): p for p in sym if isinstance(p, list) and p[0] == "property"}
        vals = {"Reference": ref, "Value": value, "Footprint": footprint or "",
                "Datasheet": str(base["Datasheet"][2]) if "Datasheet" in base else ""}
        vals.update(fields)
        names = ["Reference", "Value", "Footprint", "Datasheet"] + [k for k in vals if k not in
                                                                   ("Reference", "Value", "Footprint", "Datasheet")]
        for name in names:
            bp = base.get(name)
            if bp is not None:
                at = [c for c in bp if isinstance(c, list) and c[0] == "at"][0]
                dx, dy = rot(float(at[1]), float(at[2]), r)
                px, py = x + dx, y - dy
            else:
                px, py = x, y
            hidden = name not in ("Reference", "Value") or (name == "Reference" and hide_ref) or \
                (name == "Value" and hide_val)
            eff = ["effects", ["font", ["size", 1.27, 1.27]]]
            if lib_id in VERT2 and name in ("Reference", "Value") and r in (0, 180):
                px, py = x + 2.54, y + (-1.27 if name == "Reference" else 1.27)
                eff.append(["justify", "left"])
            elif lib_id in VERT2 and name in ("Reference", "Value"):
                px, py = x + (-1.27 if name == "Reference" else 1.27), y - 2.54
                eff.append(["justify", "left"])
            if hidden:
                eff.append(["hide", "yes"])
            out.append(["property", Q(name), Q(vals[name]), ["at", round(px, 3), round(py, 3), 0], eff])
        return out

    def _instance(self, lib_id, ref, x, y, r, value, footprint, fields, key, in_bom=True, on_board=True,
                  dnp=False, hide_ref=False, hide_val=False):
        sym = self._sym(lib_id)
        node = ["symbol", ["lib_id", Q(lib_id)], ["at", round(x, 3), round(y, 3), r], ["unit", 1],
                ["exclude_from_sim", "no"], ["in_bom", "yes" if in_bom else "no"],
                ["on_board", "yes" if on_board else "no"], ["dnp", "yes" if dnp else "no"],
                ["uuid", uid(self.project, "sym", key)]]
        node += self._props(lib_id, ref, value, footprint, x, y, r, fields, key, hide_ref, hide_val)
        for p in symbol_pins(sym):
            node.append(["pin", Q(p["number"]), ["uuid", uid(self.project, "pin", key, p["number"])]])
        node.append(["instances", ["project", Q(self.project),
                                   ["path", Q("/" + self.root), ["reference", Q(ref)], ["unit", 1]]]])
        return node

    def write(self, path, date="2026-10-07"):
        try:
            self.build()
        finally:
            self._write(path, date)

    def _write(self, path, date):
        tb = ["title_block", ["title", Q(self.title)], ["date", Q(date)], ["rev", Q(self.rev)],
              ["company", Q("ECLIPSE desk lamp - open hardware")]]
        for i, c in enumerate(self.comments):
            tb.append(["comment", i + 1, Q(c)])
        root = ["kicad_sch", ["version", 20250114], ["generator", Q("eeschema")],
                ["generator_version", Q("9.0")], ["uuid", self.root], ["paper", Q(self.paper)], tb,
                ["lib_symbols"] + list(self.libs.values())]
        for s, x, y, size, bold in self.texts:
            font = ["font", ["size", size, size]] + ([["bold", "yes"]] if bold else [])
            root.append(["text", Q(s), ["exclude_from_sim", "no"], ["at", x, y, 0],
                         ["effects", font, ["justify", "left", "bottom"]], ["uuid", uid(self.project, "t", s, x, y)]])
        for i, (x0, y0, x1, y1) in enumerate(self.rects):
            root.append(["rectangle", ["start", x0, y0], ["end", x1, y1],
                         ["stroke", ["width", 0.25], ["type", "dash"]], ["fill", ["type", "none"]],
                         ["uuid", uid(self.project, "rect", i)]])
        for i, (x, y) in enumerate(self.junctions):
            root.append(["junction", ["at", round(x, 3), round(y, 3)], ["diameter", 0], ["color", 0, 0, 0, 0],
                         ["uuid", uid(self.project, "j", i)]])
        for i, (x0, y0, x1, y1) in enumerate(self.wires):
            root.append(["wire", ["pts", ["xy", round(x0, 3), round(y0, 3)], ["xy", round(x1, 3), round(y1, 3)]],
                         ["stroke", ["width", 0], ["type", "default"]], ["uuid", uid(self.project, "w", i)]])
        for i, it in enumerate(self.items):
            if it[0] == "nc":
                root.append(["no_connect", ["at", round(it[1], 3), round(it[2], 3)], ["uuid", uid(self.project, "nc", i)]])
        for i, it in enumerate(self.items):
            if it[0] == "power":
                _, lib, net, x, y, r, ref = it
                root.append(self._instance(lib, ref, x, y, r, net, "", {}, ref, in_bom=False, on_board=False,
                                           hide_ref=True))
        for part in self.parts:
            pw = part.lib_id.startswith("power:")
            root.append(self._instance(part.lib_id, part.ref, part.pos[0], part.pos[1], part.rot, part.value,
                                       part.footprint, part.fields, part.ref, part.in_bom, part.on_board, part.dnp,
                                       hide_ref=pw, hide_val=part.hide_value))
        root.append(["sheet_instances", ["path", Q("/"), ["page", Q("1")]]])
        root.append(["embedded_fonts", "no"])
        with open(path, "w") as f:
            f.write(dump(root) + "\n")
