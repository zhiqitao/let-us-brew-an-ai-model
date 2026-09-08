#!/usr/bin/env python3
"""Run the dataset leakage audit (spec section 11).

Generates a fresh dataset, trains a TF-IDF + logistic-regression classifier to see
whether a trivial model can predict the operation from the NL text, and checks for
duplicates.

Usage: python scripts/audit.py [--n-per-op N] [--seed S]
"""
import os, sys, json, argparse, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.audit.leakage import classifier_leakage, duplicate_checks, split_operation_distribution
from src.data_generator.generator import generate_dataset

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-op", type=int, default=120)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    tasks = generate_dataset(n_per_op=args.n_per_op, id_set="letters", seed=args.seed)
    # assign splits like scripts/generate_data.py (operation-disjoint)
    from collections import defaultdict
    by_op = defaultdict(list)
    for t in tasks:
        by_op[t["semantics"]["operation"]].append(t)
    for op, g in by_op.items():
        for i, t in enumerate(sorted(g, key=lambda x: x["task_id"])):
            t["split"] = "train" if i % 10 < 7 else ("val" if i % 10 < 8 else "test")

    print(f"=== leakage audit: {len(tasks)} tasks ===")
    print("\n-- classifier: can a trivial model predict the operation from NL? --")
    acc = classifier_leakage(tasks, "operation")
    print(f"  cross-val accuracy (prediction operation): {acc:.3f}  "
          f"{'[LEAK WARNING >0.9]' if acc and acc > 0.9 else '[ok]'}")

    print("\n-- duplicate prompt check --")
    nd, sample = duplicate_checks(tasks)
    print(f"  exact-duplicate prompts: {nd}" + (f" e.g. {sample}" if sample else ""))

    print("\n-- split operation distribution --")
    for s, d in split_operation_distribution(tasks).items():
        print(f"  {s}: {d}")

    # report
    out = os.path.join(ROOT, "artifacts", "results", "leakage_audit.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    report = {"n_tasks": len(tasks), "classifier_op_accuracy": acc,
              "duplicate_prompts": nd, "dist": split_operation_distribution(tasks)}
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nwritten -> {out}")


if __name__ == "__main__":
    main()
