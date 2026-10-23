"""Generic device-rule rows: random devices, random sensors, and options whose descriptions state
their trigger ("dock: go charge when battery below 15%"). Gold labels apply the triggers exactly.
Teaches a shared model to read a value, find the option whose trigger names that sensor, and
compare the value with the stated threshold, so any spec can be answered without training.

  python training/gen_specs.py --n 80000 --seed 3 --out corpus/specs.jsonl
"""
from __future__ import annotations

import argparse
import json
import random

R: random.Random

NUMERIC = [  # name, unit, lo, hi, decimals
    ("battery", "%", 0, 100, 0), ("temp_c", "", -20, 120, 1), ("motor_temp_c", "", 10, 130, 0),
    ("pressure_kpa", "", 50, 400, 0), ("humidity", "%", 0, 100, 0), ("speed_mps", "", 0, 5, 2),
    ("front_obstacle_m", "", 0, 10, 2), ("distance_m", "", 0, 100, 1), ("voltage", "", 0, 24, 2),
    ("current_a", "", 0, 30, 1), ("rpm", "", 0, 6000, 0), ("tank_level", "%", 0, 100, 0),
    ("co2_ppm", "", 300, 3000, 0), ("soil_moisture", "%", 0, 100, 0), ("vibration_g", "", 0, 4, 2),
    ("signal_dbm", "", -110, -30, 0), ("load_kg", "", 0, 50, 1), ("light_lux", "", 0, 2000, 0),
    ("water_flow_lpm", "", 0, 40, 1), ("cpu_temp_c", "", 20, 100, 0), ("tilt_deg", "", 0, 60, 1),
    ("noise_db", "", 20, 120, 0), ("heartbeat_age_s", "", 0, 300, 0), ("queue_length", "", 0, 50, 0),
]
ENUMS = [("path", ["clear", "blocked", "crowded", "wet floor"]), ("mode", ["auto", "manual", "standby"]),
         ("door", ["open", "closed"]), ("weather", ["sunny", "rain", "storm", "fog"]),
         ("network", ["online", "offline", "degraded"]), ("lid", ["open", "closed", "jammed"])]
ACTIONS = [("stop", "halt immediately"), ("dock", "go back and charge"), ("slow", "reduce speed"),
           ("replan", "plan a new route"), ("alert", "notify an operator"), ("cool", "turn on cooling"),
           ("heat", "turn on the heater"), ("water", "start watering"), ("vent", "open the vents"),
           ("shutdown", "power down safely"), ("reboot", "restart the controller"), ("refill", "refill the tank"),
           ("throttle", "reduce power"), ("hold", "wait in place"), ("reconnect", "re-establish the link")]
DEFAULTS = [("continue", "keep going"), ("normal", "carry on as usual"), ("idle", "do nothing"),
            ("monitor", "keep monitoring")]
DEVICES = ["rover", "greenhouse controller", "drone", "boiler", "battery pack", "pump station", "robot arm",
           "cold-storage unit", "wearable", "smart lock", "conveyor", "air purifier", "solar inverter"]


def fmt(v, dec):
    return f"{v:.{dec}f}" if dec else str(int(round(v)))


def make_device():
    nums = R.sample(NUMERIC, R.randint(2, 5))
    enums = R.sample(ENUMS, R.randint(0, 2))
    n_rules = R.randint(2, min(5, len(nums) + len(enums)))
    acts = R.sample(ACTIONS, n_rules)
    triggers = R.sample([("num", f) for f in nums] + [("enum", e) for e in enums], n_rules)
    rules = []
    for (name, desc), (kind, f) in zip(acts, triggers):
        if kind == "num":
            fname, unit, lo, hi, dec = f
            thr = R.uniform(lo + 0.15 * (hi - lo), hi - 0.15 * (hi - lo))
            thr = float(fmt(thr, dec))
            op = R.choice(["<", ">"])
            word = R.choice(["below", "under", "less than"]) if op == "<" else R.choice(["above", "over", "more than"])
            text = f"{desc} when {fname} {word} {fmt(thr, dec)}{unit}"
            rules.append({"action": name, "kind": "num", "f": fname, "op": op, "thr": thr, "text": text})
        else:
            fname, vals = f
            v = R.choice(vals)
            rules.append({"action": name, "kind": "enum", "f": fname, "val": v, "text": f"{desc} when {fname} is {v}"})
    dname, ddesc = R.choice(DEFAULTS)
    return {"device": R.choice(DEVICES), "nums": nums, "enums": enums, "rules": rules,
            "default": (dname, f"{ddesc} otherwise")}


def fires(rule, st):
    v = st[rule["f"]]
    if rule["kind"] == "enum":
        return v == rule["val"]
    return v < rule["thr"] if rule["op"] == "<" else v > rule["thr"]


def sample_state(dev, want=None):
    """A state where exactly `want` (a rule index) fires, or none fires when want is None."""
    for _ in range(200):
        st = {}
        for fname, unit, lo, hi, dec in dev["nums"]:
            st[fname] = float(fmt(R.uniform(lo, hi), dec))
        for fname, vals in dev["enums"]:
            st[fname] = R.choice(vals)
        fired = [i for i, r in enumerate(dev["rules"]) if fires(r, st)]
        if (want is None and not fired) or fired == [want]:
            return st
    return None


def render(dev, st):
    lines = []
    for fname, unit, lo, hi, dec in dev["nums"]:
        lines.append(f"{fname}: {fmt(st[fname], dec)}{unit}")
    for fname, vals in dev["enums"]:
        lines.append(f"{fname}: {st[fname]}")
    R.shuffle(lines)
    if R.random() < 0.4:
        lines.insert(0, f"device: {dev['device']}")
    return "\n".join(lines)


def row(kind, state, ins, opts, label, task):
    return {"kind": kind, "state": state, "instructions": ins, "options": opts, "label": label, "task": task,
            "weight": 1.0, "src": "specs"}


def main():
    global R
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=80000)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = random.Random(a.seed)
    noul = [["false", "the statement does not hold for this state"], ["true", "the statement holds for this state"]]
    n = 0
    with open(a.out, "w") as f:
        while n < a.n:
            dev = make_device()
            for _ in range(4):
                want = R.choice(list(range(len(dev["rules"]))) + [None])
                st = sample_state(dev, want)
                if st is None:
                    continue
                state = render(dev, st)
                opts = [[r["action"], r["text"]] for r in dev["rules"]] + [list(dev["default"])]
                order = list(range(len(opts)))
                R.shuffle(order)
                opts = [opts[i] for i in order]
                gold = order.index(want if want is not None else len(dev["rules"]))
                ins = R.choice(["What should the device do now?", "Which action applies?", "Pick the action for this state.",
                                f"What should the {dev['device']} do?"])
                f.write(json.dumps(row("choice", state, ins, opts, gold, "spec_action")) + "\n")
                n += 1
                # yes/no: does one rule's trigger hold?
                r = R.choice(dev["rules"])
                f.write(json.dumps(row("noul", state, f"Should the device {r['action']}? ({r['text']})", noul,
                                       int(fires(r, st)), "spec_check")) + "\n")
                n += 1


if __name__ == "__main__":
    main()
