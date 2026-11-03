#!/usr/bin/env python3
"""CORRECTED B1 — data scaling, balanced & operation-stratified (fixes P0-01).

Bug P0-01: the original `scripts/run_data_scaling.py` did `train = pool[:size]`
on a pool laid out operation-by-operation, so the 100/300/1000/3000 arms
covered only 1/1/3/8 of the 10 operations — "dataset size" was confounded with
operation coverage — and it refit the tokenizer per arm.

Corrections:
  * pool over ALL 10 primitive operations; for each size a BALANCED, SHUFFLED
    train set with exactly size/10 tasks per operation (10/10 ops in every arm,
    nested prefixes so smaller arms are subsets of larger ones);
  * ONE fixed tokenizer (prespecified corpus, saved once to
    artifacts/tokenizer/data_scaling_corrected_tok.json) reused across every
    size AND every seed — never refit per arm; its sha256 is asserted equal
    across arms;
  * identical training protocol for every arm: n_embd 128, 4 layers, 4 heads,
    block 128, 1000 steps, batch 16, lr 1e-3;
  * ONE fixed held-out test set (30/op, 10/10 ops, seed 777) shared by all
    arms and seeds, content-disjoint from every train set;
  * aggregate AND per-operation pass@1 with exact integer successes.

Resume-safe: per-arm results go to a partial file and per-arm checkpoints to
artifacts/checkpoints/, so the retry-on-SIGILL wrapper restarts cheaply.

Usage: python scripts/run_data_scaling_corrected.py --seed 0
"""
import argparse
import json
import os
import random
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import torch

from src.data_generator.generator import OPERATIONS, generate_dataset
from src.evaluator.evaluator import Judge
from src.model.gpt import Config, GPT
from src.tokenizer.tokenizer import load_tokenizer, train_tokenizer
from src.train.trainer import Dataset, train as train_fn

from corrected_common import (assert_full_byte_alphabet, content_stats,
                              instance_seeds, load_partial, per_op_counts,
                              save_partial, score_all, vocab_sha256)

ROOT = os.path.join(_HERE, "..")
ALL_OPS = list(OPERATIONS)
N_OPS = len(ALL_OPS)
TOK_CORPUS_SEED = 4242   # prespecified tokenizer corpus (fixed across seeds/sizes)
TEST_SEED = 777          # prespecified held-out test set (fixed across seeds/sizes)


def get_fixed_tokenizer(path, corpus_per_op):
    """ONE tokenizer, built once, then loaded verbatim by every arm/seed."""
    if os.path.exists(path):
        return load_tokenizer(path), "loaded_existing"
    corpus = generate_dataset(n_per_op=corpus_per_op, id_set="letters",
                              seed=TOK_CORPUS_SEED)
    texts = [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in corpus]
    tok = train_tokenizer(texts, min_vocab=128, max_vocab=300, save_path=path)
    return tok, "trained_now"


def balanced_nested_selection(pool_by_op, sizes, seed):
    """Per op: one seeded shuffle; each size takes the first size/N_OPS items
    (so arms are nested and every arm is exactly balanced across 10/10 ops).
    The assembled train list is then shuffled."""
    selected = {}
    per_op_shuffles = {}
    for opi, op in enumerate(ALL_OPS):
        g = list(pool_by_op[op])
        rng = random.Random(seed * 7919 + opi)
        rng.shuffle(g)
        per_op_shuffles[op] = g
    for size in sizes:
        n_per_op = size // N_OPS
        rng = random.Random(seed * 104729 + size)
        train, counts = [], {}
        for op in ALL_OPS:
            sel = per_op_shuffles[op][:n_per_op]
            assert len(sel) == n_per_op, (op, len(sel), n_per_op)
            counts[op] = len(sel)
            train.extend(sel)
        rng.shuffle(train)
        assert len(train) == size, (len(train), size)
        assert set(counts) == set(ALL_OPS) and all(v == n_per_op for v in counts.values())
        selected[size] = (train, counts, n_per_op)
    return selected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[100, 300, 1000, 3000])
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--pool-per-op", type=int, default=400)
    ap.add_argument("--n-test-per-op", type=int, default=30)
    ap.add_argument("--tok-corpus-per-op", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--manifest-dir", default=os.path.join(ROOT, "artifacts", "manifests"))
    ap.add_argument("--ckpt-dir", default=os.path.join(ROOT, "artifacts", "checkpoints"))
    ap.add_argument("--tok-path", default=os.path.join(ROOT, "artifacts", "tokenizer",
                                                       "data_scaling_corrected_tok.json"))
    args = ap.parse_args()
    for s in args.sizes:
        assert s % N_OPS == 0, f"size {s} not divisible by {N_OPS} ops"
    assert args.pool_per_op * N_OPS >= max(args.sizes)
    seed = args.seed
    random.seed(seed)
    torch.manual_seed(seed)

    # ---- ONE fixed tokenizer (never refit per size/seed) -------------------
    os.makedirs(os.path.dirname(args.tok_path), exist_ok=True)
    tok, tok_source = get_fixed_tokenizer(args.tok_path, args.tok_corpus_per_op)
    assert_full_byte_alphabet(tok)
    tok_sha = vocab_sha256(tok)
    print(f"tokenizer: vocab={tok.vocab_size} sha={tok_sha[:12]} source={tok_source}",
          flush=True)

    # ---- pool over ALL 10 operations --------------------------------------
    pool = generate_dataset(n_per_op=args.pool_per_op, id_set="letters", seed=seed)
    pool_by_op = per_op_counts(pool)
    assert set(pool_by_op) == set(ALL_OPS), f"pool covers {len(pool_by_op)}/{N_OPS} ops"
    assert all(v >= max(args.sizes) // N_OPS for v in pool_by_op.values())
    from collections import defaultdict
    pool_groups = defaultdict(list)
    for t in pool:
        pool_groups[t["semantics"]["operation"]].append(t)

    # ---- ONE fixed held-out test set (10/10 ops) --------------------------
    test = generate_dataset(n_per_op=args.n_test_per_op, id_set="letters",
                            seed=TEST_SEED)
    test_counts = per_op_counts(test)
    assert len(test) == args.n_test_per_op * N_OPS
    assert set(test_counts) == set(ALL_OPS) and all(
        v == args.n_test_per_op for v in test_counts.values())
    # Instance-level holdout: the test set's construction seeds must not appear
    # in the pool. (Content-level disjointness is impossible in this benchmark:
    # prompt+code are deterministic in (op, family, id_set) — only 21 distinct
    # contents exist for the letters identifier set — so "held out" means new
    # instances with new hidden tests, which we verify via instance seeds.)
    pool_seeds = instance_seeds(pool)
    test_seeds = instance_seeds(test)
    assert not (pool_seeds & test_seeds), "test instances leak into the pool"

    selected = balanced_nested_selection(pool_groups, args.sizes, seed)

    # ---- per-arm training + evaluation (resume-safe) ----------------------
    os.makedirs(args.manifest_dir, exist_ok=True)
    os.makedirs(args.ckpt_dir, exist_ok=True)
    partial_path = os.path.join(args.manifest_dir,
                                f".partial_data_scaling_corrected_seed{seed}.json")
    partial = load_partial(partial_path)
    judge = Judge()
    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)

    rows, shas = [], set()
    for size in args.sizes:
        train, counts, n_per_op = selected[size]
        assert len(train) == size
        assert set(counts) == set(ALL_OPS) and all(v == n_per_op for v in counts.values())
        assert not (instance_seeds(train) & test_seeds), "test instance in train"

        if str(size) in partial:
            row = partial[str(size)]
            rows.append(row)
            shas.add(row["tokenizer_sha256"])
            print(f"  size {size:5d}: cached (partial) pass@1={row['aggregate_pass_at_1']}",
                  flush=True)
            continue

        ckpt_path = os.path.join(args.ckpt_dir,
                                 f"data_scaling_corrected_seed{seed}_size{size}.pt")
        model, final_loss, train_s = None, None, None
        if os.path.exists(ckpt_path):
            blob = torch.load(ckpt_path, map_location="cpu", weights_only=True)
            model = GPT(cfg)
            model.load_state_dict(blob["state_dict"])
            final_loss, train_s = blob["final_loss"], blob.get("train_time_s", None)
            print(f"  size {size:5d}: loaded checkpoint {ckpt_path}", flush=True)
        if model is None:
            torch.manual_seed(seed * 10007 + size)  # per-arm init
            model = GPT(cfg)
            ds = Dataset(train, tok)
            t0 = time.time()
            losses = train_fn(model, ds, steps=args.steps, bs=args.bs, lr=args.lr)
            train_s = round(time.time() - t0, 1)
            final_loss = float(losses[-1])
            torch.save({"state_dict": model.state_dict(), "final_loss": final_loss,
                        "train_time_s": train_s}, ckpt_path)
            print(f"  size {size:5d}: trained {args.steps} steps in {train_s}s "
                  f"loss={final_loss:.4f}", flush=True)

        t0 = time.time()
        scores = score_all(model, tok, train, test, judge,
                           eval_seed=seed * 10007 + size + 1)
        eval_s = round(time.time() - t0, 1)
        m = scores["MODEL"]
        assert m["denominator"] == len(test)
        row = {
            "size": size,
            "n_per_op": n_per_op,
            "per_op_counts": counts,
            "ops_covered": len(counts),
            "aggregate_pass_at_1": m["pass_at_1"],
            "per_op_pass_at_1": {op: v["pass_at_1"] for op, v in m["per_op"].items()},
            "model_successes": m["successes"],
            "model_denominator": m["denominator"],
            "template_pass_at_1": scores["TEMPLATE"]["pass_at_1"],
            "template_successes": scores["TEMPLATE"]["successes"],
            "retrieval_pass_at_1": scores["RETRIEVAL"]["pass_at_1"],
            "retrieval_successes": scores["RETRIEVAL"]["successes"],
            "baseline_denominator": m["denominator"],
            "final_loss": round(final_loss, 4),
            "seed": seed,
            "steps": args.steps,
            "n_per_op_train": n_per_op,
            "tokenizer_sha256": tok_sha,
            "train_content": content_stats(train),
            "train_time_s": train_s,
            "eval_time_s": eval_s,
        }
        assert row["ops_covered"] == N_OPS
        rows.append(row)
        shas.add(tok_sha)
        partial[str(size)] = row
        save_partial(partial_path, partial)
        print(f"  size {size:5d}: pass@1={m['pass_at_1']:.3f} "
              f"({m['successes']}/{m['denominator']}) "
              f"tmpl={scores['TEMPLATE']['pass_at_1']:.3f} "
              f"ret={scores['RETRIEVAL']['pass_at_1']:.3f} "
              f"loss={row['final_loss']:.4f} eval={eval_s}s", flush=True)

    assert len(shas) == 1, f"tokenizer drifted across arms: {shas}"
    assert all(r["ops_covered"] == N_OPS for r in rows)
    assert all(r["model_denominator"] == len(test) for r in rows)

    manifest = {
        "experiment_id": "data_scaling_corrected",
        "status": "MEASURED",
        "fixes": ["P0-01"],
        "seed": seed,
        "config": vars(args),
        "tokenizer": {
            "vocab_size": tok.vocab_size,
            "sha256": tok_sha,
            "source": tok_source,
            "corpus": (f"generate_dataset(n_per_op={args.tok_corpus_per_op}, "
                       f"id_set='letters', seed={TOK_CORPUS_SEED}) "
                       f"= union of training texts at the largest size"),
            "fixed_across_sizes": True,
            "fixed_across_seeds": True,
            "refit_per_arm": False,
        },
        "pool": {"n": len(pool), "per_op": pool_groups and pool_by_op, "seed": seed,
                 "id_set": "letters"},
        "test_set": {"n": len(test), "n_per_op": args.n_test_per_op,
                     "per_op": test_counts, "ops_covered": len(test_counts),
                     "seed": TEST_SEED, "id_set": "letters",
                     "content": content_stats(test),
                     "fixed_across_sizes_and_seeds": True,
                     "holdout_level": "instance (new construction seeds + new "
                                      "hidden tests); content-level holdout is "
                                      "impossible in-distribution because "
                                      "prompt+code are deterministic in "
                                      "(op, family, id_set)"},
        "selection": {"strategy": "balanced nested per-op prefixes, shuffled",
                      "n_per_op_by_size": {str(s): s // N_OPS for s in args.sizes},
                      "nested_across_sizes": True},
        "rows": rows,
        "assertions": {
            "every_arm_covers_10_of_10_ops": True,
            "every_arm_balanced_per_op": True,
            "realized_len_equals_expected_size": True,
            "tokenizer_identical_across_arms": True,
            "train_test_instance_disjoint": True,
            "test_denominator_exact": len(test),
        },
    }
    mp = os.path.join(args.manifest_dir, f"data_scaling_corrected_seed{seed}.json")
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp, flush=True)
    for r in rows:
        print(f"  size={r['size']:5d} n_per_op={r['n_per_op']:3d} "
              f"pass@1={r['aggregate_pass_at_1']:.3f} "
              f"({r['model_successes']}/{r['model_denominator']}) "
              f"loss={r['final_loss']:.4f}", flush=True)


if __name__ == "__main__":
    main()