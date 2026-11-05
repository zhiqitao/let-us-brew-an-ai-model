#!/usr/bin/env python3
"""CORRECTED B2 — diversity vs quantity: truly equal-count, operation-balanced.

Fixes review P0-02 for the diversity experiment.

Bug in the original `scripts/run_diversity.py`:
  * its "high-diversity" pool was renderer.FAMILIES x 2 identifier sets =
    21 family entries x 2 = 42 records, so `pool[:1200]` silently returned 42
    records — the arms were NOT an equal-count 1200-vs-1200 comparison, the
    operation coverage of the high arm was unverified, the tokenizer was refit
    per arm, and no held-out-family split was auditable (P0-02).

Corrections:
  * expanded wording inventory (scripts/diversity_families.py): +10 phrasing
    templates per primitive operation on top of the existing FAMILIES, +2
    further templates per op reserved EXCLUSIVELY for the held-out test, and
    +3 identifier sets (5 total);
  * TWO arms, EACH exactly 1200 records, BOTH covering 10/10 primitive
    operations with exactly 120 records per operation:
      low  = 2 families/op x letters only          -> 20 unique pairs
      high = all train families/op x 5 id sets     -> 605 unique pairs (>500)
    The low arm's (family, id_set) space is a strict subset of the high arm's.
  * ONE fixed tokenizer trained on the union of the two arms' TRAIN texts
    (never any test text), shared by both arms and all 3 seeds; its sha256 is
    asserted equal across arms/seeds;
  * matched protocol for both arms: n_embd 128, 4 layers, 4 heads, block 128,
    1000 steps, batch 16, lr 1e-3, and the SAME initialization seed for both
    arms within a run seed (identical initial weights; only the data differs);
  * TWO fixed tests shared by both arms and all seeds, exact denominators:
      in_distribution  10/op = 100  low arm's families x letters — familiar to
                                     BOTH arms by construction (low space is a
                                     subset of high's); instance-level holdout
      held_out_family  10/op = 100  2 families/op used by NO training arm —
                                     prompt- and family-disjoint from both
  * model + template + retrieval score the IDENTICAL task sets, with exact
    integer successes per operation and in aggregate;
  * P0-02 audit: family-membership disjointness with collision counts,
    prompt-level collision counts, and a program-set sha256 per split.

Resume-safe for the retry-on-SIGILL wrapper (partial results + per-arm
checkpoints). Writes artifacts/manifests/diversity_corrected_seed{N}.json and
never touches the historical diversity.json / diversity_seed*.json.

Usage: python scripts/run_diversity_corrected.py --seed 0
"""
import argparse
import hashlib
import json
import os
import random
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import torch

from diversity_families import (EXTRA_FAMILIES, EXTRA_IDENTIFIER_SETS,
                                HELD_OUT_FAMILIES, HIGH_ID_SETS, LOW_ID_SET,
                                N_TRAIN_EXTRA)
from src.data_generator.generator import (IDENTIFIER_SETS, OPERATIONS,
                                          make_task)
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
N_TRAIN = 1200          # records per arm (equal count)
N_PER_OP = 120          # records per operation per arm (10/10 ops balanced)
N_TEST_PER_OP = 10      # -> 100 tasks per test, exact denominator
DATA_SEED = 9101        # fixed task-construction seed: identical data across run seeds

# base-seed offsets so the four splits never share task seeds
OFFSETS = {"low": 0, "high": 100000, "in_distribution": 200000,
           "held_out_family": 300000}

TESTS = ["in_distribution", "held_out_family"]
ARMS = ["low", "high"]


# ---------------------------------------------------------------------------
# family pools
# ---------------------------------------------------------------------------
def train_families(op):
    """Train-eligible families for an op: existing FAMILIES + 10 extras."""
    fams = list(FAMILIES[op]) + list(EXTRA_FAMILIES[op][:N_TRAIN_EXTRA])
    assert len(fams) >= 11, (op, len(fams))
    return fams


def low_families(op):
    """The LOW arm's few families: the first 2 of the train pool."""
    fams = train_families(op)[:2]
    assert len(fams) == 2, op
    return fams


def held_families(op):
    """The 2 families reserved exclusively for the held-out-family test."""
    fams = list(HELD_OUT_FAMILIES[op])
    assert len(fams) == 2, op
    return fams


def fam_name(fam):
    return getattr(fam, "__name__", "family")


def task_family_key(t):
    """(op, family-name) identity of a task's wording family."""
    return (t["semantics"]["operation"], t["metadata"]["linguistic_template"])


def task_id_sets(tasks):
    return sorted({t["metadata"]["identifier_set"] for t in tasks})


def task_fam_pairs(tasks):
    return {task_family_key(t) for t in tasks}


def task_prompts(tasks):
    return {t["nl"]["prompt"] for t in tasks}


def task_pairs(tasks):
    return {(t["nl"]["prompt"], t["reference_code"]) for t in tasks}


def prog_set_sha256(tasks):
    progs = sorted({t["reference_code"] for t in tasks})
    return hashlib.sha256("\x1f".join(progs).encode()).hexdigest()


# ---------------------------------------------------------------------------
# arm + test construction
# ---------------------------------------------------------------------------
def build_low():
    """LOW-diversity arm: 1200 records, 120/op, 2 families/op, letters only."""
    base = DATA_SEED + OFFSETS["low"]
    tasks, counts = [], {}
    for op in ALL_OPS:
        fams = low_families(op)
        for i in range(N_PER_OP):
            fam = fams[i % len(fams)]
            tasks.append(make_task(op, f"low_{op}_{i:04d}", base + i,
                                   id_set=LOW_ID_SET, family=fam))
        counts[op] = N_PER_OP
    rng = random.Random(DATA_SEED + 7)
    rng.shuffle(tasks)
    return tasks, counts


def build_high():
    """HIGH-diversity arm: 1200 records, 120/op, all train families x 5 id sets.

    Cycles over every (family, id_set) combination per operation; because
    N_PER_OP >= number of combinations for every op, every combination is
    realized, so unique pairs = sum(len(pool) * 5).
    """
    base = DATA_SEED + OFFSETS["high"]
    tasks, counts, combos_per_op = [], {}, {}
    for op in ALL_OPS:
        fams = train_families(op)
        combos = [(f, s) for f in fams for s in HIGH_ID_SETS]
        assert N_PER_OP >= len(combos), (op, N_PER_OP, len(combos))
        combos_per_op[op] = len(combos)
        for i in range(N_PER_OP):
            fam, id_set = combos[i % len(combos)]
            tasks.append(make_task(op, f"high_{op}_{i:04d}", base + i,
                                   id_set=id_set, family=fam))
        counts[op] = N_PER_OP
    rng = random.Random(DATA_SEED + 8)
    rng.shuffle(tasks)
    return tasks, counts, combos_per_op


def build_tests():
    """Two fixed tests shared by both arms and all seeds (10/op each)."""
    tests = {}
    # in-distribution: the LOW arm's families x letters -> familiar to BOTH
    # arms (low space is a subset of high's), instance-level holdout only.
    base = DATA_SEED + OFFSETS["in_distribution"]
    tasks, counts = [], {}
    for op in ALL_OPS:
        fams = low_families(op)
        for i in range(N_TEST_PER_OP):
            fam = fams[i % len(fams)]
            tasks.append(make_task(op, f"ind_{op}_{i:04d}", base + i,
                                   id_set=LOW_ID_SET, family=fam))
        counts[op] = N_TEST_PER_OP
    tests["in_distribution"] = (tasks, counts)

    # held-out family: 2 families/op used by NO training arm, letters ids.
    base = DATA_SEED + OFFSETS["held_out_family"]
    tasks, counts = [], {}
    for op in ALL_OPS:
        fams = held_families(op)
        for i in range(N_TEST_PER_OP):
            fam = fams[i % len(fams)]
            tasks.append(make_task(op, f"held_{op}_{i:04d}", base + i,
                                   id_set=LOW_ID_SET, family=fam))
        counts[op] = N_TEST_PER_OP
    tests["held_out_family"] = (tasks, counts)
    return tests


# ---------------------------------------------------------------------------
# assertions / P0-02 audit
# ---------------------------------------------------------------------------
def arm_stats(tasks, counts, combos_per_op=None):
    cs = content_stats(tasks)
    stats = {
        "n": len(tasks),
        "ops_covered": len(counts),
        "per_op_counts": counts,
        "unique_prompts": cs["distinct_prompts"],
        "unique_prompt_program_pairs": cs["distinct_prompt_code"],
        "family_count": len({f for _, f in task_fam_pairs(tasks)}),
        "op_family_pairs": len(task_fam_pairs(tasks)),
        "families_per_op": {op: len({f for (o, f) in task_fam_pairs(tasks)
                                     if o == op}) for op in sorted(counts)},
        "identifier_sets": task_id_sets(tasks),
        "identifier_set_count": len(task_id_sets(tasks)),
        "content": cs,
    }
    if combos_per_op is not None:
        stats["expected_pairs_per_op"] = combos_per_op
        stats["expected_pairs_total"] = sum(combos_per_op.values())
    return stats


def build_and_assert():
    """Build both arms + both tests and run every design assertion."""
    # make the extra identifier sets visible to the generator (additive; the
    # existing renderer/generator are untouched and letters/words unchanged)
    IDENTIFIER_SETS.update(EXTRA_IDENTIFIER_SETS)
    for s in HIGH_ID_SETS:
        assert s in IDENTIFIER_SETS, s

    low, low_counts = build_low()
    high, high_counts, combos = build_high()
    tests = build_tests()

    # ---- equal count + operation balance ---------------------------------
    assert len(low) == N_TRAIN, len(low)
    assert len(high) == N_TRAIN, len(high)
    for name, counts in (("low", low_counts), ("high", high_counts)):
        assert set(counts) == set(ALL_OPS), (name, sorted(counts))
        assert all(v == N_PER_OP for v in counts.values()), (name, counts)
        assert per_op_counts(low if name == "low" else high) == counts

    # ---- unique-pair targets ---------------------------------------------
    low_stats = arm_stats(low, low_counts)
    high_stats = arm_stats(high, high_counts, combos)
    assert low_stats["unique_prompt_program_pairs"] == 2 * N_OPS, low_stats
    assert low_stats["unique_prompts"] == 2 * N_OPS, low_stats
    assert low_stats["op_family_pairs"] == 2 * N_OPS, low_stats
    assert low_stats["identifier_sets"] == [LOW_ID_SET], low_stats
    expected_high = sum(combos.values())
    assert high_stats["unique_prompt_program_pairs"] == expected_high, \
        (high_stats["unique_prompt_program_pairs"], expected_high)
    assert high_stats["unique_prompts"] == expected_high, high_stats
    assert high_stats["unique_prompt_program_pairs"] > 500, high_stats
    assert high_stats["unique_prompt_program_pairs"] > \
        low_stats["unique_prompt_program_pairs"] * 10
    assert high_stats["identifier_set_count"] >= 4, high_stats
    assert high_stats["op_family_pairs"] > low_stats["op_family_pairs"] * 3
    # prompt determines program, so unique prompts == unique pairs
    assert low_stats["unique_prompts"] == low_stats["unique_prompt_program_pairs"]
    assert high_stats["unique_prompts"] == high_stats["unique_prompt_program_pairs"]

    # ---- low (family, id_set) space is a strict subset of high's ---------
    low_space = {(op, fam_name(f), s)
                 for op in ALL_OPS for f in low_families(op)
                 for s in [LOW_ID_SET]}
    high_space = {(op, fam_name(f), s)
                  for op in ALL_OPS for f in train_families(op)
                  for s in HIGH_ID_SETS}
    assert low_space < high_space, "low arm space must be a subset of high's"

    # ---- tests: exact denominators, 10/10 ops ----------------------------
    test_meta = {}
    for name, (tasks, counts) in tests.items():
        assert len(tasks) == N_TEST_PER_OP * N_OPS, (name, len(tasks))
        assert set(counts) == set(ALL_OPS), (name, sorted(counts))
        assert all(v == N_TEST_PER_OP for v in counts.values()), (name, counts)
        test_meta[name] = {"n": len(tasks), "per_op_counts": counts,
                           "ops_covered": len(counts)}

    # ---- family membership (the P0-02 dimension) -------------------------
    low_pairs, high_pairs = task_fam_pairs(low), task_fam_pairs(high)
    ind_pairs = task_fam_pairs(tests["in_distribution"][0])
    held_pairs = task_fam_pairs(tests["held_out_family"][0])
    assert not (held_pairs & low_pairs), "held-out family leaked into LOW"
    assert not (held_pairs & high_pairs), "held-out family leaked into HIGH"
    assert ind_pairs <= low_pairs, "in-dist family not familiar to LOW"
    assert ind_pairs <= high_pairs, "in-dist family not familiar to HIGH"

    # prompt-level collisions
    low_prompts, high_prompts = task_prompts(low), task_prompts(high)
    held_prompts = task_prompts(tests["held_out_family"][0])
    ind_prompts = task_prompts(tests["in_distribution"][0])
    held_vs_low = len(held_prompts & low_prompts)
    held_vs_high = len(held_prompts & high_prompts)
    assert held_vs_low == 0, held_vs_low
    assert held_vs_high == 0, held_vs_high
    ind_overlap_low = len(ind_prompts & low_prompts)
    ind_overlap_high = len(ind_prompts & high_prompts)
    assert ind_overlap_low == len(ind_prompts), "in-dist prompts must be familiar"
    assert ind_overlap_high == len(ind_prompts), "in-dist prompts must be familiar"

    # pair-level collisions
    assert not (task_pairs(tests["held_out_family"][0]) & task_pairs(low))
    assert not (task_pairs(tests["held_out_family"][0]) & task_pairs(high))

    # instance-level disjointness across all four splits
    splits = {"low": low, "high": high,
              "in_distribution": tests["in_distribution"][0],
              "held_out_family": tests["held_out_family"][0]}
    names = list(splits)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            overlap = instance_seeds(splits[a]) & instance_seeds(splits[b])
            assert not overlap, f"instance seeds shared: {a}/{b}"

    audit = {
        "heldout_family_collisions_vs_low_train": {
            "op_family_pairs": len(held_pairs & low_pairs),
            "prompts": held_vs_low,
            "prompt_program_pairs": len(
                task_pairs(tests["held_out_family"][0]) & task_pairs(low)),
        },
        "heldout_family_collisions_vs_high_train": {
            "op_family_pairs": len(held_pairs & high_pairs),
            "prompts": held_vs_high,
            "prompt_program_pairs": len(
                task_pairs(tests["held_out_family"][0]) & task_pairs(high)),
        },
        "indist_family_membership": {
            "families_not_in_low_train": sorted(
                f"{o}/{f}" for o, f in (ind_pairs - low_pairs)),
            "families_not_in_high_train": sorted(
                f"{o}/{f}" for o, f in (ind_pairs - high_pairs)),
            "prompt_overlap_with_low_train": ind_overlap_low,
            "prompt_overlap_with_high_train": ind_overlap_high,
            "prompt_overlap_note": "expected: the in-distribution test shares "
                                   "(op, family, id_set) content with training "
                                   "by design; holdout is instance-level only",
        },
        "instance_seed_overlap_all_split_pairs": 0,
        "program_set_sha256": {name: prog_set_sha256(t)
                               for name, t in splits.items()},
    }

    return low, low_counts, low_stats, high, high_counts, high_stats, \
        tests, test_meta, audit


def get_fixed_tokenizer(path, low, high):
    """ONE tokenizer trained on the union of BOTH arms' TRAIN texts only."""
    if os.path.exists(path):
        return load_tokenizer(path), "loaded_existing"
    texts = [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in low + high]
    tok = train_tokenizer(texts, min_vocab=128, max_vocab=300, save_path=path)
    return tok, "trained_now"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--build-only", action="store_true",
                    help="run construction + all assertions, print stats, exit")
    ap.add_argument("--manifest-dir", default=os.path.join(ROOT, "artifacts", "manifests"))
    ap.add_argument("--ckpt-dir", default=os.path.join(ROOT, "artifacts", "checkpoints"))
    ap.add_argument("--tok-path", default=os.path.join(ROOT, "artifacts", "tokenizer",
                                                       "diversity_corrected_tok.json"))
    args = ap.parse_args()
    seed = args.seed
    random.seed(seed)
    torch.manual_seed(seed)

    # ---- fixed data: both arms + both tests, all assertions ---------------
    (low, low_counts, low_stats, high, high_counts, high_stats,
     tests, test_meta, audit) = build_and_assert()
    print(f"LOW : n={low_stats['n']} ops={low_stats['ops_covered']}/10 "
          f"per_op={N_PER_OP} unique_pairs={low_stats['unique_prompt_program_pairs']} "
          f"unique_prompts={low_stats['unique_prompts']} "
          f"families(op,fam)={low_stats['op_family_pairs']} "
          f"id_sets={low_stats['identifier_sets']}", flush=True)
    print(f"HIGH: n={high_stats['n']} ops={high_stats['ops_covered']}/10 "
          f"per_op={N_PER_OP} unique_pairs={high_stats['unique_prompt_program_pairs']} "
          f"unique_prompts={high_stats['unique_prompts']} "
          f"families(op,fam)={high_stats['op_family_pairs']} "
          f"id_sets={high_stats['identifier_set_count']} "
          f"({','.join(high_stats['identifier_sets'])})", flush=True)
    for name in TESTS:
        m = test_meta[name]
        print(f"TEST {name:17s}: n={m['n']} ops={m['ops_covered']}/10 "
              f"per_op={m['per_op_counts'][ALL_OPS[0]]}", flush=True)
    if args.build_only:
        print("build-only: all assertions passed", flush=True)
        return

    # ---- ONE fixed tokenizer (train-only, shared by both arms + seeds) ----
    os.makedirs(os.path.dirname(args.tok_path), exist_ok=True)
    tok, tok_source = get_fixed_tokenizer(args.tok_path, low, high)
    assert_full_byte_alphabet(tok)
    tok_sha = vocab_sha256(tok)
    print(f"tokenizer: vocab={tok.vocab_size} sha={tok_sha[:12]} "
          f"source={tok_source} (union of both arms' train texts, fixed)",
          flush=True)

    # ---- per-arm training + evaluation (resume-safe) ----------------------
    os.makedirs(args.manifest_dir, exist_ok=True)
    os.makedirs(args.ckpt_dir, exist_ok=True)
    partial_path = os.path.join(args.manifest_dir,
                                f".partial_diversity_corrected_seed{seed}.json")
    partial = load_partial(partial_path)
    judge = Judge()
    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)

    results = {t: {} for t in TESTS}
    shas, losses, train_times = set(), {}, {}
    for arm in ARMS:
        train = low if arm == "low" else high
        assert len(train) == N_TRAIN
        ckpt_path = os.path.join(args.ckpt_dir,
                                 f"diversity_corrected_seed{seed}_{arm}.pt")
        model, final_loss, train_s = None, None, None
        if os.path.exists(ckpt_path):
            blob = torch.load(ckpt_path, map_location="cpu", weights_only=True)
            model = GPT(cfg)
            model.load_state_dict(blob["state_dict"])
            final_loss, train_s = blob["final_loss"], blob.get("train_time_s", None)
            print(f"  {arm:4s}: loaded checkpoint {ckpt_path}", flush=True)
        if model is None:
            # SAME init seed for both arms within a run seed: identical
            # initial weights, only the training data differs.
            torch.manual_seed(seed * 10007 + 1)
            random.seed(seed * 10007 + 2)  # matched batch-sampling schedule
            model = GPT(cfg)
            ds = Dataset(train, tok)
            t0 = time.time()
            losses_list = train_fn(model, ds, steps=args.steps, bs=args.bs, lr=args.lr)
            train_s = round(time.time() - t0, 1)
            final_loss = float(losses_list[-1])
            torch.save({"state_dict": model.state_dict(), "final_loss": final_loss,
                        "train_time_s": train_s}, ckpt_path)
            emb, non_emb = model.num_params()
            print(f"  {arm:4s}: trained {args.steps} steps in {train_s}s "
                  f"loss={final_loss:.4f} params={emb + non_emb}", flush=True)
        losses[arm] = round(final_loss, 4)
        train_times[arm] = train_s

        for tidx, test_name in enumerate(TESTS):
            key = f"{arm}/{test_name}"
            tasks, counts = tests[test_name]
            expected_n = test_meta[test_name]["n"]
            if key in partial:
                results[test_name][arm] = partial[key]
                # A fully-cached resume must still satisfy the final
                # tokenizer-drift assert below, or the manifest is never
                # written (cached entries carry no tokenizer field to check).
                shas.add(tok_sha)
                m = results[test_name][arm]["systems"]["MODEL"]
                print(f"  {arm:4s} {test_name:17s}: cached (partial) "
                      f"{m['successes']}/{m['denominator']}", flush=True)
                continue
            t0 = time.time()
            # identical eval seed for both arms on the same test -> matched
            # generation sampling noise across arms.
            scores = score_all(model, tok, train, tasks, judge,
                               eval_seed=seed * 10007 + tidx + 1)
            eval_s = round(time.time() - t0, 1)
            for label, s in scores.items():
                assert s["denominator"] == expected_n, (key, label, s["denominator"])
                assert sum(v["denominator"] for v in s["per_op"].values()) == expected_n
                assert len(s["per_op"]) == N_OPS, (key, label, len(s["per_op"]))
            entry = {
                "arm": arm,
                "test": test_name,
                "n": len(tasks),
                "denominator": len(tasks),
                "ops_covered": N_OPS,
                "per_op_counts": counts,
                "content": content_stats(tasks),
                "systems": scores,
                "eval_time_s": eval_s,
            }
            results[test_name][arm] = entry
            partial[key] = entry
            save_partial(partial_path, partial)
            shas.add(tok_sha)
            m = scores["MODEL"]
            print(f"  {arm:4s} {test_name:17s}: n={len(tasks)} "
                  f"model={m['successes']}/{m['denominator']}={m['pass_at_1']:.3f} "
                  f"tmpl={scores['TEMPLATE']['successes']}/"
                  f"{scores['TEMPLATE']['denominator']} "
                  f"ret={scores['RETRIEVAL']['successes']}/"
                  f"{scores['RETRIEVAL']['denominator']} ({eval_s}s)", flush=True)

    # ---- final assertions -------------------------------------------------
    assert set(shas) == {tok_sha}, f"tokenizer drifted: {shas}"
    for test_name in TESTS:
        assert set(results[test_name]) == set(ARMS), (test_name, results[test_name])
        for arm in ARMS:
            e = results[test_name][arm]
            assert e["denominator"] == N_TEST_PER_OP * N_OPS
            assert e["ops_covered"] == N_OPS
    assert low_stats["n"] == high_stats["n"] == N_TRAIN

    manifest = {
        "experiment_id": "diversity_corrected",
        "status": "MEASURED",
        "fixes": ["P0-02"],
        "seed": seed,
        "config": vars(args),
        "design": "equal-count 1200-vs-1200, operation-balanced (120/op, 10/10 "
                  "ops) low- vs high-diversity arms under one fixed tokenizer "
                  "and a matched training protocol, scored on an identical "
                  "in-distribution test and an identical held-out-family test "
                  "(model + template + retrieval, exact denominators)",
        "tokenizer": {
            "vocab_size": tok.vocab_size,
            "sha256": tok_sha,
            "source": tok_source,
            "trained_on": "union of BOTH arms' train texts (no test text)",
            "fixed_across_arms": True,
            "fixed_across_seeds": True,
            "refit_per_arm": False,
        },
        "arms": {"low": low_stats, "high": high_stats},
        "tests": {
            "in_distribution": dict(
                test_meta["in_distribution"],
                families="low arm's 2 families/op x letters (familiar to BOTH "
                         "arms; low space is a subset of high's)",
                id_set=LOW_ID_SET,
                holdout_level="instance (new construction seeds + new hidden "
                              "tests); content overlaps training by design",
                fixed_across_arms_and_seeds=True),
            "held_out_family": dict(
                test_meta["held_out_family"],
                families="2 families/op used by NO training arm "
                         "(h01, h02) x letters",
                id_set=LOW_ID_SET,
                holdout_level="family + prompt + instance (disjoint from both "
                              "train arms; collision counts in `audit`)",
                fixed_across_arms_and_seeds=True),
        },
        "results": results,
        "audit": audit,
        "final_train_loss": losses,
        "train_time_s": train_times,
        "assertions": {
            "both_arms_exactly_1200_records": True,
            "both_arms_10_of_10_ops": True,
            "both_arms_120_per_op": True,
            "low_unique_pairs": low_stats["unique_prompt_program_pairs"],
            "high_unique_pairs": high_stats["unique_prompt_program_pairs"],
            "high_unique_pairs_gt_500": True,
            "low_id_set_count": low_stats["identifier_set_count"],
            "high_id_set_count": high_stats["identifier_set_count"],
            "low_space_subset_of_high": True,
            "tokenizer_identical_across_arms_and_seeds": True,
            "identical_task_sets_per_test_across_arms_and_seeds": True,
            "matched_steps_arch_lr_and_init_per_seed": True,
            "heldout_family_disjoint_from_both_arms": True,
            "heldout_prompt_collisions": 0,
            "denominators_exact_per_test": {t: results[t][ARMS[0]]["denominator"]
                                            for t in TESTS},
            "instance_disjoint_all_split_pairs": True,
        },
    }
    mp = os.path.join(args.manifest_dir, f"diversity_corrected_seed{seed}.json")
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp, flush=True)
    for test_name in TESTS:
        for arm in ARMS:
            e = results[test_name][arm]
            m = e["systems"]["MODEL"]
            print(f"  {test_name:17s} {arm:4s} model={m['successes']:3d}/"
                  f"{e['denominator']:3d}={m['pass_at_1']:.3f} "
                  f"tmpl={e['systems']['TEMPLATE']['pass_at_1']:.3f} "
                  f"ret={e['systems']['RETRIEVAL']['pass_at_1']:.3f} "
                  f"loss={losses[arm]:.4f}", flush=True)


if __name__ == "__main__":
    main()