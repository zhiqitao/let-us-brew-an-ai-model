#!/usr/bin/env python3
"""CORRECTED B3 — surface 2x2 factorial: identifier x wording family.

Fixes P0-03 (mixed factors) and P0-04 (wrong denominator).

Bugs in the original `scripts/run_surface.py`:
  * P0-03: the "new IDENTIFIERS" test built tasks with id_set="words" AND
    families="all", so the identifier arm also changed the wording mix — the
    two factors were confounded.
  * P0-04: held-out-wording results were reported against a denominator that
    did not match the realized task set (operations with a single template
    family contribute no held-out tasks).

Corrected design — ONE fixed training set (letters x kept families, balanced
10/10 ops), ONE fixed tokenizer trained on train-only data, then the SAME
trained model plus TEMPLATE and RETRIEVAL baselines score the IDENTICAL task
set of each factorial cell:

    cell          identifier   wording        ops   expected n (n_per=60)
    familiar      letters      kept families  10    600
    id_only       words        kept families  10    600
    wording_only  letters      held-out fam     8    480
    combined      words        held-out fam     8    480

abs_of and cond_abs_max have exactly one template family, so they have NO
held-out family: they are excluded from the held-out cells and flagged
explicitly (excluded_ops). Every cell reports exact integer successes over
its exact denominator (e.g. 420/480), per operation and in aggregate, for
model + template + retrieval.

Task construction uses a fixed data seed (identical across run seeds); only
the torch/python seeds vary per run seed. Resume-safe for the retry-on-SIGILL
wrapper (partial results + model checkpoint).

Usage: python scripts/run_surface_corrected.py --seed 0
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

from src.data_generator.generator import OPERATIONS, make_task
from src.evaluator.evaluator import Judge
from src.model.gpt import Config, GPT
from src.nl_renderer.renderer import FAMILIES
from src.tokenizer.tokenizer import load_tokenizer, train_tokenizer
from src.train.trainer import Dataset, train as train_fn

from corrected_common import (assert_full_byte_alphabet, content_stats,
                              instance_seeds, load_partial, per_op_counts,
                              save_partial, score_all, vocab_sha256)

ROOT = os.path.join(_HERE, "..")
ALL_OPS = list(OPERATIONS)
N_OPS = len(ALL_OPS)
DATA_SEED = 9001  # fixed task-construction seed: identical data across run seeds

# base-seed offsets so train and the four cells never share task seeds
OFFSETS = {"train": 0, "familiar": 100000, "id_only": 200000,
           "wording_only": 300000, "combined": 400000}

CELLS = {
    # cell -> (id_set, wording)
    "familiar": ("letters", "kept"),
    "id_only": ("words", "kept"),
    "wording_only": ("letters", "heldout"),
    "combined": ("words", "heldout"),
}


def split_families(op):
    """(kept, held) template families for an operation.

    Operations with a single family (abs_of, cond_abs_max) have NO held-out
    family: kept = that family, held = [].
    """
    fams = list(FAMILIES[op])
    if len(fams) <= 1:
        return fams, []
    return fams[:-1], [fams[-1]]


def build_cell(cell, n_per, prefix):
    """Build one factorial cell's tasks (balanced n_per per included op)."""
    id_set, wording = CELLS[cell]
    base = DATA_SEED + OFFSETS[cell]
    tasks, counts, excluded = [], {}, []
    for op in ALL_OPS:
        kept, held = split_families(op)
        chosen = kept if wording == "kept" else held
        if not chosen:
            excluded.append(op)
            continue
        for i in range(n_per):
            fam = chosen[i % len(chosen)]
            tasks.append(make_task(op, f"{prefix}_{op}_{i:04d}", base + i,
                                   id_set=id_set, family=fam))
        counts[op] = n_per
    return tasks, counts, excluded


def build_train(n_per):
    base = DATA_SEED + OFFSETS["train"]
    tasks, counts = [], {}
    for op in ALL_OPS:
        kept, _ = split_families(op)
        assert kept, op
        for i in range(n_per):
            fam = kept[i % len(kept)]
            tasks.append(make_task(op, f"train_{op}_{i:04d}", base + i,
                                   id_set="letters", family=fam))
        counts[op] = n_per
    return tasks, counts


def get_fixed_tokenizer(path, train_tasks):
    """ONE tokenizer trained on TRAIN-ONLY data, shared by every cell/seed."""
    if os.path.exists(path):
        return load_tokenizer(path), "loaded_existing"
    texts = [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in train_tasks]
    tok = train_tokenizer(texts, min_vocab=128, max_vocab=300, save_path=path)
    return tok, "trained_now"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--n-per", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--manifest-dir", default=os.path.join(ROOT, "artifacts", "manifests"))
    ap.add_argument("--ckpt-dir", default=os.path.join(ROOT, "artifacts", "checkpoints"))
    ap.add_argument("--tok-path", default=os.path.join(ROOT, "artifacts", "tokenizer",
                                                       "surface_corrected_tok.json"))
    args = ap.parse_args()
    seed = args.seed
    n_per = args.n_per
    random.seed(seed)
    torch.manual_seed(seed)

    # ---- fixed data: train + 4 cells --------------------------------------
    train, train_counts = build_train(n_per)
    assert len(train) == n_per * N_OPS
    assert set(train_counts) == set(ALL_OPS) and all(v == n_per
                                                     for v in train_counts.values())
    cells, cell_meta = {}, {}
    for cell in CELLS:
        tasks, counts, excluded = build_cell(cell, n_per, cell)
        expected_ops = N_OPS if CELLS[cell][1] == "kept" else N_OPS - 2
        if CELLS[cell][1] == "heldout":
            assert excluded == ["abs_of", "cond_abs_max"], excluded
        else:
            assert excluded == [], excluded
        assert len(tasks) == n_per * expected_ops, (cell, len(tasks))
        assert len(counts) == expected_ops
        assert set(counts) == set(ALL_OPS) - set(excluded)
        if cell == "familiar":
            # In-distribution cell: shares the (op, family, id_set) content
            # space with training BY DESIGN (prompt+code are deterministic in
            # those three), so the holdout is instance-level only.
            assert not (instance_seeds(train) & instance_seeds(tasks)), \
                "familiar cell reuses training instances"
        else:
            # Shifted cells must never reuse a training prompt.
            train_prompts = {t["nl"]["prompt"] for t in train}
            overlap = train_prompts & {t["nl"]["prompt"] for t in tasks}
            assert not overlap, f"{cell}: {len(overlap)} prompts seen in training"
        cells[cell] = tasks
        cell_meta[cell] = {"counts": counts, "excluded": excluded,
                           "expected_ops": expected_ops}
    # cells must also be disjoint from each other (different base seeds)
    keys = {c: {(t["nl"]["prompt"], t["reference_code"]) for t in cells[c]}
            for c in cells}
    for a in cells:
        for b in cells:
            if a < b:
                assert not (keys[a] & keys[b]), f"cell overlap {a}/{b}"

    # ---- ONE fixed tokenizer (train-only) ---------------------------------
    os.makedirs(os.path.dirname(args.tok_path), exist_ok=True)
    tok, tok_source = get_fixed_tokenizer(args.tok_path, train)
    assert_full_byte_alphabet(tok)
    tok_sha = vocab_sha256(tok)
    print(f"tokenizer: vocab={tok.vocab_size} sha={tok_sha[:12]} source={tok_source} "
          f"(train-only, fixed)", flush=True)

    # ---- train ONE model per seed -----------------------------------------
    os.makedirs(args.manifest_dir, exist_ok=True)
    os.makedirs(args.ckpt_dir, exist_ok=True)
    partial_path = os.path.join(args.manifest_dir,
                                f".partial_surface_corrected_seed{seed}.json")
    partial = load_partial(partial_path)
    ckpt_path = os.path.join(args.ckpt_dir, f"surface_corrected_seed{seed}.pt")
    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)

    model, final_loss, train_s = None, None, None
    if os.path.exists(ckpt_path):
        blob = torch.load(ckpt_path, map_location="cpu", weights_only=True)
        model = GPT(cfg)
        model.load_state_dict(blob["state_dict"])
        final_loss, train_s = blob["final_loss"], blob.get("train_time_s", None)
        print(f"loaded checkpoint {ckpt_path}", flush=True)
    if model is None:
        torch.manual_seed(seed)
        model = GPT(cfg)
        emb, non_emb = model.num_params()
        ds = Dataset(train, tok)
        t0 = time.time()
        losses = train_fn(model, ds, steps=args.steps, bs=args.bs, lr=args.lr)
        train_s = round(time.time() - t0, 1)
        final_loss = float(losses[-1])
        torch.save({"state_dict": model.state_dict(), "final_loss": final_loss,
                    "train_time_s": train_s}, ckpt_path)
        print(f"trained {args.steps} steps in {train_s}s final_loss={final_loss:.4f} "
              f"params={emb + non_emb}", flush=True)

    # ---- score every cell (resume-safe) -----------------------------------
    judge = Judge()
    conditions = {}
    for idx, cell in enumerate(["familiar", "id_only", "wording_only", "combined"]):
        tasks = cells[cell]
        meta = cell_meta[cell]
        expected_n = n_per * meta["expected_ops"]
        assert len(tasks) == expected_n
        if str(cell) in partial:
            conditions[cell] = partial[str(cell)]
            print(f"  {cell:14s}: cached (partial) "
                  f"{conditions[cell]['systems']['MODEL']['successes']}/{expected_n}",
                  flush=True)
            continue
        t0 = time.time()
        scores = score_all(model, tok, train, tasks, judge,
                           eval_seed=seed * 10007 + idx + 1)
        eval_s = round(time.time() - t0, 1)
        for label, s in scores.items():
            assert s["denominator"] == expected_n, (cell, label, s["denominator"])
            assert sum(v["denominator"] for v in s["per_op"].values()) == expected_n
        entry = {
            "id_set": CELLS[cell][0],
            "wording": CELLS[cell][1],
            "n": len(tasks),
            "denominator": len(tasks),
            "ops_covered": meta["expected_ops"],
            "ops": sorted(meta["counts"]),
            "excluded_ops": meta["excluded"],
            "per_op_counts": meta["counts"],
            "content": content_stats(tasks),
            "systems": scores,
            "eval_time_s": eval_s,
        }
        if meta["excluded"]:
            entry["denominator_note"] = (
                "excluded ops have a single template family, so no held-out "
                "family exists: " + ", ".join(meta["excluded"]))
        conditions[cell] = entry
        partial[str(cell)] = entry
        save_partial(partial_path, partial)
        m = scores["MODEL"]
        print(f"  {cell:14s}: n={len(tasks)} model={m['successes']}/{m['denominator']}"
              f"={m['pass_at_1']:.3f} tmpl={scores['TEMPLATE']['successes']}"
              f"/{scores['TEMPLATE']['denominator']} "
              f"ret={scores['RETRIEVAL']['successes']}"
              f"/{scores['RETRIEVAL']['denominator']} ({eval_s}s)", flush=True)

    assert set(conditions) == set(CELLS)
    assert conditions["familiar"]["denominator"] == n_per * N_OPS
    assert conditions["id_only"]["denominator"] == n_per * N_OPS
    assert conditions["wording_only"]["denominator"] == n_per * (N_OPS - 2)
    assert conditions["combined"]["denominator"] == n_per * (N_OPS - 2)

    manifest = {
        "experiment_id": "surface_corrected",
        "status": "MEASURED",
        "fixes": ["P0-03", "P0-04"],
        "seed": seed,
        "config": vars(args),
        "design": "2x2 factorial: identifier (letters|words) x wording (kept|held-out), "
                  "one fixed train set + one fixed tokenizer, identical task sets "
                  "scored by model + template + retrieval",
        "tokenizer": {"vocab_size": tok.vocab_size, "sha256": tok_sha,
                      "source": tok_source,
                      "trained_on": "train-only texts (letters x kept families)",
                      "fixed_across_cells": True, "fixed_across_seeds": True,
                      "refit_per_cell": False},
        "train_set": {"n": len(train), "per_op_counts": train_counts,
                      "ops_covered": len(train_counts), "id_set": "letters",
                      "wording": "kept families", "data_seed": DATA_SEED,
                      "n_per_op": n_per, "content": content_stats(train)},
        "data_seed": DATA_SEED,
        "final_train_loss": round(final_loss, 4),
        "train_time_s": train_s,
        "conditions": conditions,
        "assertions": {
            "train_covers_10_of_10_ops": True,
            "train_balanced_per_op": True,
            "heldout_cells_exclude_single_family_ops": ["abs_of", "cond_abs_max"],
            "denominators_exact_per_cell": {c: conditions[c]["denominator"]
                                            for c in conditions},
            "identical_task_sets_across_systems": True,
            "tokenizer_train_only_and_fixed": True,
            "train_cell_instance_disjoint": True,
            "shifted_cells_prompt_disjoint_from_train": ["id_only", "wording_only",
                                                         "combined"],
            "familiar_cell_content_overlap_with_train": "expected (in-distribution "
                                                       "cell; instance-level "
                                                       "holdout only)",
        },
    }
    mp = os.path.join(args.manifest_dir, f"surface_corrected_seed{seed}.json")
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp, flush=True)
    for cell, e in conditions.items():
        m = e["systems"]["MODEL"]
        print(f"  {cell:14s} {m['successes']:4d}/{e['denominator']:4d} "
              f"= {m['pass_at_1']:.3f} (ops={e['ops_covered']}, "
              f"excluded={e['excluded_ops']})", flush=True)


if __name__ == "__main__":
    main()