"""Minimal S-expression reader/writer for KiCad files."""
import re, copy


class Q(str):
    """A quoted string atom."""


_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text):
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("parse error at %d" % pos)
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(Q(m.group(3).replace('\\"', '"').replace("\\\\", "\\")))
        else:
            cur.append(m.group(4))
    return cur[0] if len(cur) == 1 else cur


def dump(node, indent=0):
    if isinstance(node, list):
        if not node:
            return "()"
        simple = all(not isinstance(c, list) for c in node)
        if simple:
            return "(" + " ".join(dump(c) for c in node) + ")"
        out = "(" + dump(node[0])
        for c in node[1:]:
            if isinstance(c, list):
                out += "\n" + "\t" * (indent + 1) + dump(c, indent + 1)
            else:
                out += " " + dump(c)
        return out + "\n" + "\t" * indent + ")"
    if isinstance(node, Q):
        return '"' + node.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(node, float):
        s = ("%.4f" % node).rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(node)


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def find1(node, key):
    r = find(node, key)
    return r[0] if r else None


_libcache = {}


def load_lib(path):
    if path not in _libcache:
        _libcache[path] = parse(open(path).read())
    return _libcache[path]


def lib_symbol(libdir, lib_id):
    """Return flattened symbol definition named 'Lib:Name' ready for lib_symbols."""
    lib, name = lib_id.split(":")
    tree = load_lib(f"{libdir}/{lib}.kicad_sym")
    syms = {s[1]: s for s in find(tree, "symbol")}
    s = copy.deepcopy(syms[name])
    ext = find1(s, "extends")
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        pname = ext[1]
        child_props = find(s, "property")
        body = [c for c in parent if not (isinstance(c, list) and c[0] == "property")]
        # rename sub-symbols
        for c in body:
            if isinstance(c, list) and c[0] == "symbol":
                c[1] = Q(c[1].replace(pname, name, 1))
        s = body[:2] + child_props + body[2:]
        s[1] = Q(name)
    s[1] = Q(lib_id)
    return s


def symbol_pins(symdef):
    """List of dicts: number,name,type,x,y,angle,length,hidden (unit 1/0, style 1)."""
    pins = []
    for sub in find(symdef, "symbol"):
        nm = sub[1]
        parts = nm.rsplit("_", 2)
        unit, style = int(parts[-2]), int(parts[-1])
        if unit not in (0, 1) or style not in (0, 1):
            continue
        for p in find(sub, "pin"):
            at = find1(p, "at")
            pins.append(dict(
                type=p[1], number=str(find1(p, "number")[1]), name=str(find1(p, "name")[1]),
                x=float(at[1]), y=float(at[2]), angle=int(float(at[3])) if len(at) > 3 else 0,
                length=float(find1(p, "length")[1]),
                hidden=any(c == "hide" or (isinstance(c, list) and c[0] == "hide" and c[1] == "yes") for c in p)))
    return pins
