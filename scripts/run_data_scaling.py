#!/usr/bin/env python3
"""Chapter-11 experiment: HOW MUCH DATA?

Hold model architecture + training protocol constant. Vary dataset size (1K, 5K,
10K...). Measure in-distribution pass@1 and surface-robustness. Distinguish
more-examples from more-diversity.

Usage: python scripts/run_data_scaling.py [--sizes 100 300 1000 3000] [--steps N]
"""
import os, sys, json, argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import Tokenizer
from src.model.gpt import GPT, Config
from src.train.trainer import Dataset, train as train_fn
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge
from src.data_generator.generator import generate_dataset
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..")


def split_by_op(tasks):
    by_op = defaultdict(list)
    for t in tasks:
        by_op[t["semantics"]["operation"]].append(t)
    train, test = [], []
    for op, g in by_op.items():
        g.sort(key=lambda t: t["task_id"])
        nv = max(1, int(len(g)*0.1)); nt = max(1, int(len(g)*0.1))
        test += g[:nt]
        train += g[nt:]
    return train, test


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[100, 300, 1000, 3000])
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    # build a large pool, then sample sizes from it (same distribution).
    pool = generate_dataset(n_per_op=400, id_set="letters", seed=args.seed)
    pool_test, _ = split_by_op(generate_dataset(n_per_op=60, id_set="letters", seed=args.seed+99))
    judge = Judge()

    print("=== data scaling (in-distribution pass@1) ===")
    rows = []
    for size in args.sizes:
        train = pool[:size]
        all_texts = [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in train]
        from src.tokenizer.tokenizer import train_tokenizer
        tok = train_tokenizer(all_texts, min_vocab=128, max_vocab=300)
        cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                     n_head=args.n_head, block_size=128)
        m = GPT(cfg)
        ds = Dataset(train, tok)
        t0 = time.time()
        losses = train_fn(m, ds, steps=args.steps, bs=16, lr=1e-3)
        res = evaluate_all(m, tok, train, pool_test, judge)
        model = next(r for r in res if r["label"] == "MODEL")
        row = {"dataset_size": size, "final_loss": round(losses[-1], 3),
               "pass_at_1": round(model["pass_at_1"], 3),
               "train_time_s": round(time.time()-t0, 1)}
        rows.append(row)
        print(f"  size {size:5d}: loss={row['final_loss']:.3f} "
              f"pass@1={row['pass_at_1']:.3f} ({row['train_time_s']}s)")

    mp = os.path.join(ROOT, "artifacts", "manifests", "data_scaling.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump({"rows": rows, "config": vars(args)}, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
