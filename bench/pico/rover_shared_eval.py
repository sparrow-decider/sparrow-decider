"""Zero-training check: can a shared nano answer the rover spec with no per-device training?
Each option states its trigger in its description (the gen_specs.py format), and the answers
are scored against the spec's rules on the same 600 held-out states as the pico report.

  python bench/pico/rover_shared_eval.py MODEL.sparrow --work RUN_DIR [--out FILE]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "python"))
from rover_eval import ACTIONS, oracle  # noqa: E402
from sparrow_decider import Decider  # noqa: E402

OPTIONS = {"continue": "keep driving toward the goal otherwise",
           "slow": "reduce speed when path is crowded or wet floor",
           "stop": "halt immediately when front_obstacle_m below 0.4",
           "dock": "go back and charge when battery below 15%",
           "replan": "plan a new route when path is blocked"}


def render(s):
    return "\n".join([f"battery: {s['battery']}%", f"front_obstacle_m: {s['front_obstacle_m']}", f"goal_m: {s['goal_m']}",
                      f"path: {s['path']}", f"carrying_load: {'yes' if s['carrying_load'] else 'no'}"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--work", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    d = Decider.load(a.model)
    states = json.load(open(f"{a.work}/states.json"))
    idx = np.random.RandomState(0).permutation(len(states))
    test = idx[int(len(idx) * 0.8):]
    ok_a = ok_c = 0
    for i in test:
        s, y = states[i], oracle(states[i])
        r = d.ask(render(s), {"a": {"type": "choice", "instructions": "What should the device do now?", "criteria": OPTIONS},
                              "c": {"type": "noul", "instructions": "Should the device dock? (go back and charge when battery below 15%)"}})
        ok_a += ACTIONS.index(r["a"]["choice"]) == y["action"]
        ok_c += (r["c"]["noul"] >= 0.5) == bool(y["need_charge"])
    rep = {"model": d.name, "bench": "rover-zero-training", "n": len(test),
           "action_vs_rules": round(ok_a / len(test), 3), "need_charge_vs_rules": round(ok_c / len(test), 3)}
    print(json.dumps(rep))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
