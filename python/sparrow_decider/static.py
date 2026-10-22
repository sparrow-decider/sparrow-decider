"""Static (Model2Vec-style) embeddings and a small MLP. No attention, so a question costs well
under a millisecond. Used by sparrow-micro and sparrow-nano.

The state, the question and each option are mean-pooled separately; an MLP scores every option
from element-wise products of those vectors plus a set-level contrast term.

With `kv` on (sparrow-nano and later), numbers in the state are read as key-value pairs
(`battery: 6%`, `dirt_level=34`). Each pair becomes emb(key) * g(value), where g is a small learned
map of the number, so the model can tell a low battery from a near obstacle. Each option also
attends over the pairs by similarity to the line they sit on, which binds "zone_b" to its value.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

import numpy as np

from .engine import gelu, softmax
from .wordpiece import WordPiece

KINDS = {"noul": 0, "choice": 1, "score": 2}
MAX_PAIRS = 16
# key [:=] number [%]; the key may be preceded on the line by a label ("zone_a: dirt_level=34")
_KV = re.compile(r"([A-Za-z][A-Za-z0-9_ .\-]{0,40}?)\s*[:=]\s*(-?\d+(?:\.\d+)?)\s*(%?)")


def _content(c: Any) -> str:
    if c is None:
        return ""
    if isinstance(c, str):
        return c.strip()
    return json.dumps(c, indent=2, ensure_ascii=False)


def kv_pairs(text: str, max_pairs: int = MAX_PAIRS) -> list[tuple[str, str, float]]:
    """-> [(key, line label, value)]. The label is the text before the first ':' of the line when
    that differs from the key, else the key itself."""
    out = []
    for line in text.splitlines():
        head = line.split(":", 1)[0].strip()
        for m in _KV.finditer(line):
            key = m.group(1).strip()
            out.append((key, head if head and head != key else key, float(m.group(2))))
            if len(out) >= max_pairs:
                return out
    return out


def value_features(v: float) -> list[float]:
    """Fixed numeric features of one value; g() is a learned linear map + tanh over these."""
    a = abs(v)
    return [max(-1.0, min(1.0, v / 100.0)), math.copysign(math.log1p(a), v) / 5.0,
            1.0 if 0 < a < 1 else 0.0, max(-1.0, min(1.0, v / 10.0))]


N_VF = 4


class StaticModel:
    def __init__(self, cfg: dict, w: dict[str, np.ndarray], vocab: dict[str, int]):
        self.cfg, self.w = cfg, w
        self.tok = WordPiece(vocab)
        self.emb = w["emb.weight"]
        self.kv = bool(cfg.get("kv"))
        self.max_len = int(cfg.get("max_len", 512))

    def _pool(self, text: str) -> np.ndarray:
        ids = self.tok.encode(text, self.max_len) or [0]
        return self.emb[ids].mean(0)

    @staticmethod
    def _n(z):
        return z / np.maximum(np.linalg.norm(z, axis=-1, keepdims=True), 1e-12)

    def _kv(self, state: str, o: np.ndarray):
        """-> (kv mean vector H, per-option bound vectors K x H)."""
        H = o.shape[-1]
        pairs = kv_pairs(state)
        if not pairs:
            return np.zeros(H, np.float32), np.zeros_like(o)
        w = self.w
        ek = self._n(np.stack([self._pool(k) for k, _, _ in pairs]))
        el = self._n(np.stack([self._pool(lb) for _, lb, _ in pairs]))
        g = np.tanh(np.array([value_features(v) for _, _, v in pairs], np.float32) @ w["g.weight"].T + w["g.bias"])
        pv = ek * g  # P x H
        att = softmax(float(w["tau"][0]) * (o @ el.T), -1)  # K x P
        return pv.mean(0), att @ pv

    def logits(self, state: Any, instructions: Any, kind: str, opts: list[tuple[str, str]]) -> np.ndarray:
        w = self.w
        st = _content(state)
        s = self._pool(st)
        q = self._pool(_content(instructions)) + w["kind.weight"][KINDS[kind]]
        o = np.stack([self._pool(f"{n} {d or ''}") for n, d in opts])
        s, q, o = self._n(s), self._n(q), self._n(o)
        om = o.mean(0, keepdims=True)
        feats = [o, s * o, q * o, s * q * o, o - om, (s - om) * o]
        if self.kv:
            kv, kvo = self._kv(st, o)
            feats += [kv * o, kv * q * o, kvo, kvo * q]
        f = np.concatenate([np.broadcast_to(x, o.shape) for x in feats], -1)
        h = gelu(f @ w["mlp.0.weight"].T + w["mlp.0.bias"])
        h = gelu(h @ w["mlp.2.weight"].T + w["mlp.2.bias"])
        return (h @ w["mlp.4.weight"].T + w["mlp.4.bias"])[:, 0]

    def probs(self, state, instructions, kind, opts) -> np.ndarray:
        t = float(self.cfg.get("temperature_by_kind", {}).get(kind, 1.0))
        return softmax(self.logits(state, instructions, kind, opts) / t)
