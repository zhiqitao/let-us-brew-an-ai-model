#!/usr/bin/env python3
"""0.1M-parameter training smoke test (CPU).

Purpose: prove the training pipeline *works end-to-end* on this machine before
committing the book to any size. Covers, in one run:
  1. A tiny character-level dataset
  2. A minimal GPT-style transformer (~0.1M params) built only with torch
  3. Forward + backward + optimizer step, loss going DOWN
  4. A tiny generation sample from the trained weights

Not a real training run — a smoke test. This is the "proof the machine and the
pipeline are alive" step of the book.
"""
import math, time, torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(0)

# ---------- 1. Tiny dataset: a deterministic pseudo-text ----------
# 20 repeated "sentences" over a small alphabet -> learnable in seconds.
words = [b"the quick brown fox jumps over the lazy dog",
         b"pack my box with five dozen liquor jugs",
         b"how vexingly quick daft zebras jump",
         b"the five boxing wizards jump quickly",
         b"a wizard quick fox jumps over daft dog"]
text = b"\n".join(words * 40)  # repeat to give gradient signal

vocab = sorted(set(text))
stoi = {c: i for i, c in enumerate(vocab)}
itos = {i: c for i, c in enumerate(vocab)}
V = len(vocab)
print(f"vocab size: {V}  corpus chars: {len(text)}")

data = torch.tensor([stoi[c] for c in text], dtype=torch.long)
# train/val split
n = int(0.9 * len(data)); tr, va = data[:n], data[n:]

def get_batch(split, block_size, batch_size):
    d = tr if split == "train" else va
    ix = torch.randint(len(d) - block_size, (batch_size,))
    x = torch.stack([d[i:i+block_size] for i in ix])
    y = torch.stack([d[i+1:i+1+block_size] for i in ix])
    return x, y

# ---------- 2. Minimal GPT (nanoGPT-style), ~0.1M params ----------
class GPT(nn.Module):
    def __init__(self, V, n_embd=96, n_head=4, n_layer=4, block_size=64):
        super().__init__()
        self.block_size = block_size
        self.token_emb = nn.Embedding(V, n_embd)
        self.pos_emb = nn.Embedding(block_size, n_embd)
        self.blocks = nn.ModuleList([Block(n_embd, n_head) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, V)
        self.apply(self._init)
        print(f"params: {sum(p.numel() for p in self.parameters()):,}")

    def _init(self, m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, std=0.02)
            if m.bias is not None: nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok = self.token_emb(idx)
        pos = self.pos_emb(torch.arange(T))
        x = tok + pos
        for b in self.blocks:
            x = b(x)
        x = self.ln_f(x)
        logits = self.head(x)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, V), targets.view(-1))
        return logits, loss

    def generate(self, idx, max_new=40):
        for _ in range(max_new):
            idx_cond = idx[:, -self.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :]
            ix = torch.multinomial(F.softmax(logits / 0.8, dim=-1), 1)
            idx = torch.cat([idx, ix], dim=1)
        return idx

class Block(nn.Module):
    def __init__(self, n_embd, n_head):
        super().__init__()
        self.ln1 = nn.LayerNorm(n_embd)
        self.attn = Attention(n_embd, n_head)
        self.ln2 = nn.LayerNorm(n_embd)
        self.mlp = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd), nn.GELU(), nn.Linear(4 * n_embd, n_embd))
    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x

class Attention(nn.Module):
    def __init__(self, n_embd, n_head):
        super().__init__()
        self.n_head = n_head; self.n_embd = n_embd
        self.c_attn = nn.Linear(n_embd, 3 * n_embd)
        self.c_proj = nn.Linear(n_embd, n_embd)
    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.c_attn(x).split(self.n_embd, dim=2)
        q = q.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        k = k.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        v = v.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        y = F.scaled_dot_product_attention(q, k, v)
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.c_proj(y)

# ---------- 3. Train a few steps ----------
model = GPT(V)
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
print("training ...")
t0 = time.time()
losses = []
for step in range(30):
    xb, yb = get_batch("train", block_size=64, batch_size=16)
    logits, loss = model(xb, yb)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    losses.append(loss.item())
    if step % 5 == 0 or step == 29:
        print(f"  step {step:2d}  loss {loss.item():.4f}")
elapsed = time.time() - t0
print(f"30 steps in {elapsed:.1f}s  ({elapsed/30*1000:.0f} ms/step)")

# ---------- 4. Generation proof ----------
ctx = torch.tensor([[stoi[b] for b in b"the quick"]])
gen = model.generate(ctx, max_new=40)
out = bytes(itos[i] for i in gen[0].tolist()).decode(errors="replace")
print("sample:", repr(out))

# ---------- Verdict ----------
start, end = losses[0], losses[-1]
ok = end < start * 0.7
print(f"\nVERDICT: loss {start:.4f} -> {end:.4f}  ({'PASS: loss dropped ~{:.0f}%'.format(100*(1-end/start)) if ok else 'FAIL: loss not dropping'})")
print("SMOKE TEST", "PASS" if ok else "FAIL")
