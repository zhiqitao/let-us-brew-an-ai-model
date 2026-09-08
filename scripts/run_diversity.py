#!/usr/bin/env python3
"""Chapter-13 experiments: QUANTITY vs DIVERSITY.

Isolate whether a model's in-distribution capability comes from seeing MANY examples
or DIVERSE examples. Three datasets of equal token count but different composition:
  - MINIMAL-DIVERSITY : many examples of a FEW phrasings/identifier-sets.
  - HIGH-DIVERSITY   : same example count spread across MANY phrasings + identifier
                       sets (letters vs words).
Then measure in-distribution pass@1 AND surface-robustness (new wording + new IDs).

Usage: python scripts/run_diversity.py [--steps N] [--n-embd N] [--n-layer N]
"""
import os, sys, json, argparse, time, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.model.gpt import GPT, Config
from src.train.trainer import Dataset, train as train_fn
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge
from src.data_generator.generator import make_task, OPERATIONS

ROOT = os.path.join(os.path.dirname(__file__), "..")
from src.nl_renderer.renderer import FAMILIES

ID_SETS = ["letters", "words"]


def build_pool():
    """A big pool of tasks across all operations, families, identifier-sets."""
    tasks = []
    for op in OPERATIONS:
        for fid, fam in enumerate(FAMILIES[op]):
            for idn, id_set in enumerate(ID_SETS):
                tasks.append(make_task(op, f"{op}_{fid}_{idn}", seed=1000 + len(tasks),
                                       id_set=id_set, family=fam))
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=900)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--n-train", type=int, default=1200)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    pool = build_pool()
    rng = random.Random(args.seed)
    rng.shuffle(pool)
    train_pool = pool[:args.n_train]
    # held-out surface test: a held-out family per op + word IDs
    from src.nl_renderer.renderer import FAMILIES as F

    def make_tok(tasks):
        from src.tokenizer.tokenizer import train_tokenizer
        return train_tokenizer([t["nl"]["prompt"] + "\n" + t["reference_code"] for t in tasks],
                               min_vocab=128, max_vocab=300)

    def make_test(ops=OPERATIONS):
        # in-dist test: same ops, letters, familiar families
        dist = [make_task(op, f"id_{op}_{i}", seed=5000 + i, id_set="letters")
                for op in ops for i in range(6)]
        # surface test: word identifiers + a possibly-unseen family
        surf = [make_task(op, f"sf_{op}_{i}", seed=9000 + i, id_set="words")
                for op in ops for i in range(6)]
        return dist, surf

    judge = Judge()
    results = {}
    for mode in ["minimal_diversity", "high_diversity"]:
        if mode == "minimal_diversity":
            # FEW families, FEW id-sets, but many examples repeated
            # take a narrow slice of the pool (letters, first family) and duplicate to n_train
            narrow = []
            for op in OPERATIONS:
                fam = FAMILIES[op][0]
                for i in range(args.n_train // len(OPERATIONS) + 1):
                    narrow.append(make_task(op, f"{op}_n{i}", seed=2000 + i,
                                            id_set="letters", family=fam))
            train = narrow[:args.n_train]
        else:
            train = train_pool  # diverse: all families, both id-sets
        tok = make_tok(train)
        cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                     n_head=args.n_head, block_size=128)
        m = GPT(cfg)
        ds = Dataset(train, tok)
        t0 = time.time()
        losses = train_fn(m, ds, steps=args.steps, bs=16, lr=1e-3)
        dist, surf = make_test()
        rd = evaluate_all(m, tok, train, dist, judge)
        rs = evaluate_all(m, tok, train, surf, judge)
        d_model = next(r for r in rd if r["label"] == "MODEL")
        s_model = next(r for r in rs if r["label"] == "MODEL")
        results[mode] = {"in_dist": round(d_model["pass_at_1"], 3),
                         "surface": round(s_model["pass_at_1"], 3),
                         "train_time_s": round(time.time()-t0, 1)}
        print(f"  {mode:20s} in-dist={results[mode]['in_dist']:.3f}  "
              f"surface={results[mode]['surface']:.3f}  ({results[mode]['train_time_s']}s)")

    mp = os.path.join(ROOT, "artifacts", "manifests", "diversity.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump({"results": results, "config": vars(args)}, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
