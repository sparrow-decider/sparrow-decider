"""Train a Sparrow static model (sparrow-micro / sparrow-nano) and export it to .sparrow.

Generalises static2.py: optional vocabulary pruning (--vocab), PCA-reduced embeddings (--dim),
key-value number pooling (--kv), and a configurable MLP width (--hidden). Tokenization is the
runtime's WordPiece over the pruned vocabulary, so training and runtime see the same ids.

  python training/static3.py --data corpus/teacher_src.jsonl corpus/robot.jsonl \
      --teacher corpus/teacher_src.jsonl=corpus/teacher_v22.jsonl \
      --vocab 8192 --dim 128 --hidden 256 --kv --out runs/nano-a
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import random
import sys
import time
import zipfile
from collections import Counter

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "python"))
from data import load_rows, render_content, target  # noqa: E402
from sparrow_decider.static import KINDS, N_VF, kv_pairs, value_features  # noqa: E402
from sparrow_decider.wordpiece import WordPiece  # noqa: E402

SPECIAL = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]


class FastWP:
    """Runtime-identical WordPiece, with the HF Rust normalizer/pre-tokenizer for speed."""

    def __init__(self, hf_tok, vocab: dict[str, int], max_len: int = 512):
        self.norm = hf_tok.backend_tokenizer.normalizer
        self.pre = hf_tok.backend_tokenizer.pre_tokenizer
        self.wp = WordPiece(vocab)
        self.max_len = max_len
        self.cache: dict[str, list[int]] = {}

    def __call__(self, text: str) -> list[int]:
        c = self.cache.get(text)
        if c is not None:
            return c
        ids: list[int] = []
        for w, _ in self.pre.pre_tokenize_str(self.norm.normalize_str(text)):
            ids.extend(self.wp._word(w))
            if len(ids) >= self.max_len:
                break
        ids = ids[:self.max_len] or [0]
        if len(self.cache) < 3_000_000:
            self.cache[text] = ids
        return ids


def prune_vocab(full: dict[str, int], rows: list[dict], k: int, hf_tok) -> list[str]:
    """Top-k pieces by corpus frequency, plus specials and every single-character piece, so any
    word still tokenizes (greedy longest-match falls back to shorter pieces)."""
    enc = FastWP(hf_tok, full)
    cnt: Counter = Counter()
    for r in rows[:150000]:
        for t in [render_content(r["state"]), render_content(r["instructions"])] + \
                 [f"{n} {d or ''}" for n, d in r["options"]]:
            cnt.update(enc(t))
    id2p = {i: p for p, i in full.items()}
    must = set(SPECIAL) | {p for p in full if len(p) == 1 or (p.startswith("##") and len(p) == 3)}
    keep = [p for p in sorted(must, key=lambda p: full[p])]
    for i, _ in cnt.most_common():
        if len(keep) >= k:
            break
        p = id2p[i]
        if p not in must:
            keep.append(p)
    keep.sort(key=lambda p: (p != "[PAD]", full[p]))  # [PAD] stays id 0
    return keep


class SparrowStatic(nn.Module):
    def __init__(self, emb: np.ndarray, hidden: int, kv: bool):
        super().__init__()
        V, H = emb.shape
        self.kv = kv
        self.emb = nn.EmbeddingBag(V, H, mode="mean", padding_idx=0)
        self.emb.weight.data.copy_(torch.tensor(emb))
        self.kind = nn.Embedding(3, H)
        nn.init.normal_(self.kind.weight, std=0.02)
        nf = 10 if kv else 6
        if kv:
            self.g = nn.Linear(N_VF, H)
            self.tau = nn.Parameter(torch.tensor([5.0]))
        self.mlp = nn.Sequential(nn.Linear(nf * H, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU(),
                                 nn.Linear(hidden, 1))

    def forward(self, b):
        n = lambda z: F.normalize(z, dim=-1)  # noqa: E731
        s = self.emb(*b["s"])
        q = self.emb(*b["q"]) + self.kind(b["kind"])
        of = self.emb(*b["o"])
        B, K = len(b["counts"]), b["Kmax"]
        o = of.new_zeros(B, K, of.shape[-1])
        o[b["oi"], b["oj"]] = of
        om = b["omask"]
        s, q, o = n(s), n(q), n(o)
        omf = om.float()[..., None]
        omean = (o * omf).sum(1, keepdim=True) / omf.sum(1, keepdim=True)
        s_, q_ = s[:, None].expand_as(o), q[:, None].expand_as(o)
        feats = [o, s_ * o, q_ * o, s_ * q_ * o, o - omean, (s_ - omean) * o]
        if self.kv:
            H = o.shape[-1]
            P = b["Pmax"]
            pv = o.new_zeros(B, max(P, 1), H)
            el = o.new_zeros(B, max(P, 1), H)
            pm = torch.zeros(B, max(P, 1), dtype=torch.bool, device=o.device)
            if P:
                ek = n(self.emb(*b["k"]))
                lb = n(self.emb(*b["l"]))
                g = torch.tanh(self.g(b["vf"]))
                pv[b["pi"], b["pj"]] = ek * g
                el[b["pi"], b["pj"]] = lb
                pm[b["pi"], b["pj"]] = True
            cnt = pm.sum(1, keepdim=True).clamp(min=1).float()
            kv = (pv * pm[..., None]).sum(1) / cnt  # B,H
            att = (self.tau * torch.einsum("bkh,bph->bkp", o, el)).masked_fill(~pm[:, None], -1e4)
            att = torch.softmax(att, -1) * pm.any(1).float()[:, None, None]
            kvo = torch.einsum("bkp,bph->bkh", att, pv)
            kv_ = kv[:, None].expand_as(o)
            feats += [kv_ * o, kv_ * q_ * o, kvo, kvo * q_]
        f = torch.cat(feats, -1)
        return self.mlp(f).squeeze(-1).masked_fill(~om, -1e4)


def batchify(enc, rows, dev, kv, rng=None):
    S, Q, O, K, tg, w = [], [], [], [], [], []
    keys, labs, vfs, pi, pj = [], [], [], [], []
    for bi, r in enumerate(rows):
        n = len(r["options"])
        perm = list(range(n))
        if rng:
            rng.shuffle(perm)
        ins = r["instructions"]
        if rng and r.get("instruction_variants") and rng.random() < 0.3:
            ins = rng.choice(r["instruction_variants"])
        st = render_content(r["state"])
        S.append(enc(st))
        Q.append(enc(render_content(ins)))
        O.append([enc(f"{r['options'][i][0]} {r['options'][i][1] or ''}") for i in perm])
        K.append(KINDS[r["kind"]])
        t = target(r)
        tg.append([t[i] for i in perm])
        w.append(float(r.get("weight", 1.0)))
        if kv:
            for j, (k_, l_, v) in enumerate(kv_pairs(st)):
                keys.append(enc(k_))
                labs.append(enc(l_))
                vfs.append(value_features(v))
                pi.append(bi)
                pj.append(j)

    def flat(seqs):
        offs, fl = [], []
        for x in seqs:
            offs.append(len(fl))
            fl.extend(x)
        return torch.tensor(fl, device=dev), torch.tensor(offs, device=dev)

    counts = [len(x) for x in O]
    Kmax = max(counts)
    oi = torch.tensor([i for i, c in enumerate(counts) for _ in range(c)], device=dev)
    oj = torch.tensor([j for c in counts for j in range(c)], device=dev)
    omask = torch.zeros(len(rows), Kmax, dtype=torch.bool, device=dev)
    omask[oi, oj] = True
    b = dict(s=flat(S), q=flat(Q), o=flat([x for xs in O for x in xs]), counts=counts, Kmax=Kmax, oi=oi, oj=oj,
             omask=omask, kind=torch.tensor(K, device=dev))
    if kv:
        b["Pmax"] = (max(pj) + 1) if pj else 0
        if pj:
            b.update(k=flat(keys), l=flat(labs), vf=torch.tensor(vfs, dtype=torch.float32, device=dev),
                     pi=torch.tensor(pi, device=dev), pj=torch.tensor(pj, device=dev))
    return b, tg, torch.tensor(w, device=dev)


def q8(w):
    s = np.abs(w).max(1) / 127.0
    s[s == 0] = 1.0
    return np.round(w / s[:, None]).astype(np.int8), s.astype(np.float32)


def export(model: SparrowStatic, vocab: list[str], cfg: dict, path: str):
    arrays = {}
    for k, v in model.state_dict().items():
        v = v.float().cpu().numpy()
        if v.ndim == 2:
            arrays[k + ".q8"], arrays[k + ".scale"] = q8(v)
        else:
            arrays[k] = v.astype(np.float32)
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("config.json", json.dumps(cfg, indent=1))
        zf.writestr("tokenizer.json", json.dumps({"vocab": {p: i for i, p in enumerate(vocab)}}, ensure_ascii=False))
        zf.writestr("model.npz", buf.getvalue())
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="minishlab/potion-base-8M")
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--teacher", nargs="*", default=[])
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name")
    ap.add_argument("--epochs", type=float, default=4)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--emb-lr", type=float, default=2e-4)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--vocab", type=int, default=0, help="prune to this many pieces (0 = keep all)")
    ap.add_argument("--dim", type=int, default=0, help="PCA-reduce embeddings to this width (0 = keep)")
    ap.add_argument("--hidden", type=int, default=384)
    ap.add_argument("--kv", action="store_true")
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    torch.manual_seed(a.seed)
    from model2vec import StaticModel
    os.makedirs(a.out, exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    sm = StaticModel.from_pretrained(a.base)
    hf = AutoTokenizer.from_pretrained(a.base)
    full = hf.get_vocab()
    E = np.asarray(sm.embedding, dtype=np.float32)
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
    random.Random(1 + a.seed).shuffle(rows)
    if a.vocab:
        vocab = prune_vocab(full, rows, a.vocab, hf)
    else:
        vocab = sorted(full, key=full.get)
    E = E[[full[p] for p in vocab]]
    if a.dim and a.dim < E.shape[1]:
        _, _, Vt = np.linalg.svd(E, full_matrices=False)
        E = (E @ Vt[:a.dim].T).astype(np.float32)
    vmap = {p: i for i, p in enumerate(vocab)}
    enc = FastWP(hf, vmap, a.max_len)
    print(f"{len(rows)} rows on {dev}; vocab {len(vocab)} x {E.shape[1]}, kv={a.kv}, hidden={a.hidden}", flush=True)
    model = SparrowStatic(E, a.hidden, a.kv).to(dev)
    head = [p for n_, p in model.named_parameters() if not n_.startswith("emb.")]
    opt = torch.optim.AdamW([{"params": model.emb.parameters(), "lr": a.emb_lr}, {"params": head, "lr": a.lr}],
                            weight_decay=0.0)
    per_epoch = len(rows) // a.bs
    steps = int(per_epoch * a.epochs)
    base_lrs = [g["lr"] for g in opt.param_groups]
    rng = random.Random(a.seed)
    t0 = time.time()
    for step in range(steps):
        if step % per_epoch == 0:
            rng.shuffle(rows)
        k = step % per_epoch
        b, tg, w = batchify(enc, rows[k * a.bs:(k + 1) * a.bs], dev, a.kv, rng)
        logits = model(b)
        T = torch.zeros_like(logits)
        for j, t in enumerate(tg):
            T[j, :len(t)] = torch.tensor(t)
        loss = (-(T * F.log_softmax(logits, -1)).sum(-1) * w).sum() / w.sum()
        f = min(1.0, step / max(1, steps // 20)) * 0.5 * (1 + math.cos(math.pi * step / steps))
        for g, lr in zip(opt.param_groups, base_lrs):
            g["lr"] = lr * f
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 500 == 0:
            print(f"step {step}/{steps} loss {loss.item():.4f} {time.time() - t0:.0f}s", flush=True)
    torch.save(model.state_dict(), f"{a.out}/model.pt")
    json.dump({**vars(a), "vocab_size": len(vocab)}, open(f"{a.out}/args.json", "w"), indent=1)
    name = a.name or os.path.basename(a.out.rstrip("/"))
    cfg = {"arch": "static", "family": "sparrow-decider", "name": name, "base": a.base, "kv": a.kv,
           "dim": int(E.shape[1]), "hidden": a.hidden, "vocab_size": len(vocab), "max_len": a.max_len,
           "temperature_by_kind": {}}
    size = export(model, vocab, cfg, f"{a.out}/{name}.sparrow")
    print(f"saved; exported {name}.sparrow {size / 1e6:.2f} MB", flush=True)


if __name__ == "__main__":
    main()
