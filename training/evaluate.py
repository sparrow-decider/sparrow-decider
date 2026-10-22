"""Evaluate a trained tiny decider: JevBench (v1.5 local proxy) and held-out rows.

  .venv/bin/python training/evaluate.py runs/e17-gold [--holdout D/train_v5.holdout.jsonl --n 3000]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

import torch
from transformers import AutoTokenizer

sys.path.insert(0, os.path.dirname(__file__))
from data import NOUL_DEFAULT, load_rows, set_prune  # noqa: E402
from model import build_model  # noqa: E402
from train import collate  # noqa: E402

JEV = os.environ.get("SPARROW_JEVBENCH", "")
PROXY = os.environ.get("SPARROW_JEV_PROXY", "")


def jev_rows(path=JEV):
    out = []
    for line in open(path):
        t = json.loads(line)
        q = t["question"]
        if q["type"] == "noul":
            c = {**NOUL_DEFAULT, **(q.get("criteria") or {})}
            opts = [["false", c["false"]], ["true", c["true"]]]
        elif q["type"] == "choice":
            opts = [[k, v] for k, v in q["criteria"].items()]
        else:
            opts = [[str(i), d] for i, d in enumerate(q["criteria"])]
        out.append({"kind": q["type"], "state": t["state"], "instructions": q.get("instructions") or "",
                    "options": opts, "label": 0, "_task": t})
    return out


@torch.no_grad()
def predict(model, tok, rows, dev, max_len, temps=None, bs=32):
    model.eval()
    out = []
    rng = random.Random(0)
    for i in range(0, len(rows), bs):
        chunk = rows[i:i + bs]
        x, _, _, perm = collate(tok, chunk, max_len, rng, shuffle=False)
        logits = model(**{k: v.to(dev) for k, v in x.items()}).float().cpu()
        for r, lg in zip(chunk, logits):
            n = len(r["options"])
            t = (temps or {}).get(r["kind"], 1.0)
            out.append(torch.softmax(lg[:n] / t, -1).tolist())
    return out


def jev_result(r, p):
    t = r["_task"]
    k = r["kind"]
    if k == "noul":
        probs = {"no": p[0], "yes": p[1]}
        pred = "yes" if p[1] >= 0.5 else "no"
        ev = None
    else:
        names = [o[0] for o in r["options"]]
        probs = dict(zip(names, p))
        pred = max(probs, key=probs.get)
        ev = sum(i * x for i, x in enumerate(p)) if k == "score" else None
        if k == "score":
            pred = int(pred)
    return {"task_id": t["id"], "family": t["family"], "correct": str(pred) == str(t["expected"]),
            "predicted": pred, "probs": probs, "ordinal_ev": ev, "labels": t["labels"], "expected": t["expected"]}


def jevbench(model, tok, dev, max_len, outdir, temps=None):
    sys.path.insert(0, PROXY)
    import v15_proxy  # noqa
    rows = jev_rows()
    t0 = time.time()
    probs = predict(model, tok, rows, dev, max_len, temps)
    res = [jev_result(r, p) for r, p in zip(rows, probs)]
    with open(f"{outdir}/jev_results.jsonl", "w") as f:
        for x in res:
            f.write(json.dumps(x) + "\n")
    per, intel = v15_proxy.proxy(res)
    right = sum(x["correct"] for x in res)
    fam = {}
    for x in res:
        fam.setdefault(x["family"], []).append(x["correct"])
    return {"intelligence": round(intel, 1), "per_kind": {k: round(v, 1) for k, v in per.items()},
            "right": right, "n": len(res), "secs": round(time.time() - t0, 1),
            "by_family": {k: f"{sum(v)}/{len(v)}" for k, v in sorted(fam.items())}}


def fit_temps(model, tok, rows, dev, max_len):
    """Per-kind temperature by NLL grid search on held-out rows."""
    probs1 = predict(model, tok, rows, dev, max_len)
    temps = {}
    for k in ("noul", "choice", "score"):
        idx = [i for i, r in enumerate(rows) if r["kind"] == k]
        if not idx:
            continue
        logs = [torch.log(torch.tensor(probs1[i]).clamp_min(1e-9)) for i in idx]
        best = None
        for t in [x / 20 for x in range(6, 61)]:
            nll = sum(-torch.log_softmax(lg / t, -1)[int(rows[i]["label"])].item() for lg, i in zip(logs, idx)) / len(idx)
            if best is None or nll < best[0]:
                best = (nll, t)
        temps[k] = best[1]
    return temps


def holdout(model, tok, rows, dev, max_len, temps=None):
    probs = predict(model, tok, rows, dev, max_len, temps)
    by = {}
    for r, p in zip(rows, probs):
        by.setdefault(r.get("task", r["kind"]), []).append(max(range(len(p)), key=p.__getitem__) == int(r["label"]))
    acc = {k: round(sum(v) / len(v), 3) for k, v in sorted(by.items())}
    allv = [x for v in by.values() for x in v]
    return {"acc": round(sum(allv) / len(allv), 3), "by_task": acc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--holdout", nargs="*", default=[])
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--calib", nargs="*", default=[])
    a = ap.parse_args()
    args = json.load(open(f"{a.run}/args.json"))
    dev = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(args["encoder"])
    if args.get("keep"):
        set_prune(tok, json.load(open(args["keep"])))
    model = build_model(args.get("arch", "pointer"), args["encoder"], args.get("head_dim", 128), args.get("layers"))
    model.load_state_dict(torch.load(f"{a.run}/model.pt", map_location="cpu"))
    model.to(dev)
    ml = args["max_len"]
    rep = {}
    temps = None
    if a.calib:
        temps = fit_temps(model, tok, load_rows(a.calib, 3000), dev, ml)
        rep["temps"] = temps
    rep["jevbench_raw"] = jevbench(model, tok, dev, ml, a.run)
    if temps:
        rep["jevbench"] = jevbench(model, tok, dev, ml, a.run, temps)
    if a.holdout:
        rep["holdout"] = holdout(model, tok, load_rows(a.holdout, a.n), dev, ml, temps)
    json.dump(rep, open(f"{a.run}/eval.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
