"""Score a full Strands Decider checkpoint on RobotBench, as the reference ceiling.

Needs an env with strands_decider installed (not the sparrow runtime):

  python bench/robot/run_reference.py CKPT [--device mps] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import torch
from strands_decider.data.format import Example
from strands_decider.evaluate import collect_logits
from strands_decider.modeling import StrandsDeciderModel

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_robot import BENCH, judge  # noqa: E402

NOUL = [["false", "the statement does not hold for this state"], ["true", "the statement holds for this state"]]


def to_example(c):
    q = c["question"]
    if q["type"] == "noul":
        return Example("noul", c["state"], q["instructions"], NOUL, int(bool(c["expected"])))
    if q["type"] == "choice":
        opts = [[k, v] for k, v in q["criteria"].items()]
        return Example("choice", c["state"], q["instructions"], opts, [o[0] for o in opts].index(c["expected"]))
    opts = [[str(i), v] for i, v in enumerate(q["criteria"])]
    return Example("score", c["state"], q["instructions"], opts, int(c["expected"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ckpt")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--out")
    ap.add_argument("--bench", default=BENCH)
    a = ap.parse_args()
    try:
        model = StrandsDeciderModel.load(a.ckpt)
    except Exception:
        from strands_decider.vision import VisionDeciderModel
        model = VisionDeciderModel.load(a.ckpt)
    model.to(a.device).eval()
    cfg_path = os.path.join(a.ckpt, "strands_decider_config.json")
    temps = json.load(open(cfg_path)).get("temperature_by_kind", {}) if os.path.exists(cfg_path) else {}
    cases = [json.loads(l) for l in open(a.bench)]
    exs = [to_example(c) for c in cases]
    t0 = time.time()
    with torch.inference_mode():
        logits, _, slots, _ = collect_logits(model, exs, device=a.device, batch_size=4)
    sec = (time.time() - t0) / len(cases)
    fam, right = {}, 0
    for c, ex, lg, n in zip(cases, exs, logits, slots):
        p = torch.softmax(lg[: int(n)].float() / float(temps.get(ex.kind, 1.0)), -1)
        if ex.kind == "noul":
            ans = {"type": "noul", "noul": float(p[1])}
        elif ex.kind == "choice":
            ans = {"type": "choice", "choice": ex.options[int(p.argmax())][0]}
        else:
            ans = {"type": "score", "score": float((torch.arange(len(p)) * p).sum())}
        ok = judge(ans, c["expected"])
        if not ok and os.environ.get("V"):
            print("  x", c["id"], "want", c["expected"], "got", ans.get("choice", ans.get("noul", ans.get("score"))))
        right += ok
        f = fam.setdefault(c["family"], [0, 0])
        f[0] += ok
        f[1] += 1
    rep = {"model": os.path.basename(a.ckpt.rstrip("/")), "bench": os.path.basename(a.bench), "right": right,
           "n": len(cases), "acc": round(right / len(cases), 3),
           "per_family": {k: f"{v[0]}/{v[1]}" for k, v in sorted(fam.items())},
           "sec_per_q": round(sec, 3), "device": a.device}
    print(json.dumps(rep))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
