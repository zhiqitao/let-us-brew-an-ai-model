#!/usr/bin/env python3
"""Stage 1 pilot: train the student on the pilot dataset, then evaluate it against
the template + retrieval baselines (Milestone 2). Records an experiment manifest.

Usage: python scripts/train.py [--steps N] [--n-embd N] [--n-layer N] [--bs N]
"""
import os, sys, json, argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import Tokenizer
from src.model.gpt import GPT, Config
from src.train.trainer import load_tasks, Dataset, train
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "artifacts", "datasets")


def build_tokenizer(train_tasks, save_path):
    texts = [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in train_tasks]
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
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    train_tasks = load_tasks(os.path.join(DATA, "pilot_train.jsonl"))
    val_tasks = load_tasks(os.path.join(DATA, "pilot_val.jsonl"))
    test_tasks = load_tasks(os.path.join(DATA, "pilot_test.jsonl"))
    print(f"tasks: train {len(train_tasks)} val {len(val_tasks)} test {len(test_tasks)}")

    tok_path = os.path.join(ROOT, "artifacts", "tokenizer", "pilot_tok.json")
    tok = build_tokenizer(train_tasks, tok_path)
    print(f"tokenizer vocab = {tok.vocab_size}")

    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)
    m = GPT(cfg)
    emb, non_emb = m.num_params()
    total = emb + non_emb
    print(f"model params: embedding={emb} non_emb={non_emb} total={total}")

    ds = Dataset(train_tasks, tok)
    print(f"training {args.steps} steps (bs={args.bs}, lr={args.lr}) ...")
    t0 = time.time()
    losses = train(m, ds, steps=args.steps, bs=args.bs, lr=args.lr)
    train_time = time.time() - t0
    print(f"trained in {train_time:.1f}s; final loss {losses[-1]:.4f}")

    # save model + manifest BEFORE evaluation so a crash doesn't lose training.
    ckpt = os.path.join(ROOT, "artifacts", "checkpoints", "stage1.pt")
    os.makedirs(os.path.dirname(ckpt), exist_ok=True)
    torch.save(m.state_dict(), ckpt)
    print("saved model ->", ckpt)

    print("\n=== evaluation (test set) vs baselines ===")
    judge = Judge()
    results = evaluate_all(m, tok, train_tasks, test_tasks, judge)
    for r in results:
        print(f"  {r['label']:9s} syntax={r['syntax_rate']:.3f} "
              f"exec={r['executable_rate']:.3f} pass@1={r['pass_at_1']:.3f}")

    manifest = {
        "experiment_id": f"stage1_seed{args.seed}",
        "status": "MEASURED",
        "config": vars(args),
        "model_params": {"embedding": emb, "non_embedding": non_emb, "total": total},
        "tokenizer_vocab": tok.vocab_size,
        "train_time_s": round(train_time, 1),
        "final_train_loss": round(losses[-1], 4),
        "results": results,
        "dataset_version": "v0_1",
        "evaluator_version": "v0_1",
        "spec_version": "python_capability_v0_1",
    }
    mp = os.path.join(ROOT, "artifacts", "manifests", "stage1.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
