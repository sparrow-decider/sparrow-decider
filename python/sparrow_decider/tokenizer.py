"""Byte-level BPE (GPT-2/OLMo style) in pure Python, with a pruned vocabulary.

The model keeps only the tokens its training corpus used. Text is tokenized with the full
merge list, and any token that was pruned is split back into the two tokens it was merged
from, recursively, until every piece is kept. Byte tokens are always kept, so nothing is
ever unknown.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

try:  # `regex` gives the exact \p{L}/\p{N} classes; `re` is a close fallback
    import regex as _re

    _PAT = _re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""")
except ImportError:  # pragma: no cover
    _re = re
    _PAT = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[^\W\d_]+| ?\d+| ?(?:[^\s\w]|_)+|\s+(?!\S)|\s+""")


def _bytes_to_unicode() -> dict[int, str]:
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, map(chr, cs)))


_B2U = _bytes_to_unicode()


class BPETokenizer:
    def __init__(self, vocab: dict[str, int], merges: list[str], added: dict[str, int],
                 keep: dict[int, int], cls_id: int, sep_id: int, pad_id: int):
        """vocab/merges/added are the full original tokenizer; keep maps original id ->
        pruned id. cls/sep/pad are pruned ids."""
        self.vocab = vocab
        self.ranks = {tuple(m.split(" ")): i for i, m in enumerate(merges)}
        self.parents = {}
        for a, b in self.ranks:
            self.parents.setdefault(a + b, (a, b))
        self.keep = keep
        self.cls_id, self.sep_id, self.pad_id = cls_id, sep_id, pad_id
        self.added = {k: v for k, v in added.items() if v in keep}
        if self.added:
            alts = sorted(self.added, key=len, reverse=True)
            self._added_re = re.compile("(" + "|".join(map(re.escape, alts)) + ")")
        else:
            self._added_re = None
        self._bpe = lru_cache(maxsize=65536)(self._bpe_word)

    def _bpe_word(self, word: str) -> tuple[int, ...]:
        parts = list(word)
        while len(parts) > 1:
            best, bi = None, -1
            for i in range(len(parts) - 1):
                r = self.ranks.get((parts[i], parts[i + 1]))
                if r is not None and (best is None or r < best):
                    best, bi = r, i
            if best is None:
                break
            parts[bi:bi + 2] = [parts[bi] + parts[bi + 1]]
        out: list[int] = []
        for p in parts:
            self._emit(p, out)
        return tuple(out)

    def _emit(self, piece: str, out: list[int]) -> None:
        oid = self.vocab.get(piece)
        if oid is not None and oid in self.keep:
            out.append(self.keep[oid])
        elif piece in self.parents:
            a, b = self.parents[piece]
            self._emit(a, out)
            self._emit(b, out)
        else:  # single byte char missing from keep: should not happen
            for ch in piece:
                oid = self.vocab.get(ch)
                if oid is not None and oid in self.keep:
                    out.append(self.keep[oid])

    def encode(self, text: str) -> list[int]:
        text = unicodedata.normalize("NFC", text)
        out: list[int] = []
        chunks = self._added_re.split(text) if self._added_re else [text]
        for i, chunk in enumerate(chunks):
            if not chunk:
                continue
            if i % 2 == 1:
                out.append(self.keep[self.added[chunk]])
                continue
            for w in _PAT.findall(chunk):
                out.extend(self._bpe("".join(_B2U[b] for b in w.encode("utf-8"))))
        return out

    def encode_with_offsets(self, text: str) -> tuple[list[int], list[tuple[int, int]]]:
        """Token ids with approximate character offsets (per pre-token word); enough to
        locate option lines, which always begin and end on word boundaries."""
        text = unicodedata.normalize("NFC", text)
        ids: list[int] = []
        offs: list[tuple[int, int]] = []
        pos = 0
        chunks = self._added_re.split(text) if self._added_re else [text]
        for i, chunk in enumerate(chunks):
            if not chunk:
                continue
            if i % 2 == 1:
                ids.append(self.keep[self.added[chunk]])
                offs.append((pos, pos + len(chunk)))
                pos += len(chunk)
                continue
            for m in _PAT.finditer(chunk):
                w = m.group(0)
                toks = self._bpe("".join(_B2U[b] for b in w.encode("utf-8")))
                s, e = pos + m.start(), pos + m.end()
                ids.extend(toks)
                offs.extend([(s, e)] * len(toks))
            pos += len(chunk)
        return ids, offs
