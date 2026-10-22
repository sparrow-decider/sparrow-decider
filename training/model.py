"""Encoder + pointer head: one forward pass scores every option.

query = mean hidden over the `<answer>` tokens, key_k = mean hidden over option k's line.
logit_k = <Wq LN(q), Wk LN(key_k)> / sqrt(d). With bidirectional attention each option
line has already read the state, the question and the other options.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn
from transformers import AutoModel


class PointerHead(nn.Module):
    def __init__(self, hidden: int, d: int = 128):
        super().__init__()
        self.ln = nn.LayerNorm(hidden)
        self.q = nn.Linear(hidden, d)
        self.k = nn.Linear(hidden, d)
        self.d = d

    def forward(self, hq, hk, omask):
        q = self.q(self.ln(hq))                      # B,d
        k = self.k(self.ln(hk))                      # B,K,d
        logits = torch.einsum("bd,bkd->bk", q, k) / math.sqrt(self.d)
        return logits.masked_fill(~omask, -1e4)


def span_mean(h, spans):
    """h B,T,H ; spans B,K,2 (start,end) -> B,K,H mean over [start,end)."""
    T = h.shape[1]
    ar = torch.arange(T, device=h.device)
    m = (ar[None, None, :] >= spans[..., :1]) & (ar[None, None, :] < spans[..., 1:])
    m = m.float()
    return torch.einsum("bkt,bth->bkh", m, h) / m.sum(-1, keepdim=True).clamp(min=1)


class TinyDecider(nn.Module):
    def __init__(self, encoder_name: str, d: int = 128, layers: str | None = None):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(encoder_name)
        if layers:  # layer dropping: keep a subset (re-indexed), e.g. "0,3,6"
            keep = [int(x) for x in str(layers).split(",")]
            self.encoder.layers = nn.ModuleList([self.encoder.layers[i] for i in keep])
            lt = [self.encoder.config.layer_types[i] for i in keep]
            self.encoder.config.layer_types = lt
            self.encoder.config.num_hidden_layers = len(keep)
            for j, layer in enumerate(self.encoder.layers):
                layer.layer_idx = j
                if hasattr(layer, "attn"):
                    layer.attn.layer_idx = j
        self.head = PointerHead(self.encoder.config.hidden_size, d)

    def forward(self, ids, attn, ospans, omask, ans, **_):
        h = self.encoder(input_ids=ids, attention_mask=attn).last_hidden_state
        hq = span_mean(h, ans[:, None, :])[:, 0]
        hk = span_mean(h, ospans)
        return self.head(hq, hk, omask)


class StaticDecider(nn.Module):
    """No attention: weighted bags of token embeddings for the state, the question and each
    option, compared by a small MLP. Sub-millisecond on CPU."""

    def __init__(self, encoder_name: str, d: int = 256):
        super().__init__()
        enc = AutoModel.from_pretrained(encoder_name)
        e = enc.embeddings.tok_embeddings.weight.detach().clone()
        self.emb = nn.Embedding.from_pretrained(e, freeze=False)
        self.tw = nn.Embedding(e.shape[0], 1)
        nn.init.zeros_(self.tw.weight)
        H = e.shape[1]
        self.proj = nn.Linear(H, H)
        self.mlp = nn.Sequential(nn.Linear(5 * H, d), nn.GELU(), nn.Linear(d, d), nn.GELU(), nn.Linear(d, 1))

    def _pool(self, x, w, spans):
        T = x.shape[1]
        ar = torch.arange(T, device=x.device)
        m = ((ar[None, None, :] >= spans[..., :1]) & (ar[None, None, :] < spans[..., 1:])).float() * w[:, None, :]
        return torch.einsum("bkt,bth->bkh", m, x) / m.sum(-1, keepdim=True).clamp(min=1e-6)

    def forward(self, ids, attn, ospans, omask, ans, qs, **_):
        x = self.proj(self.emb(ids))
        w = torch.nn.functional.softplus(self.tw(ids).squeeze(-1) + 1.0) * attn
        B = ids.shape[0]
        one = torch.ones(B, dtype=torch.long, device=ids.device)
        s = self._pool(x, w, torch.stack([one, qs], -1)[:, None])[:, 0]
        q = self._pool(x, w, torch.stack([qs, ospans[:, 0, 0]], -1)[:, None])[:, 0]
        o = self._pool(x, w, ospans)
        om = omask.float()[..., None]
        omean = (o * om).sum(1, keepdim=True) / om.sum(1, keepdim=True)
        s_, q_ = s[:, None].expand_as(o), q[:, None].expand_as(o)
        f = torch.cat([o, s_ * o, q_ * o, s_ * q_ * o, o - omean], -1)
        return self.mlp(f).squeeze(-1).masked_fill(~omask, -1e4)


def build_model(arch: str, encoder_name: str, d: int = 128, layers: str | None = None) -> nn.Module:
    if arch == "static":
        return StaticDecider(encoder_name, max(d, 256))
    return TinyDecider(encoder_name, d, layers)
