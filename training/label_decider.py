"""Label decider rows with a full Strands Decider checkpoint (teacher), on cuda, mps or cpu.

Runs in an env with strands_decider installed, not the sparrow venv:

  python training/label_decider.py CKPT rows.jsonl out.jsonl [--device mps]

Output: one {"i": row index, "probs": [...]} per row, in the row's option order, with the
checkpoint's per-kind temperatures applied. Resumable.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import torch
from strands_decider.data.format import Example
from strands_decider.evaluate import collect_logits
from strands_decider.modeling import StrandsDeciderModel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ckpt")
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=256)
    a = ap.parse_args()
    try:
        model = StrandsDeciderModel.load(a.ckpt)
    except Exception:
        from strands_decider.vision import VisionDeciderModel
        model = VisionDeciderModel.load(a.ckpt)
    model.to(a.device).eval()
    cfg = os.path.join(a.ckpt, "strands_decider_config.json")
    temps = json.load(open(cfg)).get("temperature_by_kind", {}) if os.path.exists(cfg) else {}
    rows = [json.loads(l) for l in open(a.src)]
    done = {json.loads(l)["i"] for l in open(a.out)} if os.path.exists(a.out) else set()
    todo = [i for i in range(len(rows)) if i not in done]
    print(f"{len(rows)} rows, {len(todo)} to label on {a.device}, temps {temps}", flush=True)
    t0 = time.time()
    with open(a.out, "a") as f, torch.inference_mode():
        for c in range(0, len(todo), a.chunk):
            idx = todo[c:c + a.chunk]
            exs = [Example(rows[i]["kind"], rows[i]["state"], rows[i]["instructions"],
                           [list(o) for o in rows[i]["options"]], int(rows[i].get("label", 0))) for i in idx]
            logits, _, slots, _ = collect_logits(model, exs, device=a.device, batch_size=a.batch)
            for i, ex, lg, n in zip(idx, exs, logits, slots):
                p = torch.softmax(lg[: int(n)].float() / float(temps.get(ex.kind, 1.0)), -1).tolist()
                f.write(json.dumps({"i": i, "probs": [round(x, 5) for x in p]}) + "\n")
            f.flush()
            print(f"{c + len(idx)}/{len(todo)} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
