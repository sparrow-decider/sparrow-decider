"""C runtime vs numpy runtime on the same model: max probability difference, argmax agreement,
per-call latency. Cases: RobotBench, the robot eval set and a JevBench sample.

  python c/tests/parity.py MODEL.sparrow [--n 1500]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "python"))
sys.path.insert(0, os.path.join(ROOT, "c", "tools"))
from pack import load, pack  # noqa: E402
from sparrow_decider import Decider, _content, _options  # noqa: E402

KIND = {"noul": 0, "choice": 1, "score": 2}
JEV = os.environ.get("SPARROW_JEVBENCH", "")  # optional: adds JevBench states to the cases


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "")


def cases(n):
    out = [(json.loads(l)["state"], json.loads(l)["question"]) for l in open(os.path.join(ROOT, "bench/robot/robotbench_v0.jsonl"))]
    eval_rows = os.path.join(ROOT, "corpus/robot_eval.jsonl")
    for l in (list(open(eval_rows))[: n // 2] if os.path.exists(eval_rows) else []):
        r = json.loads(l)
        q = {"type": r["kind"], "instructions": r["instructions"]}
        if r["kind"] == "choice":
            q["criteria"] = dict(r["options"])
        elif r["kind"] == "score":
            q["criteria"] = [d for _, d in r["options"]]
        out.append((r["state"], q))
    if os.path.exists(JEV):
        out += [(t["state"], t["question"]) for t in map(json.loads, open(JEV))]
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--n", type=int, default=1500)
    ap.add_argument("--out")
    a = ap.parse_args()
    build = os.path.join(ROOT, "c", "build")
    os.makedirs(build, exist_ok=True)
    exe = os.path.join(build, "parity")
    subprocess.run(["cc", "-std=c99", *os.environ.get("SPARROW_CFLAGS", "-O3 -ffast-math").split(), "-Wall", "-Wextra", "-I", os.path.join(ROOT, "c/sparrow/include"),
                    os.path.join(ROOT, "c/sparrow/src/sparrow.c"), os.path.join(HERE, "parity_main.c"), "-lm", "-o", exe],
                   check=True)
    blob = pack(*load(a.model))
    spb = os.path.join(build, "parity_model.spb")
    open(spb, "wb").write(blob)
    d = Decider.load(a.model)
    lines, ref = [], []
    for state, q in cases(a.n):
        kind, opts = _options(q)
        if len(opts) > 16:
            continue
        st = _content(state)
        ins = _content(q.get("instructions"))
        lines.append("\t".join([str(KIND[kind]), esc(st), esc(ins), str(len(opts))] +
                               [esc(x) for o in opts for x in (o[0], o[1] or "")]))
        ref.append(d.probs(state, q)[3])
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write("\n".join(lines) + "\n")
    res = subprocess.run([exe, spb], stdin=open(f.name), capture_output=True, text=True, check=True)
    diffs, agree, us = [], 0, []
    for out, p in zip(res.stdout.splitlines(), ref):
        v = out.split()
        assert v[0] == "0", out
        us.append(float(v[1]))
        c = np.array([float(x) for x in v[2:]])
        diffs.append(float(np.abs(c - p).max()))
        agree += int(c.argmax() == p.argmax())
    rep = {"model": d.name, "bench": "c-parity", "cflags": os.environ.get("SPARROW_CFLAGS", "-O3 -ffast-math"),
           "blob_mb": round(len(blob) / 1e6, 3), "cases": len(ref), "max_abs_diff": round(max(diffs), 6),
           "mean_abs_diff": round(float(np.mean(diffs)), 7), "argmax_agree": f"{agree}/{len(ref)}",
           "c_us_p50": round(float(np.median(us)), 1)}
    print(json.dumps(rep))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
