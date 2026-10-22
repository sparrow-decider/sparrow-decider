"""BERT uncased WordPiece in pure Python (BertNormalizer + BertPreTokenizer + WordPiece)."""
from __future__ import annotations

import unicodedata
from functools import lru_cache


def _is_punct(ch: str) -> bool:
    cp = ord(ch)
    if 33 <= cp <= 47 or 58 <= cp <= 64 or 91 <= cp <= 96 or 123 <= cp <= 126:
        return True
    return unicodedata.category(ch).startswith("P")


def _is_cjk(cp: int) -> bool:
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0x20000 <= cp <= 0x2A6DF or 0x2A700 <= cp <= 0x2B73F
            or 0x2B740 <= cp <= 0x2B81F or 0x2B820 <= cp <= 0x2CEAF or 0xF900 <= cp <= 0xFAFF or 0x2F800 <= cp <= 0x2FA1F)


class WordPiece:
    def __init__(self, vocab: dict[str, int], unk: str = "[UNK]", max_chars: int = 100):
        self.vocab, self.unk_id, self.max_chars = vocab, vocab[unk], max_chars
        self._word = lru_cache(maxsize=65536)(self._wp)

    @staticmethod
    def normalize(text: str) -> str:
        out = []
        for ch in text:
            cp = ord(ch)
            if cp == 0 or cp == 0xFFFD or (unicodedata.category(ch).startswith("C") and ch not in "\t\n\r"):
                continue
            if ch in "\t\n\r" or unicodedata.category(ch) == "Zs":
                out.append(" ")
            elif _is_cjk(cp):
                out.append(f" {ch} ")
            else:
                out.append(ch)
        text = "".join(out).lower()
        text = unicodedata.normalize("NFD", text)
        return "".join(c for c in text if unicodedata.category(c) != "Mn")

    @staticmethod
    def pretokenize(text: str) -> list[str]:
        words, cur = [], []
        for ch in text:
            if ch.isspace():
                if cur:
                    words.append("".join(cur))
                    cur = []
            elif _is_punct(ch):
                if cur:
                    words.append("".join(cur))
                    cur = []
                words.append(ch)
            else:
                cur.append(ch)
        if cur:
            words.append("".join(cur))
        return words

    def _wp(self, word: str) -> tuple[int, ...]:
        if len(word) > self.max_chars:
            return (self.unk_id,)
        out, start = [], 0
        while start < len(word):
            end = len(word)
            cur = None
            while start < end:
                sub = word[start:end] if start == 0 else "##" + word[start:end]
                if sub in self.vocab:
                    cur = self.vocab[sub]
                    break
                end -= 1
            if cur is None:
                return (self.unk_id,)
            out.append(cur)
            start = end
        return tuple(out)

    def encode(self, text: str, max_len: int = 512) -> list[int]:
        ids: list[int] = []
        for w in self.pretokenize(self.normalize(text)):
            ids.extend(self._word(w))
            if len(ids) >= max_len:
                break
        return ids[:max_len]
