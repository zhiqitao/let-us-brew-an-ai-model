#!/usr/bin/env python3
"""Stage-7 / Ch20 experiment: CONTINUAL LEARNING (capability retention).

Train on capability A (e.g. arithmetic), then on capability B (e.g. lists /
indexing). Measure:
  - B acquisition (did it learn the new op?)
  - A retention (did it keep the old op, or did learning B destroy A?)
Compare SEQUENTIAL vs REPLAY/MIXED training.

Usage: python scripts/run_continual.py [--steps-a N] [--steps-b N]
"""
import os, sys, json, argparse, time, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import Tokenizer
from src.model.gpt import GPT, Config
from src.train.trainer import Dataset, train as train_fn
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge
from src.data_generator.generator import make_task

ROOT = os.path.join(os.path.dirname(__file__), "..")

OP_A = ["add", "sub", "mul", "max_of", "min_of"]       # arithmetic capability
OP_B = ["list_sum", "list_len", "first_element"]        # list capability


def gen_op(ops, n_per, seed):
    tasks = []
    for op in ops:
        for i in range(n_per):
            tasks.append(make_task(op, f"{op}_{i:04d}", seed + i))
    return tasks


def train_both(m, tok, seq_tasks, mix_tasks, steps_a, steps_b, bs=16, lr=1e-3):
    """Sequential: train A then B. Returns per-phase eval on A-test."""
    pass


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
    for mode in ["sequential", "replay"]:
        tok = make_tok(A_train + B_train)
        cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                     n_head=args.n_head, block_size=128)
        m = GPT(cfg)
        if mode == "sequential":
            # phase 1: learn A
            train_fn(m, Dataset(A_train, tok), steps=args.steps_a, bs=16, lr=1e-3,
                     log_every=args.steps_a)
            # phase 2: learn B (exposure to B only)
            train_fn(m, Dataset(B_train, tok), steps=args.steps_b, bs=16, lr=1e-3,
                     log_every=args.steps_b)
        else:
            # replay/mixed: interleave A and B throughout
            mixed = A_train + B_train
            for i in range(len(mixed)):
                pass
            # build a dataset that yields a 50/50 mix by concatenating and shuffling
            allt = A_train + B_train
            random.Random(args.seed).shuffle(allt)
            train_fn(m, Dataset(allt, tok), steps=args.steps_a + args.steps_b,
                     bs=16, lr=1e-3, log_every=max(1, (args.steps_a+args.steps_b)//6))

        judge = Judge()
        from src.eval.evaluator_runner import evaluate_all
        # A retention
        ra = evaluate_all(m, tok, A_train, A_test, judge)
        a_model = next(r for r in ra if r["label"] == "MODEL")
        # B acquisition
        rb = evaluate_all(m, tok, B_train, B_test, judge)
        b_model = next(r for r in rb if r["label"] == "MODEL")
        results[mode] = {"A_retention_pass@1": round(a_model["pass_at_1"], 3),
                         "B_acquisition_pass@1": round(b_model["pass_at_1"], 3)}
        print(f"  {mode:11s}  A-retention={results[mode]['A_retention_pass@1']:.3f} "
              f"  B-acquisition={results[mode]['B_acquisition_pass@1']:.3f}")

    mp = os.path.join(ROOT, "artifacts", "manifests", "continual.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump({"results": results, "config": vars(args)}, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
