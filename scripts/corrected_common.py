"""Shared helpers for the CORRECTED experiments (fixes P0-01 / P0-03 / P0-04).

Both corrected scripts score MODEL + TEMPLATE + RETRIEVAL with the exact same
candidate functions that `src.eval.evaluator_runner.evaluate_all` builds, but
they tally per-operation integer successes so every manifest row carries an
exact numerator/denominator (e.g. 420/480) instead of a rounded rate only
(P0-04), and every condition's realized task counts are asserted.
"""
import hashlib
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.baselines.retrieval.baseline import RetrievalBaseline
from src.baselines.template.baseline import template_baseline_generate
from src.eval.evaluator_runner import evaluate_candidates, generate_code


def vocab_sha256(tok):
    """Stable hash of the tokenizer mapping (token string -> id order)."""
    return hashlib.sha256("\x1f".join(tok.vocab).encode("utf-8")).hexdigest()


def assert_full_byte_alphabet(tok):
    """Nothing may be out-of-vocab: all 256 single-byte tokens must exist."""
    missing = [c for c in (chr(i) for i in range(256)) if c not in tok.stoi]
    assert not missing, f"tokenizer missing {len(missing)} byte tokens"


def content_key(task):
    return (task["nl"]["prompt"], task["reference_code"])


def instance_seeds(tasks):
    """The per-instance construction seed (metadata.seed) of every task."""
    return {t["metadata"]["seed"] for t in tasks}


def content_stats(tasks):
    """Instance count vs distinct (prompt, code) contents.

    In this benchmark the prompt and reference code are deterministic in
    (operation, template family, identifier set), so many instances share
    content; instances differ by their hidden tests. An in-distribution
    holdout can therefore only be instance-level, never content-level.
    """
    keys = [content_key(t) for t in tasks]
    return {"n_instances": len(keys),
            "distinct_prompt_code": len(set(keys)),
            "distinct_prompts": len({k[0] for k in keys})}


def group_by_op(tasks):
    by_op = defaultdict(list)
    for t in tasks:
        by_op[t["semantics"]["operation"]].append(t)
    return by_op


def per_op_counts(tasks):
    return {op: len(g) for op, g in sorted(group_by_op(tasks).items())}


def assert_disjoint(a, b, what="train/test"):
    overlap = {content_key(t) for t in a} & {content_key(t) for t in b}
    assert not overlap, f"{what} content overlap: {len(overlap)} tasks"


def score_all(model, tokenizer, train_tasks, test_tasks, judge, eval_seed):
    """Score MODEL/TEMPLATE/RETRIEVAL over the IDENTICAL task set, per operation.

    Uses the same `generate_code` / `template_baseline_generate` /
    `RetrievalBaseline` candidate functions as `evaluate_all`, but calls
    `evaluate_candidates` once per operation group so we get exact integer
    successes per operation and in aggregate.

    Returns {label: {successes, denominator, pass_at_1, syntax_rate,
                     executable_rate, per_op: {op: {successes, denominator,
                                                   pass_at_1}}}}.
    """
    import random

    import torch

    by_op = group_by_op(test_tasks)
    rb = RetrievalBaseline(train_tasks)
    fns = [
        ("MODEL", lambda t: generate_code(model, tokenizer, t["nl"]["prompt"])),
        ("TEMPLATE", template_baseline_generate),
        ("RETRIEVAL", rb.baseline_generate),
    ]
    total = len(test_tasks)
    assert total > 0, "empty test set"
    out = {}
    for label, fn in fns:
        # Deterministic sampling: reseed before each system so a resumed run
        # reproduces the same generations from the same checkpoint.
        torch.manual_seed(eval_seed)
        random.seed(eval_seed)
        per_op, succ, syn, exe = {}, 0, 0.0, 0.0
        for op in sorted(by_op):
            g = by_op[op]
            r = evaluate_candidates(g, judge, fn, label)
            n = len(g)
            s = int(round(r["pass_at_1"] * n))
            per_op[op] = {"successes": s, "denominator": n,
                          "pass_at_1": round(s / n, 4)}
            succ += s
            syn += r["syntax_rate"] * n
            exe += r["executable_rate"] * n
        assert sum(v["denominator"] for v in per_op.values()) == total
        out[label] = {
            "successes": succ,
            "denominator": total,
            "pass_at_1": round(succ / total, 4),
            "syntax_rate": round(syn / total, 4),
            "executable_rate": round(exe / total, 4),
            "per_op": per_op,
        }
        assert 0 <= succ <= total
    return out


def load_partial(path):
    import json
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_partial(path, partial):
    import json
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(partial, f, indent=2)
    os.replace(tmp, path)