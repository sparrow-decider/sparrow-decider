"""Benchmark a .sparrow through the shipped numpy runtime: JevBench (v1.5 local proxy),
CPU latency per question, file size, peak RSS.

  python bench/bench_jev.py dist/model.sparrow [--threads 1] [--holdout FILE --n 2000]
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
# JevBench public tasks (all.jsonl) and the v1.5 proxy scorer (v15_proxy.py) from the Strands Decider repo
# (evaluation/jevbench). Point these at your copies.
JEV = os.environ.get("SPARROW_JEVBENCH", "")
PROXY = os.environ.get("SPARROW_JEV_PROXY", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--holdout", nargs="*", default=[])
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--out")
    a = ap.parse_args()
    if not (os.path.exists(JEV) and os.path.isdir(PROXY)):
        sys.exit("set SPARROW_JEVBENCH=/path/to/all.jsonl and SPARROW_JEV_PROXY=/path/to/evaluation/jevbench")
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[v] = str(a.threads)
    from sparrow_decider import Decider
    sys.path.insert(0, PROXY)
    import v15_proxy

    t0 = time.time()
    d = Decider.load(a.model)
    load_s = time.time() - t0
    tasks = [json.loads(l) for l in open(JEV)]
    res, lat = [], []
    d.probs("warm", {"type": "noul", "instructions": "warm up"})
    for t in tasks:
        q = t["question"]
        s = time.perf_counter()
        kind, names, _, p = d.probs(t["state"], q)
        lat.append(time.perf_counter() - s)
        if kind == "noul":
            probs = {"no": float(p[0]), "yes": float(p[1])}
            pred, ev = ("yes" if p[1] >= 0.5 else "no"), None
        else:
            probs = dict(zip(names, map(float, p)))
            pred = max(probs, key=probs.get)
            ev = sum(i * x for i, x in enumerate(p)) if kind == "score" else None
            if kind == "score":
                pred = int(pred)
        res.append({"task_id": t["id"], "family": t["family"], "correct": str(pred) == str(t["expected"]),
                    "probs": probs, "ordinal_ev": ev, "labels": t["labels"], "expected": t["expected"]})
    per, intel = v15_proxy.proxy(res)
    lat_ms = sorted(x * 1000 for x in lat)
    rep = {"model": os.path.basename(a.model), "file_mb": round(os.path.getsize(a.model) / 1e6, 2),
           "load_s": round(load_s, 2), "threads": a.threads,
           "jevbench": {"intelligence": round(intel, 1), "per_kind": {k: round(v, 1) for k, v in per.items()},
                        "right": sum(r["correct"] for r in res), "n": len(res)},
           "latency_ms": {"p50": round(statistics.median(lat_ms), 2), "p95": round(lat_ms[int(0.95 * len(lat_ms))], 2),
                          "mean": round(sum(lat_ms) / len(lat_ms), 2)},
           "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1 << 20 if sys.platform == "darwin" else 1 << 10), 1)}
    if a.holdout:
        sys.path.insert(0, os.path.join(ROOT, "training"))
        from data import load_rows
        rows = load_rows(a.holdout, a.n)
        by = {}
        for r in rows:
            q = {"type": r["kind"], "instructions": r["instructions"]}
            if r["kind"] == "choice":
                q["criteria"] = {n: dsc for n, dsc in r["options"]}
            elif r["kind"] == "score":
                q["criteria"] = [dsc for _, dsc in r["options"]]
            else:
                q["criteria"] = {n: dsc for n, dsc in r["options"]}
            _, _, _, p = d.probs(r["state"], q)
            by.setdefault(r.get("task", r["kind"]), []).append(int(p.argmax()) == int(r["label"]))
        allv = [x for v in by.values() for x in v]
        rep["holdout"] = {"acc": round(sum(allv) / len(allv), 3), "by_task": {k: round(sum(v) / len(v), 3) for k, v in sorted(by.items())}}
    print(json.dumps(rep, indent=1))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
