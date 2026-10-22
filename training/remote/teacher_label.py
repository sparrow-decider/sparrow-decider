"""Label a corpus with a decider checkpoint's calibrated option distribution.

Runs on a GPU box with sd-next installed (`pip install -e sd-next`):

    python teacher_label.py --ckpt CHECKPOINT_DIR --src corpus.jsonl --out teacher.jsonl

Output: one {"i": row index, "probs": [...]} per row, in the row's own option order, with
the checkpoint's per-kind temperatures applied. Resumable: rows already in --out are skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import torch

from strands_decider.data.format import read_jsonl
from strands_decider.evaluate import collect_logits
from strands_decider.modeling import StrandsDeciderModel
from strands_decider.vision import VisionDeciderModel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunk", type=int, default=2048)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--max-length", type=int, default=3072)
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(a.ckpt, "strands_decider_config.json")))
    temps = cfg.get("temperature_by_kind") or {}
    try:
        model = StrandsDeciderModel.load(a.ckpt)
    except Exception as e:  # LoRA trained on the multimodal torso
        print('text load failed, using VisionDeciderModel:', type(e).__name__, flush=True)
        model = VisionDeciderModel.load(a.ckpt)
    model.to("cuda").eval()
    exs = list(read_jsonl(a.src))
    done = set()
    if os.path.exists(a.out):
        done = {json.loads(l)["i"] for l in open(a.out)}
    todo = [i for i in range(len(exs)) if i not in done]
    # long rows last so batches are length-homogeneous
    todo.sort(key=lambda i: len(str(exs[i].state)))
    print(f"{len(exs)} rows, {len(todo)} to label, temps {temps}", flush=True)
    t0 = time.time()
    with open(a.out, "a") as f, torch.inference_mode():
        for c in range(0, len(todo), a.chunk):
            idx = todo[c:c + a.chunk]
            batch = [exs[i] for i in idx]
            bs = a.batch if len(str(batch[-1].state)) < 4000 else max(1, a.batch // 4)
            logits, _, slots, _ = collect_logits(model, batch, batch_size=bs, max_length=a.max_length)
            for i, ex, lg, n in zip(idx, batch, logits, slots):
                t = float(temps.get(ex.kind, 1.0))
                p = torch.softmax(lg[: int(n)] / t, -1).tolist()
                f.write(json.dumps({"i": i, "probs": [round(x, 5) for x in p]}) + "\n")
            f.flush()
            el = time.time() - t0
            print(f"{c + len(idx)}/{len(todo)} {el:.0f}s {(c + len(idx)) / el:.1f} rows/s", flush=True)


if __name__ == "__main__":
    main()
