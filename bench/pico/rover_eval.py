"""sparrow-pico rover: accuracy of the teacher and of the compiled pico heads against the
spec's own rules (the rules are in the teacher's prompt; the oracle applies them exactly).

  python bench/pico/rover_eval.py runs/pico-rover [--teacher teacher-2B.jsonl]
"""
import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "training"))
from pico_compile import featurize, forward  # noqa: E402

ACTIONS = ["continue", "slow", "stop", "dock", "replan"]


def oracle(s):
    if s["front_obstacle_m"] < 0.4:
        a = "stop"
    elif s["battery"] < 15:
        a = "dock"
    elif s["path"] == "blocked":
        a = "replan"
    elif s["path"] in ("crowded", "wet floor"):
        a = "slow"
    else:
        a = "continue"
    return {"action": ACTIONS.index(a), "need_charge": int(s["battery"] < 15)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--teacher", default="teacher.jsonl")
    ap.add_argument("--spec", default=os.path.join(ROOT, "c/examples/specs/rover.json"))
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    states = json.load(open(f"{a.work}/states.json"))
    rows = [json.loads(l) for l in open(f"{a.work}/rows.jsonl")]
    tp = {json.loads(l)["i"]: json.loads(l)["probs"] for l in open(os.path.join(a.work, a.teacher))}
    z = np.load(f"{a.work}/heads.npz")
    idx = np.random.RandomState(0).permutation(len(states))
    test = set(idx[int(len(idx) * 0.8):].tolist())
    rep = {}
    for qn in ("action", "need_charge"):
        layers = [(z[f"{qn}_{i}_w"], z[f"{qn}_{i}_b"]) for i in range(3)]
        t_ok = p_ok = n = 0
        for i, r in enumerate(rows):
            if r["q"] != qn or r["sid"] not in test or i not in tp:
                continue
            s = states[r["sid"]]
            y = oracle(s)[qn]
            t_ok += int(np.argmax(tp[i]) == y)
            p_ok += int(forward(layers, [featurize(spec, s)])[0].argmax() == y)
            n += 1
        rep[qn] = {"n": n, "teacher_vs_rules": round(t_ok / n, 3), "pico_vs_rules": round(p_ok / n, 3)}
    print(json.dumps(rep))


if __name__ == "__main__":
    main()
