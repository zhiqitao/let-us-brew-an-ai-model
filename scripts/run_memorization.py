#!/usr/bin/env python3
"""Stage / Level-1 experiment: MEMORIZATION.

Given a trained model, ask: has it memorized the training examples, or learned a
general mapping? We test:
  (a) TRAIN-PROMPT PREFIX: give the model a training example's NL prompt and see if
      it reproduces the exact reference code (memorization signature).
  (b) HELD-OUT PROMPT: a fresh prompt with the same operation -> does it generalize?
      (this is what our pass@1 already measures).
  (c) CANARY: a pair (prompt, code) that never appears in training -> the model must
      NOT reproduce it; if it does, that's leakage / exact memorization.

We compute, over the training set:
  - exact-match rate (generated code == reference code) — high => memorization.
  - pass@1 on those same prompts (should be ~1.0 since they're in training).
And over a held-out set:
  - pass@1 (generalization), which we already know is lower.

Usage: python scripts/run_memorization.py --ckpt artifacts/checkpoints/stage1.pt
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import load_tokenizer
from src.model.gpt import GPT, Config
from src.train.trainer import load_tasks
from src.eval.evaluator_runner import generate_code
from src.evaluator.evaluator import Judge

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "artifacts", "datasets")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=os.path.join(ROOT, "artifacts", "checkpoints", "stage1.pt"))
    ap.add_argument("--tok", default=os.path.join(ROOT, "artifacts", "tokenizer", "pilot_tok.json"))
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--sample", type=int, default=120)
    args = ap.parse_args()

    tok = load_tokenizer(args.tok)
    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)
    m = GPT(cfg); m.load_state_dict(torch.load(args.ckpt)); m.eval()
    judge = Judge()

    train = load_tasks(os.path.join(DATA, "pilot_train.jsonl"))[:args.sample]
    test = load_tasks(os.path.join(DATA, "pilot_test.jsonl"))[:args.sample]

    print("=== (a) MEMORIZATION signature: train-prompt prefix ===")
    exact = 0; pass1 = 0
    for t in train:
        gen = generate_code(m, tok, t["nl"]["prompt"])
        ref = t["reference_code"].strip()
        if gen.strip() == ref:
            exact += 1
        r = judge.evaluate_problem(gen, t["hidden_tests"])
        if r["pass_at_1"]:
            pass1 += 1
    print(f"  train examples: exact-reference-reproduction = {exact}/{len(train)}")
    print(f"  train examples: pass@1 on own prompt        = {pass1}/{len(train)}")

    print("\n=== (b) GENERALIZATION: held-out prompts ===")
    exact_h = 0; pass1_h = 0
    for t in test:
        gen = generate_code(m, tok, t["nl"]["prompt"])
        r = judge.evaluate_problem(gen, t["hidden_tests"])
        if r["pass_at_1"]:
            pass1_h += 1
    print(f"  held-out: pass@1 = {pass1_h}/{len(test)}")

    print("\n=== (c) CANARY (prompts never in training) ===")
    from src.data_generator.generator import make_task
    canary = [make_task("add", f"canary_{i}", seed=99999 + i) for i in range(20)]
    for t in canary[:3]:
        gen = generate_code(m, tok, t["nl"]["prompt"])
        print(f"  prompt: {t['nl']['prompt'][:45]!r}")
        print(f"    GEN: {gen.replace(chr(10),' | ')[:50]!r}")

    report = {"exact_train": exact, "train_n": len(train),
              "pass1_train": pass1, "pass1_test": pass1_h, "test_n": len(test)}
    mp = os.path.join(ROOT, "artifacts", "manifests", "memorization.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump(report, f, indent=2)
    print("\nmanifest ->", mp)


if __name__ == "__main__":
    main()
