"""Pack a static .sparrow model (micro/nano) into the flat SPB1 blob the C runtime reads.

  python c/tools/pack.py MODEL.sparrow -o model.spb [--header model.h --symbol sparrow_model_blob]

Layout (little-endian, every section 4-byte aligned):

  magic "SPB1" | u32 version=1 | u32 flags (bit0 = kv, bit1 = block gains) | u32 V | u32 D | u32 HIDDEN | u32 NF | u32 MAX_LEN
  f32 temps[3] (noul, choice, score) | u32 unk_id
  u32 strbytes | u8 strings[strbytes]      vocabulary pieces, NUL-terminated, sorted by bytes
  u32 str_off[V]                           offset of each sorted piece in strings
  u32 str_id[V]                            token id of each sorted piece
  i8 emb[V*D] | f32 emb_scale[V]
  f32 kind[3*D]
  (kv) f32 g_w[D*4] | f32 g_b[D] | f32 tau
  (gains) f32 gain[NF]                     feature block b is multiplied by gain[b]; w0 is divided by it
  i8 w0[HIDDEN*NF*D] | f32 s0[HIDDEN] | f32 b0[HIDDEN]
  i8 w2[HIDDEN*HIDDEN] | f32 s2[HIDDEN] | f32 b2[HIDDEN]
  f32 w4[HIDDEN] | f32 b4
"""
from __future__ import annotations

import argparse
import io
import json
import struct
import zipfile

import numpy as np


def q8(w):
    s = np.abs(w).max(1) / 127.0
    s[s == 0] = 1.0
    return np.round(w / s[:, None]).astype(np.int8), s.astype(np.float32)


def load(path):
    with zipfile.ZipFile(path) as zf:
        cfg = json.loads(zf.read("config.json"))
        vocab = json.loads(zf.read("tokenizer.json"))["vocab"]
        with np.load(io.BytesIO(zf.read("model.npz"))) as z:
            arr = {k: z[k] for k in z.files}
    if cfg.get("arch") not in ("static", "pico"):
        raise SystemExit("only static models (sparrow-micro / sparrow-nano) pack to SPB1")
    return cfg, vocab, arr


def deq(arr, k):
    if k + ".q8" in arr:
        return arr[k + ".q8"].astype(np.float32) * arr[k + ".scale"][:, None]
    return arr[k].astype(np.float32)


def int8_rows(arr, k):
    if k + ".q8" in arr:
        return arr[k + ".q8"], arr[k + ".scale"].astype(np.float32)
    return q8(arr[k].astype(np.float32))


def block_gains(model_path, cases):
    """1 / RMS of each feature block over sample questions. Folding these into w0 balances the
    blocks, so one int8 scale fits the whole feature vector on the int8 path."""
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "python"))
    from sparrow_decider import Decider, _options
    d = Decider.load(model_path)
    rows = []
    for state, q in cases:
        kind, opts = _options(q)
        rows.append(d.static.features(state, q.get("instructions"), kind, opts))
    f = np.concatenate(rows)
    D = d.static.emb.shape[1]
    rms = np.sqrt((f.reshape(len(f), -1, D) ** 2).mean((0, 2)))
    return (1.0 / np.maximum(rms, 1e-6)).astype(np.float32)


def pack(cfg, vocab, arr, gains=None) -> bytes:
    kv = bool(cfg.get("kv"))
    emb_q, emb_s = int8_rows(arr, "emb.weight")
    V, D = emb_q.shape
    w0q, w0s = int8_rows(arr, "mlp.0.weight")
    H, IN = w0q.shape
    NF = IN // D
    if gains is not None:
        w0 = deq(arr, "mlp.0.weight").reshape(H, NF, D) / np.asarray(gains, np.float32)[None, :, None]
        w0q, w0s = q8(w0.reshape(H, IN))
    w2q, w2s = int8_rows(arr, "mlp.2.weight")
    w4 = deq(arr, "mlp.4.weight").reshape(-1)
    temps = cfg.get("temperature_by_kind", {})
    out = io.BytesIO()

    def put(b: bytes):
        out.write(b)
        out.write(b"\0" * (-len(b) % 4))

    flags = int(kv) | (2 if gains is not None else 0)
    put(b"SPB1" + struct.pack("<7I", 1, flags, V, D, H, NF, int(cfg.get("max_len", 512))))
    put(struct.pack("<3fI", float(temps.get("noul", 1.0)), float(temps.get("choice", 1.0)),
                    float(temps.get("score", 1.0)), int(vocab["[UNK]"])))
    pieces = sorted(vocab.items(), key=lambda kv_: kv_[0].encode("utf-8"))
    strings, offs = bytearray(), []
    for p, _ in pieces:
        offs.append(len(strings))
        strings += p.encode("utf-8") + b"\0"
    put(struct.pack("<I", len(strings)) + bytes(strings))
    put(np.array(offs, "<u4").tobytes())
    put(np.array([i for _, i in pieces], "<u4").tobytes())
    put(emb_q.astype(np.int8).tobytes())
    put(emb_s.astype("<f4").tobytes())
    put(deq(arr, "kind.weight").astype("<f4").tobytes())
    if kv:
        put(deq(arr, "g.weight").astype("<f4").tobytes())
        put(arr["g.bias"].astype("<f4").tobytes())
        put(arr["tau"].astype("<f4").reshape(1).tobytes())
    if gains is not None:
        put(np.asarray(gains, "<f4").tobytes())
    put(w0q.astype(np.int8).tobytes())
    put(w0s.astype("<f4").tobytes())
    put(arr["mlp.0.bias"].astype("<f4").tobytes())
    put(w2q.astype(np.int8).tobytes())
    put(w2s.astype("<f4").tobytes())
    put(arr["mlp.2.bias"].astype("<f4").tobytes())
    put(w4.astype("<f4").tobytes())
    put(arr["mlp.4.bias"].astype("<f4").reshape(1).tobytes())
    return out.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--header", help="also write a C header with the blob as a const array")
    ap.add_argument("--symbol", default="sparrow_model_blob")
    ap.add_argument("--balance", action="store_true",
                    help="fold per-block gains into w0 (faster int8 path on microcontrollers)")
    a = ap.parse_args()
    gains = None
    if a.balance:
        import os
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cases = [(r["state"], r["question"]) for r in map(json.loads, open(os.path.join(root, "bench/robot/robotbench_v0.jsonl")))]
        cases += [(r["state"], r["question"]) for r in map(json.loads, open(os.path.join(root, "bench/massive/massive_intent.jsonl")))][:200]
        gains = block_gains(a.model, cases)
        print("block gains:", np.round(gains, 2).tolist())
    blob = pack(*load(a.model), gains=gains)
    open(a.out, "wb").write(blob)
    print(f"{a.out}: {len(blob) / 1e6:.3f} MB")
    if a.header:
        with open(a.header, "w") as f:
            f.write(f"/* generated by c/tools/pack.py from {a.model.split('/')[-1]} */\n#pragma once\n"
                    f"#include <stdint.h>\n#include <stddef.h>\n\n"
                    f"static const uint8_t {a.symbol}[{len(blob)}] __attribute__((aligned(4))) = {{\n")
            for i in range(0, len(blob), 24):
                f.write("  " + ",".join(str(x) for x in blob[i:i + 24]) + ",\n")
            f.write(f"}};\nstatic const size_t {a.symbol}_len = {len(blob)};\n")


if __name__ == "__main__":
    main()
