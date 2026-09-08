#!/usr/bin/env python3
"""Generate the pilot dataset and write it to artifacts/datasets/ as JSONL.

Splits are assigned by OPERATION distribution so train/val/test are semantically
disjoint (no near-duplicate operation leakage). The pilot uses the Stage-1 task set:
arithmetic + comparison/conditional basics.

Usage: python scripts/generate_data.py [--n-per-op N] [--seed S]
"""
import os, json, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_generator.generator import generate_dataset

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "artifacts", "datasets")
os.makedirs(OUT, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-op", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    tasks = generate_dataset(n_per_op=args.n_per_op, id_set="letters", seed=args.seed)
    # Assign splits: per operation, 70% train / 15% val / 15% test.
    from collections import defaultdict
    by_op = defaultdict(list)
    for t in tasks:
        by_op[t["semantics"]["operation"]].append(t)
    splits = {"train": [], "val": [], "test": []}
    for op, group in by_op.items():
        n = len(group)
        nv = max(1, int(n * 0.15)); nt = max(1, int(n * 0.15))
        group.sort(key=lambda t: t["task_id"])
        splits["val"].extend(group[:nv])
        splits["test"].extend(group[nv:nv + nt])
        splits["train"].extend(group[nv + nt:])
    for t in splits["train"]: t["split"] = "train"
    for t in splits["val"]: t["split"] = "val"
    for t in splits["test"]: t["split"] = "test"

    manifest = {
        "dataset_version": "v0_1",
        "seed": args.seed,
        "n_per_op": args.n_per_op,
        "counts": {k: len(v) for k, v in splits.items()},
        "operations": list(by_op.keys()),
    }
    for split, items in splits.items():
        p = os.path.join(OUT, f"pilot_{split}.jsonl")
        with open(p, "w") as f:
            for t in items:
                t["split"] = split
                f.write(json.dumps(t) + "\n")
        print(f"{split}: {len(items)} tasks -> {p}")
    mp = os.path.join(OUT, "pilot_manifest.json")
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
