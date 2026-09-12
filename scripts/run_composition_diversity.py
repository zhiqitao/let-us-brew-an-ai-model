#!/usr/bin/env python3
"""Composition STRUCTURAL-DIVERSITY experiment.

Follows up on composition exposure: naive exposure to a few composites did NOT unlock
composition on unseen ones (run_composition_exposure.py -> held-out 0.000). This tests
the stronger hypothesis the reviews flag: is composition like SURFACE robustness, i.e.
is it a DIVERSITY question rather than a quantity question?

Setup: primitives + a broad set of composite operations in training, but ONE composite
operation is HELD OUT entirely. Two diversity conditions on the exposure set (same
example count each):
  - minimal_diversity: few phrasings, one id-set (letters)
  - high_diversity  : many phrasings, BOTH id-sets (letters + words)
Test on: in-dist primitives, exposed composites, and the HELD-OUT composite op.
If high diversity exposes a general compose-operator that transfers to the held-out op,
composition is a diversity lever. If not, the wall is structural regardless of diversity.

Run: TORCH_DISABLE_AVX2=1 python scripts/run_composition_diversity.py
"""
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from collections import defaultdict
from src.data_generator.generator import generate_dataset, make_task, COMPOSITE_OPERATIONS
from src.model.gpt import GPT, Config
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge

ROOT = os.path.join(os.path.dirname(__file__), "..")
ID_SETS = ["letters", "words"]
# one composite op never seen at all (the transfer test)
HELD_OUT_OP = "len_minus_one"
# the composite ops used for the exposure set (diverse surface)
EXPOSED_OPS = [op for op in COMPOSITE_OPERATIONS if op != HELD_OUT_OP]


def main():
    import argparse
    from src.train.trainer import Dataset, train as train_fn
    from src.tokenizer.tokenizer import train_tokenizer
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-per-op", type=int, default=200)
    ap.add_argument("--comp-n", type=int, default=30)   # per family per id-set
    ap.add_argument("--exposed-budget", type=int, default=120)  # same count both modes
    ap.add_argument("--out", default=os.path.join(ROOT, "artifacts", "checkpoints"))
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    # ---- primitives: train/val/test (same split as run_composition) ----
    prim = generate_dataset(n_per_op=args.n_per_op, id_set="letters", seed=args.seed)
    by_op = defaultdict(list)
    for t in prim:
        by_op[t["semantics"]["operation"]].append(t)
    train_p, val, test = [], [], []
    for op, g in by_op.items():
        g.sort(key=lambda t: t["task_id"])
        n = len(g); nv = max(1, int(n*0.15)); nt = max(1, int(n*0.15))
        val += g[:nv]; test += g[nv:nv+nt]; train_p += g[nv+nt:]

    # ---- build a diverse POOL of exposed composites (many fams x both id-sets) ----
    # Track id_set explicitly (make_task sets it, but nl doesn't store the key).
    def build_exposed_pool():
        pool = []
        for op in EXPOSED_OPS:
            for id_set in ID_SETS:
                for i in range(args.comp_n):
                    t = make_task(op, f"{op}_{id_set}_{i}", seed=4000 + len(pool),
                                  id_set=id_set)
                    t["_id_set"] = id_set
                    pool.append(t)
        return pool
    pool = build_exposed_pool()

    def sample_pool(mode):
        import random
        rng = random.Random(args.seed + 1)
        if mode == "high_diversity":
            # expose a broad spread: multiple ops, BOTH id-sets
            return rng.sample(pool, min(args.exposed_budget, len(pool)))
        else:  # minimal: letters id-set only, duplicated to the same budget
            narrow = [t for t in pool if t.get("_id_set") == "letters"]
            if len(narrow) < args.exposed_budget:
                narrow = (narrow * (args.exposed_budget // max(1, len(narrow)) + 1))[:args.exposed_budget]
            return rng.sample(narrow, min(args.exposed_budget, len(narrow)))

    # ---- held-out composite (transfer test) ----
    heldout = [make_task(HELD_OUT_OP, f"{HELD_OUT_OP}_{i:04d}", 9000 + i, id_set="letters")
               for i in range(40)]

    for t in train_p: t["split"] = "train"
    for t in val: t["split"] = "val"
    for t in test: t["split"] = "test"
    for t in heldout: t["split"] = "composition_holdout"

    results = {}
    for mode in ["minimal_diversity", "high_diversity"]:
        exposed = sample_pool(mode)
        for t in exposed: t["split"] = "train"
        train_all = train_p + exposed
        print(f"\n##### {mode}: exposed {len(exposed)} composites #####")
        print(f"  exposed ops: {EXPOSED_OPS}")
        print(f"  held-out op: {HELD_OUT_OP}")

        all_texts = ([t["nl"]["prompt"] + "\n" + t["reference_code"] for t in train_all] +
                     [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in heldout] +
                     [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in val] +
                     [t["nl"]["prompt"] + "\n" + t["reference_code"] for t in test])
        tok = train_tokenizer(all_texts, min_vocab=128, max_vocab=300,
                              save_path=os.path.join(ROOT, "artifacts", "tokenizer", "comp_tok.json"))
        cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                     n_head=args.n_head, block_size=128)
        m = GPT(cfg)
        ds = Dataset(train_all, tok)
        t0 = time.time()
        losses = train_fn(m, ds, steps=args.steps, bs=16, lr=1e-3)
        print(f"  trained {len(train_all)} tasks in {time.time()-t0:.0f}s; final loss {losses[-1]:.4f}")

        ckpt = os.path.join(args.out, f"stage4_compdiv_{mode}{args.tag}.pt")
        torch.save(m.state_dict(), ckpt)
        judge = Judge()

        def show(name, tasks):
            r = evaluate_all(m, tok, train_all, tasks, judge)
            for rr in r:
                print(f"    {rr['label']:9s} {name:22s} pass@1={rr['pass_at_1']:.3f}")
            return dict((rr['label'], rr['pass_at_1']) for rr in r)

        r_dist = show("in-dist", test)
        r_exp = show("exposed-composite", exposed)
        r_held = show("HELD-OUT-composite", heldout)
        results[mode] = {"in_dist": r_dist, "exposed": r_exp, "held_out": r_held,
                         "final_loss": losses[-1], "n_exposed": len(exposed)}
        print("  saved ->", ckpt)

    manifest = {
        "experiment_id": f"composition_diversity{args.tag}",
        "status": "MEASURED",
        "held_out_op": HELD_OUT_OP,
        "exposed_ops": EXPOSED_OPS,
        "results": results,
    }
    mp = os.path.join(ROOT, "artifacts", "manifests", f"composition_diversity{args.tag}.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("\nmanifest ->", mp)

    # ---- print summary table ----
    print("\n=========================== SUMMARY ===========================")
    print(f"{'mode':<18} {'in-dist':>8} {'exposed':>9} {'HELD-OUT':>9}")
    for mode, r in results.items():
        print(f"{mode:<18} {r['in_dist'].get('MODEL',0):>8.3f} {r['exposed'].get('MODEL',0):>9.3f} "
              f"{r['held_out'].get('MODEL',0):>9.3f}")


if __name__ == "__main__":
    main()
