#!/usr/bin/env python3
"""Stage 3 experiment: SURFACE generalization (Level 3).

Train the student on one surface regime, then test whether it survives changes that
should NOT alter the underlying computation:
  (a) HELD-OUT WORDING  : train on some template families; test on a held-out one.
  (b) NEW IDENTIFIERS   : train on letter names (a,b); test on word names (l,r).
  (c) NEW CONSTANTS     : baked into hidden tests (general programs).

Compares MODEL vs template + retrieval baselines.

Usage: python scripts/run_surface.py [--steps N] [--n-embd N] [--n-layer N]
"""
import os, sys, json, argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import Tokenizer
from src.model.gpt import GPT, Config
from src.train.trainer import Dataset, train as train_fn
from src.eval.evaluator_runner import evaluate_all
from src.evaluator.evaluator import Judge
from src.data_generator.generator import make_task, OPERATIONS
from src.nl_renderer.renderer import FAMILIES

ROOT = os.path.join(os.path.dirname(__file__), "..")


def build_tasks(id_set, families, n_per, seed):
    """Build train tasks (letters, kept wording families), an in-distribution test,
    and a held-out-family test. `families` == 'holdout_last' or 'all'.
    Returns (train, in_dist, held_word).
    """
    in_dist, held_word, train = [], [], []
    for op in OPERATIONS:
        fams = FAMILIES[op]
        kept = fams if families == "all" else fams[:max(1, len(fams) - 1)]
        held_fams = [f for f in fams if f not in kept] if families != "all" else []
        for i in range(n_per):
            fam = (kept[i % len(kept)] if kept else fams[0])
            train.append(make_task(op, f"{op}_{i:04d}", seed + i, id_set=id_set, family=fam))
            in_dist.append(make_task(op, f"{op}_id{i:04d}", seed + 20000 + i,
                                     id_set=id_set, family=fam))
        for i in range(n_per):
            if held_fams:
                held_word.append(make_task(op, f"{op}_h{i:04d}", seed + 30000 + i,
                                           id_set=id_set, family=held_fams[0]))
    return train, in_dist, held_word


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-per", type=int, default=130)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    # train on letters, all-but-last wording families.
    train_tasks, in_dist, held_word = build_tasks("letters", "holdout_last", args.n_per, args.seed)
    # new-identifier test: word names, any family.
    _, word_id, _ = build_tasks("words", "all", args.n_per, args.seed + 5000)

    all_texts = []
    for t in train_tasks + in_dist + held_word + word_id:
        all_texts.append(t["nl"]["prompt"] + "\n" + t["reference_code"])
    from src.tokenizer.tokenizer import train_tokenizer
    tok_path = os.path.join(ROOT, "artifacts", "tokenizer", "surface_tok.json")
    tok = train_tokenizer(all_texts, min_vocab=128, max_vocab=300, save_path=tok_path)
    print(f"tokenizer vocab = {tok.vocab_size}  train={len(train_tasks)} "
          f"in-dist={len(in_dist)} held-word={len(held_word)} new-id={len(word_id)}")

    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)
    m = GPT(cfg); emb, non_emb = m.num_params()
    print(f"model params: total={emb+non_emb}")

    ds = Dataset(train_tasks, tok)
    t0 = time.time()
    losses = train_fn(m, ds, steps=args.steps, bs=args.bs, lr=args.lr)
    print(f"trained in {time.time()-t0:.1f}s; final loss {losses[-1]:.4f}")
    ckpt = os.path.join(ROOT, "artifacts", "checkpoints", "stage3_surface.pt")
    os.makedirs(os.path.dirname(ckpt), exist_ok=True)
    torch.save(m.state_dict(), ckpt)
    print("saved ->", ckpt)

    judge = Judge()
    from src.baselines.retrieval.baseline import RetrievalBaseline
    rb = RetrievalBaseline(train_tasks)

    setups = [("in-distribution", in_dist),
              ("new IDENTIFIERS (word names)", word_id),
              ("held-out WORDING (last family)", held_word)]
    manifest = {"experiment_id": "stage3_surface", "status": "MEASURED",
                "model_params": {"total": emb+non_emb},
                "final_train_loss": round(losses[-1], 4), "config": vars(args),
                "results": {}}
    for label, tasks in setups:
        if not tasks:
            print(f"\n  {label}: (no tasks)"); continue
        results = evaluate_all(m, tok, train_tasks, tasks, judge)
        print(f"\n  {label} ({len(tasks)} tasks):")
        for r in results:
            print(f"    {r['label']:9s} pass@1={r['pass_at_1']:.3f}")
        manifest["results"][label] = results

    mp = os.path.join(ROOT, "artifacts", "manifests", "stage3_surface.json")
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest ->", mp)


if __name__ == "__main__":
    main()
