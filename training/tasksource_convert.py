"""tasksource-instruct rows with a quoted option list -> decider rows. Commercial-use
licences only; tasks overlapping our held-out evaluation are skipped; capped per task.

  python -I training/tasksource_convert.py ext/tasksource/*.parquet --out corpus/tasksource.jsonl
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re

import pyarrow.parquet as pq

CLAUSE = re.compile(r'With no explanation,\s*(.*?)\s*(?:with either|either|from|with one of|one of)\s+((?:"[^"\n]+"(?:,\s*|,? or\s+)?)+)\.?', re.S)
OPT = re.compile(r'"([^"\n]+)"')
HELDOUT = ("emotion", "massive", "sarcasm", "hate", "jev")


def convert(r):
    m = CLAUSE.search(r["inputs"])
    if not m:
        return None
    opts = list(dict.fromkeys(OPT.findall(m.group(2))))
    tgt = r["targets"].strip().rstrip(".").strip()
    if not 2 <= len(opts) <= 20 or tgt not in opts:
        return None
    before = r["inputs"][:m.start()].strip()
    after = r["inputs"][m.end():].strip()
    verb = m.group(1).strip().rstrip(",")
    verb = verb[0].upper() + verb[1:] if verb else "Label the following"
    if verb.lower().startswith("answer"):
        verb = "Answer"
    ins = (before + " " if before else "") + verb + "."
    if not after:
        return None
    low = {o.lower() for o in opts}
    if low in ({"yes", "no"}, {"true", "false"}):
        y = [o for o in opts if o.lower() in ("yes", "true")][0]
        n = [o for o in opts if o.lower() in ("no", "false")][0]
        return {"kind": "noul", "state": after, "instructions": ins,
                "options": [["false", n], ["true", y]], "label": int(tgt == y)}
    return {"kind": "choice", "state": after, "instructions": ins,
            "options": [[o, ""] for o in opts], "label": opts.index(tgt)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--eval-out")
    ap.add_argument("--per-task", type=int, default=400)
    a = ap.parse_args()
    by = collections.defaultdict(list)
    for f in a.files:
        for r in pq.read_table(f, columns=["inputs", "targets", "task", "license_use"]).to_pylist():
            if r["license_use"] != "commercial" or any(h in r["task"].lower() for h in HELDOUT):
                continue
            if len(by[r["task"]]) >= a.per_task + 50:
                continue
            x = convert(r)
            if x and len(x["state"]) < 3000:
                x.update(task="ts:" + r["task"], weight=1.0, instruction_variants=[])
                by[r["task"]].append(x)
    rng = random.Random(0)
    tr, ev = [], []
    for t, rows in by.items():
        rng.shuffle(rows)
        ev += rows[:20]
        tr += rows[20:20 + a.per_task]
    rng.shuffle(tr)
    with open(a.out, "w") as f:
        for x in tr:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    if a.eval_out:
        with open(a.eval_out, "w") as f:
            for x in ev:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(len(by), "tasks", len(tr), "train", len(ev), "eval", collections.Counter(x["kind"] for x in tr))


if __name__ == "__main__":
    main()
