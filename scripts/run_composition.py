#!/usr/bin/env python3
"""Stage 4 experiment: STRUCTURAL / COMPOSITIONAL generalization.

Train the student on PRIMITIVE operations only. Then test on:
  (a) held-out primitive test set (in-distribution), and
  (b) COMPOSITE operations that combine two primitives but never appeared in
      training (Level-4 structural / compositional generalization).

The model must COMPOSE known primitives, not retrieve a seen combination. Also
runs the template and retrieval baselines for comparison.

Usage: python scripts/run_composition.py [--steps N] [--n-embd N] [--n-layer N]
"""
import os, sys, json, argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import Tokenizer
from src.model.gpt import GPT, Config
from src.train.trainer import load_tasks, Dataset, train as train_fn
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "artifacts", "datasets")


def build_tokenizer(texts, save_path):
    from src.tokenizer.tokenizer import train_tokenizer
    return train_tokenizer(texts, min_vocab=128, max_vocab=300, save_path=save_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--comp-per-op", type=int, default=40)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    # ---- generate primitive train/val/test + composite held-out set
    from src.data_generator.generator import (generate_dataset, generate_compositional,
                                              OPERATIONS)
    prim = generate_dataset(n_per_op=200, id_set="letters", seed=args.seed)
    from collections import defaultdict
    by_op = defaultdict(list)
    for t in prim:
        by_op[t["semantics"]["operation"]].append(t)
    train, val, test = [], [], []
    for op, g in by_op.items():
        g.sort(key=lambda t: t["task_id"])
        n = len(g); nv = max(1, int(n*0.15)); nt = max(1, int(n*0.15))
        val += g[:nv]; test += g[nv:nv+nt]; train += g[nv+nt:]
    comp = generate_compositional(n_per_op=args.comp_per_op, id_set="letters",
                                  seed=args.seed + 5000)
    for t in train: t["split"] = "train"
    for t in val: t["split"] = "val"
    for t in test: t["split"] = "test"
    for t in comp: t["split"] = "composition_holdout"
    print(f"tasks: train {len(train)} val {len(val)} test {len(test)} "
          f"composition_holdout {len(comp)}")

    # tokenizer trained on primitives + composites (vocab must cover all)
    all_texts = ([t["nl"]["prompt"] + "\n" + t["reference_code"] for t in train] +
                 [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in comp])
    tok_path = os.path.join(ROOT, "artifacts", "tokenizer", "comp_tok.json")
    tok = build_tokenizer(all_texts, tok_path)
    print(f"tokenizer vocab = {tok.vocab_size}")

    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)
    m = GPT(cfg)
    emb, non_emb = m.num_params()
    print(f"model params: emb={emb} non_emb={non_emb} total={emb+non_emb}")

    ds = Dataset(train, tok)
    print(f"training {args.steps} steps on primitives only (composites HELD OUT)...")
    t0 = time.time()
    losses = train_fn(m, ds, steps=args.steps, bs=args.bs, lr=args.lr)
    print(f"trained in {time.time()-t0:.1f}s; final loss {losses[-1]:.4f}")

    ckpt = os.path.join(ROOT, "artifacts", "checkpoints", "stage4_composition.pt")
    os.makedirs(os.path.dirname(ckpt), exist_ok=True)
    torch.save(m.state_dict(), ckpt)
    print("saved model ->", ckpt)

    judge = Judge()
    print("\n=== IN-DISTRIBUTION test (held-out primitives) vs baselines ===")
    r1 = evaluate_all(m, tok, train, test, judge)
    for r in r1:
        print(f"  {r['label']:9s} pass@1={r['pass_at_1']:.3f}")

    print("\n=== COMPOSITIONAL generalization (composites never seen in training) ===")
    r2 = evaluate_all(m, tok, train, comp, judge)
    for r in r2:
        print(f"  {r['label']:9s} pass@1={r['pass_at_1']:.3f}")

    manifest = {
        "experiment_id": f"stage4_composition_seed{args.seed}",
        "status": "MEASURED",
        "config": vars(args),
        "model_params": {"embedding": emb, "non_embedding": non_emb, "total": emb+non_emb},
        "tokenizer_vocab": tok.vocab_size,
        "final_train_loss": round(losses[-1], 4),
        "in_distribution": r1,
        "compositional": r2,
        "dataset_version": "v0_1",
        "spec_version": "python_capability_v0_1",
    }
    mp = os.path.join(ROOT, "artifacts", "manifests", "stage4_composition.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
