#!/usr/bin/env python3
"""Audit model-visible prompt uniqueness across train/test for the surface and
composition splits (R05). Task IDs can change hidden-test inputs without changing
the prompt/reference; this checks the actual model-input strings.

For each split, reports: distinct task records, distinct prompt strings, distinct
prompt/reference pairs, and the prompt overlap between train and test.
"""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_generator.generator import make_task, OPERATIONS, COMPOSITE_OPERATIONS
from src.nl_renderer.renderer import FAMILIES


def surface_split():
    """Mimic run_surface.py: train = letters + all-but-last family; test held-out
    last family; new-ID test = words + any family."""
    by_op = {}
    for op in OPERATIONS:
        fams = FAMILIES[op]
        kept = fams[:-1]; held = [fams[-1]]
        by_op[op] = (kept, held)
    train, in_dist, held_word = [], [], []
    for op,(kept,held) in by_op.items():
        for i,fam in enumerate(kept):
            for j in range(10):
                train.append(make_task(op, f"{op}_t{i}_{j}", 2000+j, id_set="letters", family=fam))
        fidx = kept[0] if kept else held[0]
        for j in range(10):
            in_dist.append(make_task(op, f"{op}_id{j}", 9000+j, id_set="letters", family=fidx))
        for j in range(10):
            held_word.append(make_task(op, f"{op}_h{j}", 30000+j, id_set="letters", family=held[0]))
    return train, in_dist, held_word


def compose_split():
    train = []
    for op in OPERATIONS:
        for j in range(10):
            train.append(make_task(op, f"{op}_c{j}", 3000+j, id_set="letters"))
    comp = []
    for op in COMPOSITE_OPERATIONS:
        for j in range(10):
            comp.append(make_task(op, f"{op}_cc{j}", 6000+j, id_set="letters"))
    return train, comp


def uniq(records):
    prompts = collections.Counter(r["nl"]["prompt"] for r in records)
    pairs = collections.Counter((r["nl"]["prompt"], r["reference_code"]) for r in records)
    return set(records[0]["nl"]["prompt"].__class__(k) if False else k for k in prompts), \
           set(p for p,_ in pairs), len(records), len(prompts), len(pairs)


def main():
    out = {}
    # --- surface ---
    train, in_dist, held_word = surface_split()
    def count(recs):
        ps = set(r["nl"]["prompt"] for r in recs)
        pairs = set((r["nl"]["prompt"], r["reference_code"]) for r in recs)
        return len(recs), len(ps), len(pairs)
    tr,trp,trpr = count(train)
    hid,hp,hpr = count(held_word)
    nd,ndp,ndpr = count(in_dist)
    # prompt overlap between train and held-word
    train_prompts = set(r["nl"]["prompt"] for r in train)
    held_prompts = set(r["nl"]["prompt"] for r in held_word)
    train_pairs = set((r["nl"]["prompt"], r["reference_code"]) for r in train)
    held_pairs = set((r["nl"]["prompt"], r["reference_code"]) for r in held_word)
    surface = {
        "train": {"records": tr, "unique_prompts": trp, "unique_prompt_program_pairs": trpr},
        "in_dist": {"records": nd, "unique_prompts": ndp, "unique_pairs": ndpr},
        "held_word": {"records": hid, "unique_prompts": hp, "unique_pairs": hpr},
        "train_heldword_prompt_overlap": len(train_prompts & held_prompts),
        "train_heldword_pair_overlap": len(train_pairs & held_pairs),
    }
    out["surface"] = surface

    # --- composition ---
    ctrain, comp = compose_split()
    ct,ctp,ctpr = count(ctrain)
    c2, cp, cpr = count(comp)
    ctrain_prompts = set(r["nl"]["prompt"] for r in ctrain)
    comp_prompts = set(r["nl"]["prompt"] for r in comp)
    out["composition"] = {
        "train": {"records": ct, "unique_prompts": ctp, "unique_pairs": ctpr},
        "composite_holdout": {"records": c2, "unique_prompts": cp, "unique_pairs": cpr},
        "train_comp_prompt_overlap": len(ctrain_prompts & comp_prompts),
    }

    mp = os.path.join(os.path.dirname(__file__), "..", "artifacts", "manifests", "dedup_audit.json")
    json.dump(out, open(mp, "w"), indent=2)
    print(json.dumps(out, indent=1))
    print("manifest ->", mp)

if __name__ == "__main__":
    main()
