"""Check that the KiCad-exported netlist equals the design description (net for net)."""
import sys, importlib
from pcbutil import read_netlist


def check(design_module, netfile):
    sch = importlib.import_module(design_module).build()
    want = {}
    for p in sch.parts:
        for pin, net in p.nets.items():
            if net and not p.lib_id.startswith("power:"):
                want.setdefault(net, set()).add((p.ref, pin))
    _, got = read_netlist(netfile)
    got_sets = [set(v) - {(r, n) for r, n in v if r.startswith("#")} for v in got.values()]
    got_sets = [g for g in got_sets if g]
    errors = 0
    for net, nodes in want.items():
        match = [g for g in got_sets if nodes & g]
        if len(match) != 1 or match[0] != nodes:
            errors += 1
            print("MISMATCH", net, sorted(nodes), "->", [sorted(m) for m in match])
    print(f"{design_module}: {len(want)} design nets, {len(got_sets)} netlist nets, {errors} mismatches")
    return errors


if __name__ == "__main__":
    sys.exit(1 if check(sys.argv[1], sys.argv[2]) else 0)
