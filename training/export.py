"""Export a trained run to a `.sparrow` file: pruned vocab, int8 weights, numpy-loadable.

  .venv/bin/python training/export.py runs/e17-gold --vocab 16384 --out dist/x.sparrow [--temps '{"noul":1.0}']
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import sys
import zipfile

import numpy as np
import torch
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
COUNTS = os.path.join(ROOT, "corpus", "token_counts.json")


def token_counts(tok) -> collections.Counter:
    if os.path.exists(COUNTS):
        return collections.Counter({int(k): v for k, v in json.load(open(COUNTS)).items()})
    c = collections.Counter()
    srcs = [os.path.join(ROOT, "corpus", "teacher_src.jsonl")]
    for p in srcs:
        batch = []
        for line in open(p):
            r = json.loads(line)
            st = r["state"] if isinstance(r["state"], str) else json.dumps(r["state"], indent=2, ensure_ascii=False)
            batch += [st, r["instructions"]] + [f"{n} — {d}" for n, d in r["options"]]
            if len(batch) > 4096:
                for ids in tok(batch, add_special_tokens=False)["input_ids"]:
                    c.update(ids)
                batch = []
        for ids in tok(batch, add_special_tokens=False)["input_ids"]:
            c.update(ids)
    json.dump(dict(c), open(COUNTS, "w"))
    return c


def q8(w: np.ndarray):
    s = np.abs(w).max(1) / 127.0
    s[s == 0] = 1.0
    return np.round(w / s[:, None]).astype(np.int8), s.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--vocab", type=int, default=16384)
    ap.add_argument("--out", required=True)
    ap.add_argument("--temps", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--fp16", action="store_true", help="fp16 instead of int8")
    a = ap.parse_args()
    args = json.load(open(f"{a.run}/args.json"))
    enc_name = args["encoder"]
    tok = AutoTokenizer.from_pretrained(enc_name)
    tj = json.load(open(hf_hub_download(enc_name, "tokenizer.json")))
    vocab = {**tj["model"]["vocab"], **{t["content"]: t["id"] for t in tj["added_tokens"]}}
    id2p = {i: p for p, i in vocab.items()}
    added = [t["content"] for t in tj["added_tokens"] if not t["special"]]
    specials = ["[CLS]", "[SEP]", "[PAD]", "[UNK]", "[MASK]"]
    # must-keep: specials, added (space runs), every single byte char
    must = [vocab[s] for s in specials] + [vocab[s] for s in added]
    must += [i for p, i in tj["model"]["vocab"].items() if len(p) == 1]
    counts = token_counts(tok)
    if args.get("keep"):
        a.vocab = len(json.load(open(os.path.join(ROOT, args["keep"]) if not os.path.isabs(args["keep"]) else args["keep"])))
    keep = list(dict.fromkeys(must))
    for i, _ in counts.most_common():
        if len(keep) >= a.vocab:
            break
        if i not in keep:
            keep.append(i)
    keep_set = set(keep)
    keep.sort()
    new_of = {o: n for n, o in enumerate(keep)}
    cover = sum(v for k, v in counts.items() if k in keep_set) / sum(counts.values())
    print(f"vocab {len(keep)} covers {cover:.4%} of corpus tokens")

    sd = torch.load(f"{a.run}/model.pt", map_location="cpu")
    sd = {k: v.float().numpy() for k, v in sd.items()}
    emb_k = "encoder.embeddings.tok_embeddings.weight"
    sd[emb_k] = sd[emb_k][keep]
    arrays = {}
    for k, v in sd.items():
        if v.ndim == 2 and not a.fp16:
            arrays[k + ".q8"], arrays[k + ".scale"] = q8(v)
        elif v.ndim == 2:
            arrays[k] = v.astype(np.float16)
        else:
            arrays[k] = v.astype(np.float32)
    from transformers import AutoConfig
    c = AutoConfig.from_pretrained(enc_name)
    theta = (getattr(c, "rope_parameters", None) or {}).get("full_attention", {}).get("rope_theta") or c.global_rope_theta
    cfg = {"name": a.name or os.path.basename(a.out).removesuffix(".sparrow"), "base": enc_name,
           "encoder": {"hidden": c.hidden_size, "layers": c.num_hidden_layers, "heads": c.num_attention_heads,
                       "window": c.local_attention, "theta": float(theta), "global_every": c.global_attn_every_n_layers},
           "max_len": args["max_len"], "vocab": len(keep),
           "temperature_by_kind": json.loads(a.temps) if a.temps else {}}
    tk = {"pieces": [id2p[o] for o in keep], "merges": tj["model"]["merges"], "added": added}
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("config.json", json.dumps(cfg, indent=1))
        zf.writestr("tokenizer.json", json.dumps(tk, ensure_ascii=False))
        zf.writestr("model.npz", buf.getvalue())
    print(a.out, f"{os.path.getsize(a.out) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
