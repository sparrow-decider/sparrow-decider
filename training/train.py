"""Train a tiny pointer decider.

  .venv/bin/python training/train.py --encoder jhu-clsp/ettin-encoder-17m --out runs/e17-gold \
      --data D/train_v5.jsonl ... --epochs 2
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer

sys.path.insert(0, os.path.dirname(__file__))
from data import encode, load_rows, set_prune, target  # noqa: E402
from model import build_model  # noqa: E402


def collate(tok, rows, max_len, rng, shuffle=True):
    ids_l, sp_l, ans_l, tg_l, perm_l, w_l, qs_l = [], [], [], [], [], [], []
    for r in rows:
        n = len(r["options"])
        perm = list(range(n))
        if shuffle:
            rng.shuffle(perm)
        opts = [tuple(r["options"][i]) for i in perm]
        ins = r["instructions"]
        if shuffle and r.get("instruction_variants") and rng.random() < 0.3:
            ins = rng.choice(r["instruction_variants"])
        ids, sp, ans, qs = encode(tok, r["kind"], r["state"], ins, opts, max_len)
        qs_l.append(qs)
        t = target(r)
        ids_l.append(ids); sp_l.append(sp); ans_l.append(ans)
        tg_l.append([t[i] for i in perm]); perm_l.append(perm); w_l.append(float(r.get("weight", 1.0)))
    B, T, K = len(rows), max(map(len, ids_l)), max(map(len, sp_l))
    ids = torch.full((B, T), tok.pad_token_id); attn = torch.zeros(B, T, dtype=torch.long)
    sp = torch.zeros(B, K, 2, dtype=torch.long); om = torch.zeros(B, K, dtype=torch.bool)
    tg = torch.zeros(B, K)
    for b in range(B):
        ids[b, :len(ids_l[b])] = torch.tensor(ids_l[b]); attn[b, :len(ids_l[b])] = 1
        k = len(sp_l[b])
        sp[b, :k] = torch.tensor(sp_l[b]); om[b, :k] = True; tg[b, :k] = torch.tensor(tg_l[b])
        sp[b, k:] = torch.tensor([0, 1])
    return dict(ids=ids, attn=attn, ospans=sp, omask=om, ans=torch.tensor(ans_l), qs=torch.tensor(qs_l)), tg, torch.tensor(w_l), perm_l


def batches(rows, tok_budget, tok_len):
    """Length-bucketed batches with ~tok_budget padded tokens each."""
    order = sorted(range(len(rows)), key=lambda i: tok_len[i])
    out, cur, mx = [], [], 0
    for i in order:
        mx2 = max(mx, tok_len[i])
        if cur and mx2 * (len(cur) + 1) > tok_budget:
            out.append(cur); cur, mx2 = [], tok_len[i]
        cur.append(i); mx = mx2
    if cur:
        out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoder", default="jhu-clsp/ettin-encoder-17m")
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--eval", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=2)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--tok-budget", type=int, default=16384)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--teacher", nargs="*", default=[], help="DATA.jsonl=TEACHER.jsonl pairs ({i, probs} by line of DATA)")
    ap.add_argument("--alpha", type=float, default=0.5, help="weight of teacher probs in the target")
    ap.add_argument("--init")
    ap.add_argument("--head-dim", type=int, default=128)
    ap.add_argument("--arch", default="pointer", choices=["pointer", "static"])
    ap.add_argument("--keep", help="json list of kept token ids (pruned-vocab training)")
    ap.add_argument("--layers", default=None, help="keep only these encoder layers, e.g. 0,3,6")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    dev = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(a.encoder)
    if a.keep:
        set_prune(tok, json.load(open(a.keep)))
    model = build_model(a.arch, a.encoder, a.head_dim, a.layers).to(dev)
    if a.init:
        model.load_state_dict(torch.load(a.init, map_location=dev))
    rows = load_rows(a.data, a.limit)
    if a.teacher:
        tp = {}
        for spec in a.teacher:
            dfile, tfile = spec.split("=")
            for line in open(tfile):
                x = json.loads(line)
                tp[(dfile, x["i"])] = x["probs"]
        hit = 0
        for r in rows:
            p = tp.get((r["_f"], r["_i"]))
            if p is not None:
                r["teacher"], r["alpha"] = p, (1.0 if r.get("src") == "cross" else a.alpha)
                hit += 1
        before = len(rows)
        rows = [r for r in rows if r.get("src") != "cross" or "teacher" in r]  # no gold for cross rows
        print(f"dropped {before - len(rows)} unlabeled cross rows", flush=True)
        print(f"teacher probs on {hit}/{len(rows)} rows, alpha {a.alpha}", flush=True)
    # rough length for bucketing: chars/3.5 capped
    tl = [min(a.max_len, int((len(str(r["state"])) + len(r["instructions"]) + sum(len(n) + len(d or "") for n, d in r["options"])) / 3.5) + 40) for r in rows]
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    bl = batches(rows, a.tok_budget, tl)
    total = int(len(bl) * a.epochs)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1, s / max(1, total * 0.05)) * max(0.0, 0.5 * (1 + math.cos(math.pi * s / total))))
    rng = random.Random(0)
    step, t0 = 0, time.time()
    print(f"rows {len(rows)} batches/epoch {len(bl)} steps {total} dev {dev}", flush=True)
    model.train()
    while step < total:
        rng.shuffle(bl)
        for b in bl:
            if step >= total:
                break
            x, tg, w, _ = collate(tok, [rows[i] for i in b], a.max_len, rng)
            x = {k: v.to(dev) for k, v in x.items()}
            with torch.autocast("cuda", dtype=torch.bfloat16, enabled=dev == "cuda"):
                logits = model(**x).float()
            logp = F.log_softmax(logits, -1)
            loss = (-(tg.to(dev) * logp).sum(-1) * w.to(dev)).sum() / w.sum().to(dev)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); step += 1
            if step % 200 == 0:
                print(f"step {step}/{total} loss {loss.item():.4f} {time.time() - t0:.0f}s", flush=True)
    torch.save(model.state_dict(), f"{a.out}/model.pt")
    json.dump(vars(a), open(f"{a.out}/args.json", "w"), indent=1)
    print("saved", a.out, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
