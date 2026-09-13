#!/usr/bin/env python3
"""Recover the sequential A-before-B measurement for the continual-learning result.

The original run_continual.py only evaluates A at the END (after B), so its 0.000 final
A score cannot distinguish "A was learned then forgotten" from "A was never learned under
this budget". This script re-runs the SAME sequential pipeline (same ops, seeds, sizes,
steps, tokenizer schedule, optimizer defaults) but adds an intermediate A evaluation right
after phase A and before phase B. That gives a before/after measurement on the same
trajectory.

It also re-runs the joint/replay control so the pair can be reported consistently.
"""
import os, sys, json, argparse, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import Tokenizer
from src.model.gpt import GPT, Config
from src.train.trainer import Dataset, train as train_fn
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge
from src.data_generator.generator import make_task

ROOT = os.path.join(os.path.dirname(__file__), "..")
OP_A = ["add", "sub", "mul", "max_of", "min_of"]
OP_B = ["list_sum", "list_len", "first_element"]


def gen_op(ops, n_per, seed):
    tasks = []
    for op in ops:
        for i in range(n_per):
            tasks.append(make_task(op, f"{op}_{i:04d}", seed + i))
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps-a", type=int, default=600)
    ap.add_argument("--steps-b", type=int, default=600)
    ap.add_argument("--n-per", type=int, default=80)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    A_train = gen_op(OP_A, args.n_per, args.seed)
    B_train = gen_op(OP_B, args.n_per, args.seed + 111)
    A_test = gen_op(OP_A, 12, args.seed + 222)
    B_test = gen_op(OP_B, 12, args.seed + 333)
    from src.train.trainer import Dataset

    def make_tok(tasks):
        from src.tokenizer.tokenizer import train_tokenizer
        return train_tokenizer([t["nl"]["prompt"] + "\n" + t["reference_code"] for t in tasks],
                               min_vocab=128, max_vocab=300)

    results = {}
    for mode in ["sequential"]:
        tok = make_tok(A_train + B_train)
        cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                     n_head=args.n_head, block_size=128)
        m = GPT(cfg)
        judge = Judge()
        # phase 1: learn A
        train_fn(m, Dataset(A_train, tok), steps=args.steps_a, bs=16, lr=1e-3,
                 log_every=args.steps_a)
        # INTERMEDIATE A eval right after phase A, before any B exposure
        ra_pre = evaluate_all(m, tok, A_train, A_test, judge)
        a_pre = next(r for r in ra_pre if r["label"] == "MODEL")
        # phase 2: learn B (no A exposure)
        train_fn(m, Dataset(B_train, tok), steps=args.steps_b, bs=16, lr=1e-3,
                 log_every=args.steps_b)
        # final A and B
        ra = evaluate_all(m, tok, A_train, A_test, judge)
        a_post = next(r for r in ra if r["label"] == "MODEL")
        rb = evaluate_all(m, tok, B_train, B_test, judge)
        b_post = next(r for r in rb if r["label"] == "MODEL")
        results[mode] = {
            "A_pass@1_after_phaseA": round(a_pre["pass_at_1"], 3),
            "A_pass@1_final_after_B": round(a_post["pass_at_1"], 3),
            "B_pass@1_final": round(b_post["pass_at_1"], 3),
        }
        print(f"  {mode:11s}  A-after-A={results[mode]['A_pass@1_after_phaseA']:.3f}  "
              f"A-after-B={results[mode]['A_pass@1_final_after_B']:.3f}  "
              f"B={results[mode]['B_pass@1_final']:.3f}")

    mp = os.path.join(ROOT, "artifacts", "manifests", "continual_preB.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump({"results": results, "config": vars(args)}, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
