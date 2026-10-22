"""ModernBERT encoder + pointer head in numpy. No torch, no onnxruntime.

Weights are int8 with one fp32 scale per output row (symmetric), dequantised once at load
into fp32 (small models: a few tens of MB of RAM), or kept fp16/fp32 if exported so.
"""
from __future__ import annotations

import math

import numpy as np


def _erf(x: np.ndarray) -> np.ndarray:
    # Abramowitz & Stegun 7.1.26 has 1.5e-7 abs error; exact-GELU models tolerate it.
    s = np.sign(x)
    a = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-a * a)
    return s * y


def gelu(x: np.ndarray) -> np.ndarray:
    return 0.5 * x * (1.0 + _erf(x / math.sqrt(2.0)))


def layer_norm(x: np.ndarray, w: np.ndarray, b: np.ndarray | None = None, eps: float = 1e-5) -> np.ndarray:
    mu = x.mean(-1, keepdims=True)
    var = ((x - mu) ** 2).mean(-1, keepdims=True)
    y = (x - mu) / np.sqrt(var + eps) * w
    return y + b if b is not None else y


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis, keepdims=True)


class Encoder:
    """cfg: hidden, layers, heads, window (local attention width), theta, global_every.
    w: dict of fp32 arrays named as the torch state dict (encoder.* stripped)."""

    def __init__(self, cfg: dict, w: dict[str, np.ndarray]):
        self.cfg, self.w = cfg, w
        self.hd = cfg["hidden"] // cfg["heads"]
        inv = 1.0 / (cfg["theta"] ** (np.arange(0, self.hd, 2, dtype=np.float64) / self.hd))
        self._inv = inv.astype(np.float32)

    def _rope(self, T: int):
        f = np.outer(np.arange(T, dtype=np.float32), self._inv)
        emb = np.concatenate([f, f], -1)
        return np.cos(emb), np.sin(emb)

    @staticmethod
    def _rot(x):
        h = x.shape[-1] // 2
        return np.concatenate([-x[..., h:], x[..., :h]], -1)

    def __call__(self, ids: np.ndarray) -> np.ndarray:
        """ids: (T,) int -> hidden (T, H)."""
        c, w = self.cfg, self.w
        T = len(ids)
        x = w["embeddings.tok_embeddings.weight"][ids]
        x = layer_norm(x, w["embeddings.norm.weight"])
        cos, sin = self._rope(T)
        pos = np.arange(T)
        local = np.abs(pos[:, None] - pos[None, :]) > c["window"] // 2
        H, nh, hd = c["hidden"], c["heads"], self.hd
        for i in range(c["layers"]):
            p = f"layers.{i}."
            h = x if i == 0 else layer_norm(x, w[p + "attn_norm.weight"])
            qkv = (h @ w[p + "attn.Wqkv.weight"].T).reshape(T, 3, nh, hd).transpose(1, 2, 0, 3)
            q, k, v = qkv[0], qkv[1], qkv[2]
            q = q * cos + self._rot(q) * sin
            k = k * cos + self._rot(k) * sin
            s = (q @ k.transpose(0, 2, 1)) / math.sqrt(hd)
            if i % c["global_every"] != 0:
                s = np.where(local[None], -1e9, s)
            a = softmax(s) @ v
            x = x + a.transpose(1, 0, 2).reshape(T, H) @ w[p + "attn.Wo.weight"].T
            h = layer_norm(x, w[p + "mlp_norm.weight"])
            inp, gate = np.split(h @ w[p + "mlp.Wi.weight"].T, 2, -1)
            x = x + (gelu(inp) * gate) @ w[p + "mlp.Wo.weight"].T
        return layer_norm(x, w["final_norm.weight"])


class PointerHead:
    def __init__(self, w: dict[str, np.ndarray]):
        self.w = w

    def __call__(self, hq: np.ndarray, hk: np.ndarray) -> np.ndarray:
        w = self.w
        ln = lambda z: layer_norm(z, w["ln.weight"], w["ln.bias"])  # noqa: E731
        q = ln(hq) @ w["q.weight"].T + w["q.bias"]
        k = ln(hk) @ w["k.weight"].T + w["k.bias"]
        return (k @ q) / math.sqrt(q.shape[-1])
