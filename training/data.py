"""Rows -> rendered decider prompts -> token tensors for a bidirectional encoder.

A row is the decider's training format: {kind, state, instructions, options:[[name, desc]],
label, weight, task}. Rendering matches strands_decider.prompting exactly, so a tiny model
reads the same text the 2B decider reads. Options are shuffled per epoch; `perm` records
the binding so targets follow their option.
"""
from __future__ import annotations

import json
import random
from typing import Any

NOUL_DEFAULT = {
    "false": "the statement does not hold for this state",
    "true": "the statement holds for this state",
}

HEADERS = {
    "noul": "Decide whether the statement is true of the state.",
    "choice": "Select exactly one option.",
    "score": "Rate the state against the ordered levels below (lowest first).",
}


def render_content(c: Any) -> str:
    if c is None:
        return ""
    if isinstance(c, str):
        return c.strip()
    return json.dumps(c, indent=2, ensure_ascii=False)


def render(kind: str, state: Any, instructions: str, options: list[tuple[str, str]]):
    """-> (state_text, question_text, option char spans within question_text)."""
    lines, spans, cur = [], [], 0
    for i, (name, desc) in enumerate(options):
        desc = " ".join((desc or "").split())
        line = f"{i + 1}. {name}" + (f" — {desc}" if desc else "")
        lines.append(line)
        spans.append((cur, cur + len(line)))
        cur += len(line) + 1
    prefix = f'<question type="{kind}">\n{HEADERS[kind]}\n{render_content(instructions)}\n<options>\n'
    q = prefix + "\n".join(lines) + "\n</options>\n</question>\n<answer>"
    base = len(prefix)
    return (f"<state>\n{render_content(state)}\n</state>\n", q,
            [(base + s, base + e) for s, e in spans])


_PRUNE = {}


def set_prune(tok, keep_ids):
    """Make encode() emit the pruned vocabulary's tokenization: every token outside
    keep_ids is replaced by its BPE parents, recursively (the runtime does the same)."""
    import json as _j
    from huggingface_hub import hf_hub_download
    tj = _j.load(open(hf_hub_download(tok.name_or_path, "tokenizer.json")))
    vocab = tj["model"]["vocab"]
    parents = {}
    for m in tj["model"]["merges"]:
        a, b = m.split(" ") if isinstance(m, str) else m
        parents.setdefault(a + b, (a, b))
    keep = set(keep_ids)
    memo = {}

    def dec(piece):
        if piece in memo:
            return memo[piece]
        i = vocab.get(piece)
        if i is not None and i in keep:
            out = [i]
        elif piece in parents:
            a, b = parents[piece]
            out = dec(a) + dec(b)
        else:
            out = [vocab[c] for c in piece if c in vocab]
        memo[piece] = out
        return out

    id2p = {i: p for p, i in vocab.items()}
    _PRUNE.clear()
    for i, p in id2p.items():
        if i not in keep:
            _PRUNE[i] = dec(p)


def _pruned(ids, offs=None):
    if not _PRUNE:
        return ids, offs
    oi, oo = [], []
    for k, i in enumerate(ids):
        rep = _PRUNE.get(i)
        if rep is None:
            oi.append(i)
            if offs is not None:
                oo.append(offs[k])
        else:
            oi.extend(rep)
            if offs is not None:
                oo.extend([offs[k]] * len(rep))
    return oi, (oo if offs is not None else None)


def encode(tok, kind, state, instructions, options, max_len: int):
    """Token ids for [CLS] state question [SEP], the state truncated (head+tail) to fit.

    Returns ids, option token spans [(start, end)) and the index range of `<answer>`."""
    st, q, spans = render(kind, state, instructions, options)
    qe = tok(q, add_special_tokens=False, return_offsets_mapping=True)
    qids, offs = _pruned(qe["input_ids"], qe["offset_mapping"])
    sids, _ = _pruned(tok(st, add_special_tokens=False)["input_ids"])
    budget = max_len - len(qids) - 2
    if budget < 8:  # question alone is too long: keep the tail of it (options + answer)
        qids, offs = qids[-(max_len - 10):], offs[-(max_len - 10):]
        budget = 8
    if len(sids) > budget:
        h = budget // 2
        sids = sids[:h] + sids[len(sids) - (budget - h):]
    base = 1 + len(sids)
    ids = [tok.cls_token_id] + sids + qids + [tok.sep_token_id]
    ospans = []
    for s, e in spans:
        toks = [i for i, (a, b) in enumerate(offs) if b > s and a < e]
        if not toks:
            toks = [len(qids) - 1]
        ospans.append((base + toks[0], base + toks[-1] + 1))
    ans = (base + len(qids) - 3, base + len(qids))  # last few tokens: "<answer>"
    return ids, ospans, ans, base


def load_rows(paths: list[str], limit: int | None = None) -> list[dict]:
    rows = []
    for p in paths:
        with open(p) as f:
            for i, line in enumerate(f):
                r = json.loads(line)
                if r.get("kind") in HEADERS and r.get("options"):
                    r["_i"] = i
                    r["_f"] = p
                    rows.append(r)
    if limit:
        random.Random(0).shuffle(rows)
        rows = rows[:limit]
    return rows


def target(r: dict, smoothing: float = 0.1) -> list[float]:
    """Soft target in the row's own option order: teacher probs if present, else gold
    one-hot (score: `smoothing` spread to adjacent levels, as the decider trains)."""
    n = len(r["options"])
    t = [0.0] * n
    y = int(r["label"])
    if r["kind"] == "score" and smoothing:
        nb = [j for j in (y - 1, y + 1) if 0 <= j < n]
        t[y] = 1 - smoothing
        for j in nb:
            t[j] = smoothing / len(nb)
    else:
        t[y] = 1.0
    if r.get("teacher") is not None and len(r["teacher"]) == n:
        a = r.get("alpha", 0.5)
        t = [a * p + (1 - a) * g for p, g in zip(r["teacher"], t)]
    return t
