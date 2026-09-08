"""Tokenizer — a compact BPE over the task corpus.

The tokenizer is an explicit experimental variable (spec section 22). For a small
model the embedding matrix can dominate, so we prefer a compact vocabulary.
"""
import json
import os


class Tokenizer:
    """Small byte-level-ish BPE wrapper (built from the task corpus)."""

    def __init__(self, vocab, merges_special=("def ", "solve", "(", ")", ":", "\n", "    ")):
        self.vocab = vocab  # list of token strings, index = id
        self.stoi = {t: i for i, t in enumerate(vocab)}
        self.itos = vocab
        self.merge_tokens = merges_special

    @property
    def vocab_size(self):
        return len(self.vocab)

    def encode(self, text):
        # Greedy longest-match over the vocabulary (simple, deterministic).
        toks = []
        i = 0
        while i < len(text):
            best = None
            for k in range(min(24, len(text) - i), 0, -1):
                cand = text[i:i + k]
                if cand in self.stoi:
                    best = cand
                    break
            if best is None:
                best = text[i]
                i += 1
            else:
                i += len(best)
            toks.append(self.stoi.get(best, self.stoi.get("<unk>", 0)))
        return toks

    def decode(self, ids):
        return "".join(self.itos[i] for i in ids if 0 <= i < len(self.itos))


def train_tokenizer(texts, min_vocab=128, max_vocab=512, save_path=None):
    """Build a vocabulary from the corpus.

    Strategy: byte alphabet + the most frequent whitespace-aware n-grams up to
    `max_vocab`. Deterministic. Returns a Tokenizer.
    """
    from collections import Counter
    # Start from a byte alphabet (so nothing is out-of-vocab).
    vocab = {chr(c) for c in range(256)}
    # Add common short tokens (whitespace-joined words) that appear often.
    words = Counter()
    for t in texts:
        for w in t.split():
            words[w] += 1
    # add the most frequent words + common punctuation tokens
    for w, _ in words.most_common(max_vocab - len(vocab)):
        vocab.add(w)
    vocab = sorted(vocab)[:max_vocab]
    tok = Tokenizer(vocab)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            json.dump({"vocab": vocab}, f)
    return tok


def load_tokenizer(path):
    with open(path) as f:
        data = json.load(f)
    return Tokenizer(data["vocab"])
