"""sparrow_decider: few-MB decision models for agents. numpy only.

    from sparrow_decider import Decider
    d = Decider.load()                       # bundled default model
    d.ask("User: I was charged twice", {
        "refund": {"type": "noul", "instructions": "Is the user asking for money back?"},
        "intent": {"type": "choice", "instructions": "Primary intent?",
                   "criteria": {"billing": "charges, invoices", "bug": "broken feature"}},
        "urgency": {"type": "score", "instructions": "How urgent?",
                    "criteria": ["not urgent", "soon", "now"]},
    })

The request and answer shapes follow Strands Decider's /v1/systemone contract.
"""
from __future__ import annotations

import io
import json
import os
import zipfile
from typing import Any

import numpy as np

from .engine import Encoder, PointerHead, softmax
from .static import StaticModel
from .tokenizer import BPETokenizer

__version__ = "0.2.0"
__all__ = ["Decider", "available_models", "__version__"]

HEADERS = {
    "noul": "Decide whether the statement is true of the state.",
    "choice": "Select exactly one option.",
    "score": "Rate the state against the ordered levels below (lowest first).",
}
NOUL_DEFAULT = {
    "false": "the statement does not hold for this state",
    "true": "the statement holds for this state",
}
_HERE = os.path.dirname(__file__)
DEFAULT_MODEL = "sparrow-nano-general-v1.1"


def _search_dirs() -> list[str]:
    extra = os.environ.get("SPARROW_MODELS", os.path.expanduser("~/.cache/sparrow-decider"))
    return [os.path.join(_HERE, "models")] + [d for d in extra.split(os.pathsep) if d]


def available_models() -> list[str]:
    """Names of the models that Decider.load() can find without a path."""
    out = set()
    for d in _search_dirs():
        if os.path.isdir(d):
            out.update(f[:-8] for f in os.listdir(d) if f.endswith(".sparrow"))
    return sorted(out)


def _resolve(name: str | None) -> str:
    name = name or DEFAULT_MODEL
    if os.path.isfile(name):
        return name
    key = name.removesuffix(".sparrow")
    key = key if key.startswith("sparrow-") else f"sparrow-{key}"
    for d in _search_dirs():
        if not os.path.isdir(d):
            continue
        hits = sorted(f for f in os.listdir(d) if f.endswith(".sparrow") and f[:-8].startswith(key))
        if hits:
            return os.path.join(d, hits[-1])  # newest version wins
    raise FileNotFoundError(f"no model {name!r}; available: {', '.join(available_models()) or 'none'}. "
                            "Download more from the GitHub releases into ~/.cache/sparrow-decider.")


def _content(c: Any) -> str:
    if c is None:
        return ""
    if isinstance(c, str):
        return c.strip()
    return json.dumps(c, indent=2, ensure_ascii=False)


def _options(q: dict) -> tuple[str, list[tuple[str, str]]]:
    kind = q.get("type", "noul")
    crit = q.get("criteria")
    if kind == "noul":
        c = {**NOUL_DEFAULT, **(crit or {})}
        return kind, [("false", _content(c["false"])), ("true", _content(c["true"]))]
    if kind == "choice":
        if not isinstance(crit, dict) or len(crit) < 2:
            raise ValueError("a choice question needs criteria: {name: description}, at least 2")
        return kind, [(str(k), _content(v)) for k, v in crit.items()]
    if kind == "score":
        if not isinstance(crit, list) or not 2 <= len(crit) <= 10:
            raise ValueError("a score question needs criteria: a list of 2-10 levels, lowest first")
        return kind, [(str(i), _content(v)) for i, v in enumerate(crit)]
    raise ValueError(f"unknown question type {kind!r}")


_LAZY = ("encoder.embeddings.tok_embeddings.weight", "emb.weight")


def _dequant(z: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    out = {}
    for k, v in z.items():
        if k.endswith(".q8") and k[:-3] in _LAZY:  # embedding tables stay int8; rows dequantised on lookup
            out[k[:-3]] = _Q8Rows(v, z[k[:-3] + ".scale"])
        elif k.endswith(".q8"):
            f = v.astype(np.float32)
            f *= z[k[:-3] + ".scale"][:, None]
            out[k[:-3]] = f
        elif k.endswith(".scale"):
            continue
        else:
            out[k] = v.astype(np.float32)
    return out


class _Q8Rows:
    """An int8 row table that dequantises only the rows indexed."""

    def __init__(self, q: np.ndarray, scale: np.ndarray):
        self.q, self.scale = q, scale
        self.shape = q.shape

    def __getitem__(self, ids):
        return self.q[ids].astype(np.float32) * self.scale[ids][..., None]


class Decider:
    def __init__(self, cfg: dict, weights: dict[str, np.ndarray], tok: BPETokenizer | None = None,
                 static_vocab: dict[str, int] | None = None):
        self.cfg = cfg
        self.tok = tok
        self.name = cfg.get("name", "sparrow_decider")
        self.temps = cfg.get("temperature_by_kind", {})
        self.static = StaticModel(cfg, weights, static_vocab) if cfg.get("arch") in ("static", "pico") else None
        if self.static:
            return
        enc = {k[8:]: v for k, v in weights.items() if k.startswith("encoder.")}
        head = {k[5:]: v for k, v in weights.items() if k.startswith("head.")}
        self.encoder = Encoder(cfg["encoder"], enc)
        self.head = PointerHead(head)
        self.max_len = cfg.get("max_len", 512)

    # ---- loading ------------------------------------------------------------------------
    @classmethod
    def load(cls, path: str | None = None) -> "Decider":
        """Load a model by file path or by name.

        Decider.load()                              # bundled sparrow-nano-general-v1.1
        Decider.load("nano-robot")                  # bundled sparrow-nano-robot-v1.1
        Decider.load("sparrow-micro-general-v1.1")  # looked up in the bundled models, then $SPARROW_MODELS
        Decider.load("path/to/model.sparrow")
        """
        path = _resolve(path)
        with zipfile.ZipFile(path) as zf:
            cfg = json.loads(zf.read("config.json"))
            tk = json.loads(zf.read("tokenizer.json"))
            raw = zf.read("model.npz")
            with np.load(io.BytesIO(raw)) as z:
                weights = _dequant({k: z[k] for k in z.files})
            del raw
        if cfg.get("arch") in ("static", "pico"):
            return cls(cfg, weights, static_vocab=tk["vocab"])
        pieces = tk["pieces"]
        keep = {i: i for i in range(len(pieces))}
        vocab = {p: i for i, p in enumerate(pieces)}
        added = {p: vocab[p] for p in tk["added"]}
        tok = BPETokenizer(vocab, tk["merges"], added, keep, vocab["[CLS]"], vocab["[SEP]"], vocab["[PAD]"])
        return cls(cfg, weights, tok)

    # ---- one question -------------------------------------------------------------------
    def _encode(self, state: Any, instructions: Any, kind: str, opts: list[tuple[str, str]]):
        lines, spans, cur = [], [], 0
        for i, (name, desc) in enumerate(opts):
            desc = " ".join((desc or "").split())
            line = f"{i + 1}. {name}" + (f" — {desc}" if desc else "")
            lines.append(line)
            spans.append((cur, cur + len(line)))
            cur += len(line) + 1
        prefix = f'<question type="{kind}">\n{HEADERS[kind]}\n{_content(instructions)}\n<options>\n'
        q = prefix + "\n".join(lines) + "\n</options>\n</question>\n<answer>"
        base = len(prefix)
        qids, offs = self.tok.encode_with_offsets(q)
        sids = self.tok.encode(f"<state>\n{_content(state)}\n</state>\n")
        budget = self.max_len - len(qids) - 2
        if budget < 8:
            qids, offs = qids[-(self.max_len - 10):], offs[-(self.max_len - 10):]
            budget = 8
        if len(sids) > budget:
            h = budget // 2
            sids = sids[:h] + sids[len(sids) - (budget - h):]
        b0 = 1 + len(sids)
        ids = [self.tok.cls_id] + sids + qids + [self.tok.sep_id]
        ospans = []
        for s, e in spans:
            s, e = s + base, e + base
            toks = [i for i, (a, b) in enumerate(offs) if b > s and a < e]
            ospans.append((b0 + toks[0], b0 + toks[-1] + 1) if toks else (b0 + len(qids) - 1, b0 + len(qids)))
        return np.array(ids), ospans, (b0 + len(qids) - 3, b0 + len(qids))

    def probs(self, state: Any, question: dict) -> tuple[str, list[str], list[str], np.ndarray]:
        kind, opts = _options(question)
        if self.static:
            p = self.static.probs(state, question.get("instructions"), kind, opts)
            return kind, [n for n, _ in opts], [d for _, d in opts], p
        ids, ospans, ans = self._encode(state, question.get("instructions"), kind, opts)
        h = self.encoder(ids)
        hq = h[ans[0]:ans[1]].mean(0)
        hk = np.stack([h[a:b].mean(0) for a, b in ospans])
        logits = self.head(hq, hk) / float(self.temps.get(kind, 1.0))
        return kind, [n for n, _ in opts], [d for _, d in opts], softmax(logits)

    # ---- the /v1/systemone contract -----------------------------------------------------
    def ask(self, state: Any, questions: dict[str, dict]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name, q in questions.items():
            kind, names, descs, p = self.probs(state, q)
            if kind == "noul":
                out[name] = {"type": "noul", "noul": round(float(p[1]), 4)}
            elif kind == "choice":
                n = len(p)
                i = int(p.argmax())
                out[name] = {"type": "choice", "choice": names[i],
                             "probabilities": {k: round(float(x), 4) for k, x in zip(names, p)},
                             "confidence": round(float((n * p[i] - 1) / (n - 1)), 4)}
            else:
                lv = np.arange(len(p))
                ev = float((lv * p).sum())
                sd = float(np.sqrt((((lv - ev) ** 2) * p).sum()))
                out[name] = {"type": "score", "score": round(ev, 4),
                             "legend": dict(zip(names, descs)),
                             "probabilities": {k: round(float(x), 4) for k, x in zip(names, p)},
                             "confidence": round(1 - sd / ((len(p) - 1) / 2), 4)}
        return out

    def __call__(self, state: Any, questions: dict[str, dict]) -> dict[str, Any]:
        return self.ask(state, questions)
