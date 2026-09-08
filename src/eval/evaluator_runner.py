"""Evaluation pipeline: model generation -> Judge -> metric extraction + baseline
comparison. `scripts/train.py --eval` drives this after training, or as a fast smoke.
"""
import json
import torch
from src.evaluator.evaluator import Judge
from src.baselines.template.baseline import template_baseline_generate
from src.baselines.retrieval.baseline import RetrievalBaseline


def load_tasks(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def generate_code(model, tokenizer, prompt, max_new=80, prompt_marker="\n"):
    text = prompt + prompt_marker
    ids = tokenizer.encode(text)
    ctx = torch.tensor([ids])
    out = model.generate(ctx, max_new=max_new)
    gen_ids = out[0].tolist()
    code = tokenizer.decode(gen_ids[len(ids):])
    # Truncate at the first NUL byte (a valid Python program never contains it).
    # The model tends to pad with NUL after producing a complete program.
    nul = code.find("\x00")
    if nul != -1:
        code = code[:nul]
    return code.strip()


def evaluate_candidates(tasks, judge, candidate_fn, label):
    """Return dict of {metric: value} over a candidate-generating function."""
    syntax = 0; cap = 0; exe = 0; pass1 = 0
    total = len(tasks)
    for t in tasks:
        code = candidate_fn(t)
        r = judge.evaluate_problem(code, t["hidden_tests"])
        if r["syntax_ok"]: syntax += 1
        if r["capability_ok"]: cap += 1
        if r["execution_ok"]: exe += 1
        if r["pass_at_1"]: pass1 += 1
    return {
        "label": label,
        "syntax_rate": syntax / total if total else 0.0,
        "executable_rate": exe / total if total else 0.0,
        "pass_at_1": pass1 / total if total else 0.0,
    }


def evaluate_all(model, tokenizer, train_tasks, test_tasks, judge, prompt_marker="\n"):
    model.eval()
    results = []

    def model_fn(t):
        return generate_code(model, tokenizer, t["nl"]["prompt"], prompt_marker=prompt_marker)

    def template_fn(t):
        return template_baseline_generate(t)

    rb = RetrievalBaseline(train_tasks)

    def retrieval_fn(t):
        return rb.baseline_generate(t)

    for fn, label in [(model_fn, "MODEL"), (template_fn, "TEMPLATE"), (retrieval_fn, "RETRIEVAL")]:
        results.append(evaluate_candidates(test_tasks, judge, fn, label))
    return results
