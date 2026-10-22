"""Export a static2 (pico) run to .sparrow.  python training/export_pico.py runs/pico-g --out dist/pico.sparrow"""
from __future__ import annotations

import argparse
import io
import json
import os
import zipfile

import numpy as np
import torch
from huggingface_hub import hf_hub_download


def q8(w):
    s = np.abs(w).max(1) / 127.0
    s[s == 0] = 1.0
    return np.round(w / s[:, None]).astype(np.int8), s.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", required=True)
    ap.add_argument("--temps")
    a = ap.parse_args()
    args = json.load(open(f"{a.run}/args.json"))
    sd = {k: v.float().numpy() for k, v in torch.load(f"{a.run}/model.pt", map_location="cpu").items()}
    arrays = {}
    for k, v in sd.items():
        if v.ndim == 2:
            arrays[k + ".q8"], arrays[k + ".scale"] = q8(v)
        else:
            arrays[k] = v.astype(np.float32)
    tj = json.load(open(hf_hub_download(args["base"], "tokenizer.json")))
    cfg = {"arch": "static", "name": os.path.basename(a.out).removesuffix(".sparrow"), "base": args["base"],
           "temperature_by_kind": json.loads(a.temps) if a.temps else {}}
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("config.json", json.dumps(cfg, indent=1))
        zf.writestr("tokenizer.json", json.dumps({"vocab": tj["model"]["vocab"]}, ensure_ascii=False))
        zf.writestr("model.npz", buf.getvalue())
    print(a.out, f"{os.path.getsize(a.out) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
