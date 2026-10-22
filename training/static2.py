"""Static-embedding decider on Model2Vec potion embeddings (WordPiece, uncased).

Segments are pooled independently (state, question, each option), then an MLP scores
every option against the state and question, with a set-level contrast feature.

  python training/static2.py --data corpus/teacher_src.jsonl --out runs/pico [--teacher D=T ...]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer

sys.path.insert(0, os.path.dirname(__file__))
from data import HEADERS, load_rows, render_content, target  # noqa: E402


class Pico(nn.Module):
    def __init__(self, emb: np.ndarray, d: int = 384):
        super().__init__()
        V, H = emb.shape
        self.emb = nn.EmbeddingBag(V, H, mode="mean", padding_idx=0)
        self.emb.weight.data.copy_(torch.tensor(emb))
        self.kind = nn.Embedding(3, H)
        nn.init.normal_(self.kind.weight, std=0.02)
        self.mlp = nn.Sequential(nn.Linear(6 * H, d), nn.GELU(), nn.Linear(d, d), nn.GELU(), nn.Linear(d, 1))

    def pool(self, flat, offsets):
        return self.emb(flat, offsets)

    def forward(self, s, q, o, omask, kind):
        """s,q: B,H ; o: B,K,H"""
        q = q + self.kind(kind)
        n = lambda z: F.normalize(z, dim=-1)  # noqa: E731
        s, q, o = n(s), n(q), n(o)
        om = omask.float()[..., None]
        omean = (o * om).sum(1, keepdim=True) / om.sum(1, keepdim=True)
        s_, q_ = s[:, None].expand_as(o), q[:, None].expand_as(o)
        f = torch.cat([o, s_ * o, q_ * o, s_ * q_ * o, o - omean, (s_ - omean) * o], -1)
        return self.mlp(f).squeeze(-1).masked_fill(~omask, -1e4)


KINDS = {"noul": 0, "choice": 1, "score": 2}


def seg_ids(tok, texts, cache):
    out = []
    miss = [t for t in texts if t not in cache]
    if miss:
        for t, ids in zip(miss, tok(miss, add_special_tokens=False, truncation=True, max_length=512)["input_ids"]):
            cache[t] = ids or [0]
    return [cache[t] for t in texts]


def batchify(tok, rows, dev, rng=None, cache=None):
    cache = {} if cache is None else cache
    S, Q, O, K, tg, w = [], [], [], [], [], []
    for r in rows:
        n = len(r["options"])
        perm = list(range(n))
        if rng:
            rng.shuffle(perm)
        ins = r["instructions"]
        if rng and r.get("instruction_variants") and rng.random() < 0.3:
            ins = rng.choice(r["instruction_variants"])
        S.append(render_content(r["state"]))
        Q.append(render_content(ins))
        O.append([f"{r['options'][i][0]} {r['options'][i][1] or ''}" for i in perm])
        K.append(KINDS[r["kind"]])
        t = target(r)
        tg.append([t[i] for i in perm])
        w.append(float(r.get("weight", 1.0)))
    def flat(seqs):
        offs, fl = [], []
        for s in seqs:
            offs.append(len(fl))
            fl.extend(s)
        return torch.tensor(fl, device=dev), torch.tensor(offs, device=dev)
    sids = seg_ids(tok, S, cache)
    qids = seg_ids(tok, Q, cache)
    allo = [x for os_ in O for x in os_]
    oids = seg_ids(tok, allo, cache)
    Kmax = max(len(x) for x in O)
    return dict(s=flat(sids), q=flat(qids), o=flat(oids), counts=[len(x) for x in O], Kmax=Kmax,
                kind=torch.tensor(K, device=dev)), tg, torch.tensor(w, device=dev)


def run(model, b, dev):
    s = model.pool(*b["s"])
    q = model.pool(*b["q"])
    o_flat = model.pool(*b["o"])
    B, K = len(b["counts"]), b["Kmax"]
    o = torch.zeros(B, K, o_flat.shape[-1], device=dev)
    om = torch.zeros(B, K, dtype=torch.bool, device=dev)
    i = 0
    for j, c in enumerate(b["counts"]):
        o[j, :c] = o_flat[i:i + c]
        om[j, :c] = True
        i += c
    return model(s, q, o, om, b["kind"]), om


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="minishlab/potion-base-8M")
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--teacher", nargs="*", default=[])
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=4)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--emb-lr", type=float, default=2e-4)
    ap.add_argument("--bs", type=int, default=256)
    a = ap.parse_args()
    from model2vec import StaticModel
    os.makedirs(a.out, exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    sm = StaticModel.from_pretrained(a.base)
    tok = AutoTokenizer.from_pretrained(a.base)
    model = Pico(np.asarray(sm.embedding, dtype=np.float32)).to(dev)
    rows = load_rows(a.data)
    if a.teacher:
        tp = {}
        for spec in a.teacher:
            dfile, tfile = spec.split("=")
            for line in open(tfile):
                x = json.loads(line)
                tp[(dfile, x["i"])] = x["probs"]
        for r in rows:
            p = tp.get((r["_f"], r["_i"]))
            if p is not None:
                r["teacher"], r["alpha"] = p, (1.0 if r.get("src") == "cross" else a.alpha)
        rows = [r for r in rows if r.get("src") != "cross" or "teacher" in r]
    print(len(rows), "rows", dev, flush=True)
    opt = torch.optim.AdamW([{"params": model.emb.parameters(), "lr": a.emb_lr},
                             {"params": list(model.mlp.parameters()) + list(model.kind.parameters()), "lr": a.lr}], weight_decay=0.0)
    steps = int(len(rows) / a.bs * a.epochs)
    base_lrs = [g["lr"] for g in opt.param_groups]
    rng = random.Random(0)
    cache: dict = {}
    t0 = time.time()
    for step in range(steps):
        if step % (len(rows) // a.bs) == 0:
            rng.shuffle(rows)
        k = step % (len(rows) // a.bs)
        chunk = rows[k * a.bs:(k + 1) * a.bs]
        b, tg, w = batchify(tok, chunk, dev, rng, cache)
        logits, om = run(model, b, dev)
        T = torch.zeros_like(logits)
        for j, t in enumerate(tg):
            T[j, :len(t)] = torch.tensor(t)
        loss = (-(T * F.log_softmax(logits, -1)).sum(-1) * w).sum() / w.sum()
        f = 0.5 * (1 + math.cos(math.pi * step / steps))
        for g, lr in zip(opt.param_groups, base_lrs):
            g["lr"] = lr * f
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 500 == 0:
            print(f"step {step}/{steps} loss {loss.item():.4f} {time.time() - t0:.0f}s", flush=True)
    torch.save(model.state_dict(), f"{a.out}/model.pt")
    json.dump(vars(a), open(f"{a.out}/args.json", "w"), indent=1)
    print("saved", flush=True)


if __name__ == "__main__":
    main()
