#!/usr/bin/env python3
"""Composition-exposure experiment — the book's central open question.

Does training on a FEW composite operations unlock composition on UNSEEN
composites?

Baseline (already measured): train on primitives ONLY -> composition 0.000.

Here we train on primitives + a small subset of composite operations, and test on
the composite operations that were NEVER seen in training. If composition is a
learnable structural skill, exposure to some combinations should transfer to new
ones. If it's purely memorization of seen combinations, the held-out composites
stay at 0.000.

The 6 composite ops are split:
  EXPOSED (train):  abs_add, sub_abs, sum_of_abs
  HELD-OUT (test):  max_add, double_first, len_minus_one

Run: TORCH_DISABLE_AVX2=1 python scripts/run_composition_exposure.py
"""
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.data_generator.generator import generate_dataset, generate_compositional
from src.model.gpt import GPT, Config
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXPOSED = ["abs_add", "sub_abs", "sum_of_abs"]
HELD_OUT = ["max_add", "double_first", "len_minus_one"]


def main():
    import argparse
    from collections import defaultdict
    from src.tokenizer.tokenizer import train_tokenizer
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-per-op", type=int, default=200)
    ap.add_argument("--comp-n", type=int, default=40)
    ap.add_argument("--out", default=os.path.join(ROOT, "artifacts", "checkpoints", "stage4_exposure.pt"))
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    # ---- primitives: train/val/test (same split as run_composition) ----
    prim = generate_dataset(n_per_op=args.n_per_op, id_set="letters", seed=args.seed)
    by_op = defaultdict(list)
    for t in prim:
        by_op[t["semantics"]["operation"]].append(t)
    train, val, test = [], [], []
    for op, g in by_op.items():
        g.sort(key=lambda t: t["task_id"])
        n = len(g); nv = max(1, int(n*0.15)); nt = max(1, int(n*0.15))
        val += g[:nv]; test += g[nv:nv+nt]; train += g[nv+nt:]

    # ---- composites: split by operation into exposed (train) / held-out (test) ----
    comp = generate_compositional(n_per_op=args.comp_n, id_set="letters", seed=args.seed + 5000)
    by_op_c = defaultdict(list)
    for t in comp:
        by_op_c[t["semantics"]["operation"]].append(t)

    # dedupe composites by (op, arg pattern) so we don't train+test the same instance
    exposed, heldout = [], []
    for op, g in by_op_c.items():
        if op in EXPOSED:
            exposed += g
        elif op in HELD_OUT:
            heldout += g
        else:
            print(f"  (skipping composite op not in either split: {op})")

    print(f"primitives: train {len(train)} val {len(val)} test {len(test)}")
    print(f"composites: EXPOSED(train) {len(exposed)}  HELD-OUT(test) {len(heldout)}")
    print(f"  exposed ops: {EXPOSED}")
    print(f"  held-out ops: {HELD_OUT}")

    # ---- train set = primitives + exposed composites ----
    for t in train: t["split"] = "train"
    for t in val: t["split"] = "val"
    for t in test: t["split"] = "test"
    for t in exposed: t["split"] = "train"
    for t in heldout: t["split"] = "composition_holdout"
    train_with_comp = train + exposed

    # tokenizer over all texts (primitives + exposed + heldout so vocab covers all)
    all_texts = ([t["nl"]["prompt"] + "\n" + t["reference_code"] for t in train_with_comp] +
                 [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in heldout])
    tok_path = os.path.join(ROOT, "artifacts", "tokenizer", "comp_tok.json")
    tok = train_tokenizer(all_texts, min_vocab=128, max_vocab=300, save_path=tok_path)
    print(f"tokenizer vocab = {tok.vocab_size}")

    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)
    m = GPT(cfg)
    emb, non_emb = m.num_params()
    print(f"model params: total={emb+non_emb:,}")

    from src.train.trainer import Dataset, train as train_fn
    ds = Dataset(train_with_comp, tok)
    print(f"training {args.steps} steps on primitives + {len(exposed)} EXPOSED composites...")
    t0 = time.time()
    losses = train_fn(m, ds, steps=args.steps, bs=16, lr=1e-3)
    print(f"trained in {time.time()-t0:.1f}s; final loss {losses[-1]:.4f}")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    torch.save(m.state_dict(), args.out)
    print("saved model ->", args.out)

    judge = Judge()
    print("\n=== IN-DISTRIBUTION (held-out primitives) ===")
    r1 = evaluate_all(m, tok, train, test, judge)
    for r in r1:
        print(f"  {r['label']:9s} pass@1={r['pass_at_1']:.3f}")

    print("\n=== EXPOSED COMPOSITES (seen in training) ===")
    r2 = evaluate_all(m, tok, train, exposed, judge)
    for r in r2:
        print(f"  {r['label']:9s} pass@1={r['pass_at_1']:.3f}")

    print("\n=== HELD-OUT COMPOSITES (never seen) — THE KEY QUESTION ===")
    r3 = evaluate_all(m, tok, train, heldout, judge)
    for r in r3:
        print(f"  {r['label']:9s} pass@1={r['pass_at_1']:.3f}")

    manifest = {
        "experiment_id": f"composition_exposure{args.tag}",
        "status": "MEASURED",
        "config": vars(args),
        "exposed_ops": EXPOSED,
        "held_out_ops": HELD_OUT,
        "model_params": {"embedding": emb, "non_embedding": non_emb, "total": emb+non_emb},
        "final_train_loss": round(losses[-1], 4),
        "in_distribution": r1,
        "exposed_composites": r2,
        "held_out_composites": r3,
    }
    mp = os.path.join(ROOT, "artifacts", "manifests", f"composition_exposure{args.tag}.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
