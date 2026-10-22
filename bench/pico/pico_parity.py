"""Compile a generated sparrow-pico header on the host, run it on held-out states, and compare
with the numpy reference: max probability difference, argmax agreement, time per call.

  python bench/pico/pico_parity.py c/examples/specs/rover.json runs/pico-rover HEADER.h
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "training"))
from pico_compile import c_ident, featurize, forward, options  # noqa: E402


def main():
    spec_p, work, header = sys.argv[1:4]
    spec = json.load(open(spec_p))
    nm = c_ident(spec["name"])
    states = json.load(open(f"{work}/states.json"))[:500]
    z = np.load(f"{work}/heads.npz")
    fields = []
    for f in spec["features"]:
        fields.append(c_ident(f["name"]))
    src = [f'#include <stdio.h>', f'#include <time.h>', f'#include "{os.path.abspath(header)}"', "int main(void) {",
           f"  {nm}_state s; float p[16]; double t = 0; struct timespec a, b;"]
    for s in states:
        sets = []
        for f in spec["features"]:
            v = s[f["name"]]
            v = f["values"].index(v) if f["type"] == "enum" else (int(v) if f["type"] == "bool" else v)
            sets.append(f"s.{c_ident(f['name'])} = {v};")
        src.append("  " + " ".join(sets))
        for qn, q in spec["questions"].items():
            k = len(options(q))
            src.append(f"  clock_gettime(CLOCK_MONOTONIC, &a); {nm}_{c_ident(qn)}(&s, p); "
                       f"clock_gettime(CLOCK_MONOTONIC, &b); t += (b.tv_sec - a.tv_sec) * 1e9 + (b.tv_nsec - a.tv_nsec);")
            src.append(f'  for (int i = 0; i < {k}; i++) printf("%.7f ", p[i]); printf("\\n");')
    src += [f'  fprintf(stderr, "%.1f\\n", t / {len(states) * len(spec["questions"])});', "  return 0;", "}"]
    d = tempfile.mkdtemp()
    open(f"{d}/t.c", "w").write("\n".join(src))
    subprocess.run(["cc", "-O2", "-std=c99", f"{d}/t.c", "-lm", "-o", f"{d}/t"], check=True)
    r = subprocess.run([f"{d}/t"], capture_output=True, text=True, check=True)
    lines = r.stdout.splitlines()
    i, diffs, agree = 0, [], 0
    for s in states:
        x = [featurize(spec, s)]
        for qn in spec["questions"]:
            layers = [(z[f"{qn}_{j}_w"], z[f"{qn}_{j}_b"]) for j in range(3)]
            ref = forward(layers, x)[0]
            c = np.array([float(v) for v in lines[i].split()])
            diffs.append(float(np.abs(c - ref).max()))
            agree += int(c.argmax() == ref.argmax())
            i += 1
    print(json.dumps({"calls": i, "max_abs_diff": round(max(diffs), 7), "argmax_agree": f"{agree}/{i}",
                      "ns_per_call_host": float(r.stderr.strip())}))


if __name__ == "__main__":
    main()
