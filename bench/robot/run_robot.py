"""Score a .sparrow model on RobotBench through the shipped numpy runtime.

  python bench/robot/run_robot.py release/sparrow-micro-general-v1.0.sparrow [--out FILE] [-v]

A choice is right when its argmax is the expected option, a noul when P(true) is on the
expected side of 0.5, a score when its expected level rounds to the expected level.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "python"))
BENCH = os.path.join(HERE, "robotbench_v0.jsonl")


def judge(ans: dict, expected) -> bool:
    if ans["type"] == "noul":
        return (ans["noul"] >= 0.5) == bool(expected)
    if ans["type"] == "choice":
        return ans["choice"] == expected
    return round(ans["score"]) == int(expected)


def run(ask, cases, verbose=False):
    fam, lat = defaultdict(lambda: [0, 0]), []
    for c in cases:
        t = time.perf_counter()
        a = ask(c["state"], {"q": c["question"]})["q"]
        lat.append((time.perf_counter() - t) * 1000)
        ok = judge(a, c["expected"])
        fam[c["family"]][0] += ok
        fam[c["family"]][1] += 1
        if verbose and not ok:
            got = a.get("choice", a.get("noul", a.get("score")))
            print(f"  x {c['id']:11s} want {c['expected']!s:9s} got {got}")
    right = sum(v[0] for v in fam.values())
    return {"right": right, "n": len(cases), "acc": round(right / len(cases), 3),
            "per_family": {k: f"{v[0]}/{v[1]}" for k, v in sorted(fam.items())},
            "p50_ms": round(statistics.median(lat), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--bench", default=BENCH)
    ap.add_argument("--out")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    from sparrow_decider import Decider
    d = Decider.load(a.model)
    cases = [json.loads(l) for l in open(a.bench)]
    d.ask("warm", {"q": {"type": "noul", "instructions": "warm"}})
    rep = {"model": d.name, "bench": os.path.basename(a.bench), **run(d.ask, cases, a.v)}
    print(json.dumps(rep))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
