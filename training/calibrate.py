"""Fit per-kind temperatures for a .sparrow model on held-out rows (NLL grid search through the
shipped numpy runtime) and write them into a renamed copy of the model.

  python training/calibrate.py MODEL.sparrow --out release/sparrow-nano-robot-v1.0.sparrow \
      --name sparrow-nano-robot-v1.0 [--eval corpus/robot_eval.jsonl corpus/families_eval.jsonl ...]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
sys.path.insert(0, os.path.join(ROOT, "training"))
from data import load_rows  # noqa: E402
from sparrow_decider import Decider  # noqa: E402

DEFAULT_EVAL = ["corpus/robot_eval.jsonl", "corpus/families_eval.jsonl", "corpus/tasksource_eval.jsonl",
                "corpus/catchall_eval.jsonl", "corpus/synth_pairs_eval.jsonl"]


def logits_of(d: Decider, r: dict) -> np.ndarray:
    q = {"type": r["kind"], "instructions": r["instructions"]}
    if r["kind"] == "choice":
        q["criteria"] = {n: dsc for n, dsc in r["options"]}
    elif r["kind"] == "score":
        q["criteria"] = [dsc for _, dsc in r["options"]]
    else:
        q["criteria"] = {n: dsc for n, dsc in r["options"]}
    _, _, _, p = d.probs(r["state"], q)
    return np.log(np.maximum(p, 1e-12))  # temps are 1 while fitting, so log p = logits + const


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--eval", nargs="*", default=DEFAULT_EVAL)
    ap.add_argument("--n", type=int, default=4000)
    a = ap.parse_args()
    d = Decider.load(a.model)
    if d.static:
        d.static.cfg["temperature_by_kind"] = {}
    d.temps = {}
    rows = load_rows([os.path.join(ROOT, p) if not os.path.isabs(p) else p for p in a.eval], a.n)
    by = {}
    for r in rows:
        by.setdefault(r["kind"], []).append((logits_of(d, r), int(r["label"])))
    grid = np.exp(np.linspace(np.log(0.3), np.log(4.0), 60))
    temps, rep = {}, {}
    for kind, items in by.items():
        def nll(t):
            tot = 0.0
            for lg, y in items:
                z = lg / t
                z = z - z.max()
                tot -= z[y] - np.log(np.exp(z).sum())
            return tot / len(items)
        best = min(grid, key=nll)
        temps[kind] = round(float(best), 3)
        rep[kind] = {"n": len(items), "nll_t1": round(float(nll(1.0)), 4), "nll_fit": round(float(nll(best)), 4),
                     "acc": round(float(np.mean([lg.argmax() == y for lg, y in items])), 4)}
    with zipfile.ZipFile(a.model) as zi, zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            b = zi.read(it.filename)
            if it.filename == "config.json":
                c = json.loads(b)
                c.update(name=a.name, family="sparrow-decider", temperature_by_kind=temps)
                b = json.dumps(c, indent=1).encode()
            zo.writestr(it.filename, b)
    print(json.dumps({"model": a.name, "temperature_by_kind": temps, "fit": rep}))


if __name__ == "__main__":
    main()
