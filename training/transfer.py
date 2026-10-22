"""Build an unlabeled transfer set for distillation: new (state, question) pairings the
teacher never trained on. Labels come from the teacher; `label` here is a placeholder
(the teacher's argmax replaces it at training time).

  python training/transfer.py --out corpus/transfer.jsonl --n 150000
"""
from __future__ import annotations

import argparse
import json
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", nargs="+", default=["corpus/teacher_src.jsonl"])
    ap.add_argument("--extra", nargs="*", default=["corpus/catchall.jsonl", "corpus/synth_pairs.jsonl"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=150000)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    rows = [json.loads(l) for p in a.src for l in open(p)]
    short = [r for r in rows if len(str(r["state"])) < 2500]
    by_task: dict[str, list[dict]] = {}
    for r in short:
        by_task.setdefault(r["task"], []).append(r)
    tasks = list(by_task)
    out = []
    # extras (gold-labelled generators) go in as they are
    for p in a.extra:
        for l in open(p):
            r = json.loads(l)
            r["src"] = "extra"
            out.append(r)
    n_cross = int(a.n * 0.6)
    while len(out) < n_cross:
        t1, t2 = rng.sample(tasks, 2)
        s = rng.choice(by_task[t1])
        q = rng.choice(by_task[t2])
        ins = q["instructions"]
        if q.get("instruction_variants") and rng.random() < 0.5:
            ins = rng.choice(q["instruction_variants"])
        out.append({"kind": q["kind"], "state": s["state"], "instructions": ins, "options": q["options"],
                    "label": 0, "task": f"x:{t1}>{t2}", "weight": 1.0, "instruction_variants": [], "src": "cross"})
    while len(out) < a.n:
        r = rng.choice(short)
        if not r.get("instruction_variants"):
            continue
        v = dict(r)
        v["instructions"] = rng.choice(r["instruction_variants"])
        v["task"] = "v:" + r["task"]
        v["src"] = "variant"
        out.append(v)
    rng.shuffle(out)
    with open(a.out, "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(a.out, len(out))


if __name__ == "__main__":
    main()
