"""JevBench + held-out accuracy for a static2 (pico) run.  python training/eval_pico.py runs/pico-g"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch
from transformers import AutoTokenizer

sys.path.insert(0, os.path.dirname(__file__))
from data import load_rows  # noqa: E402
from evaluate import PROXY, jev_result, jev_rows  # noqa: E402
from static2 import Pico, batchify, run  # noqa: E402


@torch.no_grad()
def probs(model, tok, rows, dev, bs=128):
    out = []
    for i in range(0, len(rows), bs):
        chunk = rows[i:i + bs]
        b, _, _ = batchify(tok, chunk, dev)
        lg, _ = run(model, b, dev)
        for r, l in zip(chunk, lg.cpu()):
            out.append(torch.softmax(l[:len(r["options"])], -1).tolist())
    return out


def main():
    run_dir = sys.argv[1]
    a = json.load(open(f"{run_dir}/args.json"))
    from model2vec import StaticModel
    dev = "cpu"
    sm = StaticModel.from_pretrained(a["base"])
    tok = AutoTokenizer.from_pretrained(a["base"])
    model = Pico(np.asarray(sm.embedding, dtype=np.float32))
    model.load_state_dict(torch.load(f"{run_dir}/model.pt", map_location="cpu"))
    model.eval()
    sys.path.insert(0, PROXY)
    import v15_proxy
    rows = jev_rows()
    res = [jev_result(r, p) for r, p in zip(rows, probs(model, tok, rows, dev))]
    per, intel = v15_proxy.proxy(res)
    rep = {"jevbench": {"intelligence": round(intel, 1), "per_kind": {k: round(v, 1) for k, v in per.items()},
                        "right": sum(x["correct"] for x in res)}}
    D = os.environ.get("SPARROW_HOLDOUT_DIR", "data")  # holds train_v5.holdout.jsonl
    hrows = load_rows([f"{D}/train_v5.holdout.jsonl", "corpus/families_eval.jsonl"], 3000)
    by = {}
    for r, p in zip(hrows, probs(model, tok, hrows, dev)):
        by.setdefault(r["task"], []).append(int(np.argmax(p)) == int(r["label"]))
    allv = [x for v in by.values() for x in v]
    rep["holdout"] = {"acc": round(sum(allv) / len(allv), 3), "by_task": {k: round(sum(v) / len(v), 3) for k, v in sorted(by.items())}}
    json.dump(rep, open(f"{run_dir}/eval.json", "w"), indent=1)
    print(json.dumps(rep))


if __name__ == "__main__":
    main()
