"""Training pipeline for the student model (NL spec -> Python program).

Reads the pilot JSONL dataset, tokenizes prompt+code, trains the small GPT with the
standard next-token objective. `scripts/train.py` drives this.
"""
import json
import torch
from src.model.gpt import GPT, Config


def load_tasks(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def to_examples(task, tokenizer, prompt_marker="\n", max_len=128):
    prompt = task["nl"]["prompt"] + prompt_marker
    code = task["reference_code"]
    text = prompt + code
    ids = tokenizer.encode(text)[:max_len]
    return ids


class Dataset:
    def __init__(self, tasks, tokenizer, max_len=128):
        self.examples = [to_examples(t, tokenizer, max_len=max_len) for t in tasks]
        self.examples = [e for e in self.examples if len(e) >= 4]

    def __len__(self):
        return len(self.examples)

    def batch(self, bs):
        import random
        idx = [random.choice(self.examples) for _ in range(bs)]
        T = max(len(e) for e in idx)
        T = min(T, 128)
        x = torch.zeros((bs, T), dtype=torch.long)
        for i, e in enumerate(idx):
            x[i, :len(e)] = torch.tensor(e[:T])
        return x


def train(model, dataset, steps=2000, bs=16, lr=1e-3, device="cpu", log_every=200):
    model.to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    model.train()
    losses = []
    for step in range(steps):
        x = dataset.batch(bs).to(device)
        _, loss = model(x, x)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        losses.append(loss.item())
        if step % log_every == 0 or step == steps - 1:
            print(f"  step {step:4d}  loss {loss.item():.4f}")
    return losses
