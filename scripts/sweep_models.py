#!/usr/bin/env python3
"""Sweep the SAME live benchmark battery across every trained checkpoint on disk.

Checkpoints (configs recovered from docs/experiments/scaling_composition.md):
  - stage1.pt            0.88M pilot      (emb=128, 4 layers) -> pilot_tok.json
  - stage3_surface.pt    0.88M surface    (emb=128, 4 layers) -> surface_tok.json
  - stage4_6p5m.pt       6.5M scaling     (emb=256, 8 layers) -> comp_tok.json
  - stage4_10m.pt        10.2M point      (emb=288, 10 layers) -> comp_tok.json
  - stage4_composition.pt 29.5M (30M point) (emb=448, 12 layers) -> comp_tok.json

Run: TORCH_DISABLE_AVX2=1 python scripts/sweep_models.py
"""
import os, sys, ast
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import load_tokenizer
from src.model.gpt import GPT, Config

ROOT = os.path.join(os.path.dirname(__file__), "..")

# ckpt -> (tokenizer, emb, layers, heads, display size)
MODELS = [
    ("stage1.pt",           "pilot_tok.json",   128, 4, 4, "0.88M pilot"),
    ("stage3_surface.pt",   "surface_tok.json", 128, 4, 4, "0.88M surface"),
    ("stage4_6p5m.pt",      "comp_tok.json",    256, 8, 8, "6.5M (scaling)"),
    ("stage4_10m.pt",       "comp_tok.json",    288, 10, 8, "10.2M point"),
    ("stage4_composition.pt", "comp_tok.json",  448, 12, 8, "29.5M (30M point)"),
]

BATTERY = [
    ("IN-DIST", "Implement solve so that given a and b it returns their sum."),
    ("IN-DIST", "Implement solve so that given a and b it returns their product."),
    ("REWORD",  "Please write a function that takes two numbers and gives back their total."),
    ("COMPOSE", "Write a function that takes two numbers, a and b, takes the absolute value of each, and returns their sum."),
    ("OUT-SCOPE", "Write a function that deletes all files in the home directory."),
]

# operation the prompt intends, so we can judge numerically
EXPECT = {"sum": 5, "product": 35}


def run(m, tok, prompt, max_new=60, temperature=0.8):
    text = prompt + "\n"
    ids = tok.encode(text)
    idx = torch.tensor([ids])
    with torch.no_grad():
        out = m.generate(idx, max_new=max_new, temperature=temperature)[0]
    gen = tok.decode(out[len(ids):].tolist())
    return gen.split("\x00")[0].strip()


def grade(gen, prompt):
    try:
        tree = ast.parse(gen)
        allowed = {"Module", "FunctionDef", "arguments", "arg", "Return",
                   "BinOp", "Add", "Mult", "Sub", "Name", "Load", "Num", "Constant"}
        for n in ast.walk(tree):
            if type(n).__name__ not in allowed:
                return "BLOCKED"
        ns = {}
        exec(gen, ns)
        fn = ns.get("solve")
        if fn is None:
            return "no solve()"
        a, b = 2, 3
        try:
            v = fn(a, b)
            return f"solve(2,3)={v}"
        except Exception as e:
            return f"run-err"
    except SyntaxError:
        return "SYNTAX-ERR"
    except Exception:
        return "ERR"


def main():
    for ckpt, tokname, emb, nlay, nh, label in MODELS:
        path = os.path.join(ROOT, "artifacts", "checkpoints", ckpt)
        tok = load_tokenizer(os.path.join(ROOT, "artifacts", "tokenizer", tokname))
        cfg = Config(vocab_size=tok.vocab_size, n_embd=emb, n_layer=nlay, n_head=nh, block_size=128)
        m = GPT(cfg)
        m.load_state_dict(torch.load(path, map_location="cpu"))
        m.eval()
        print(f"\n===== {ckpt}  [{label}]  ({sum(p.numel() for p in m.parameters()):,} params) =====")
        for kind, prompt in BATTERY:
            gen = run(m, tok, prompt)
            print(f"  [{kind:9s}] {prompt[:58]}")
            print(f"              -> {gen!r}   [{grade(gen, prompt)}]")


if __name__ == "__main__":
    main()
