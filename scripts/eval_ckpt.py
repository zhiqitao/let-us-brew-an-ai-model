#!/usr/bin/env python3
"""Eval-only: load a saved composition checkpoint and evaluate in-dist + composition.
Avoids retraining (the heavy part). Used to re-run eval after the retrieval-baseline
perf fix.

Usage: python scripts/eval_ckpt.py --ckpt artifacts/checkpoints/stage4_composition.pt
         [--n-embd N --n-layer N --n-head N] [--tok artifacts/tokenizer/comp_tok.json]
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import Tokenizer, load_tokenizer
from src.model.gpt import GPT, Config
from src.train.trainer import load_tasks
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge
from src.data_generator.generator import generate_dataset, generate_compositional
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "artifacts", "datasets")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=os.path.join(ROOT, "artifacts", "checkpoints", "stage4_composition.pt"))
    ap.add_argument("--tok", default=os.path.join(ROOT, "artifacts", "tokenizer", "comp_tok.json"))
    ap.add_argument("--n-embd", type=int, default=256)
    ap.add_argument("--n-layer", type=int, default=8)
    ap.add_argument("--n-head", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--comp-per-op", type=int, default=40)
    ap.add_argument("--sample", type=int, default=60, help="eval at most this many tasks per set")
    args = ap.parse_args()

    tok = load_tokenizer(args.tok)
    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)
    m = GPT(cfg); m.load_state_dict(torch.load(args.ckpt)); m.eval()

    prim = generate_dataset(n_per_op=200, id_set="letters", seed=args.seed)
    by_op = defaultdict(list)
    for t in prim: by_op[t["semantics"]["operation"]].append(t)
    train, test = [], []
    for op, g in by_op.items():
        g.sort(key=lambda t: t["task_id"])
        n = len(g); nv = max(1, int(n*0.15)); nt = max(1, int(n*0.15))
        test += g[nv:nv+nt]; train += g[nv+nt:]
    comp = generate_compositional(n_per_op=args.comp_per_op, id_set="letters", seed=args.seed + 5000)
    # sample to keep eval fast
    import random
    rng = random.Random(1)
    test = rng.sample(test, min(args.sample, len(test)))
    comp = rng.sample(comp, min(args.sample, len(comp)))

    judge = Judge()
    print("=== IN-DISTRIBUTION (held-out primitives) ===")
    r1 = evaluate_all(m, tok, train, test, judge)
    for r in r1: print(f"  {r['label']:9s} pass@1={r['pass_at_1']:.3f}")
    print("\n=== COMPOSITIONAL (unseen combos) ===")
    r2 = evaluate_all(m, tok, train, comp, judge)
    for r in r2: print(f"  {r['label']:9s} pass@1={r['pass_at_1']:.3f}")

    mp = os.path.join(ROOT, "artifacts", "manifests", "stage4_scaling.json")
    with open(mp, "w") as f:
        json.dump({"config": vars(args), "in_distribution": r1, "compositional": r2}, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
