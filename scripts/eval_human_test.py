#!/usr/bin/env python3
"""Evaluate the human-written test set (§37 external sanity check) against a trained
model. Loads a checkpoint, runs each human-phrased prompt through the model, and
scores the generated program on the expected output. Reports per-operation.

Usage: python scripts/eval_human_test.py [--ckpt artifacts/checkpoints/stage1.pt]
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.model.gpt import GPT, Config
from src.tokenizer.tokenizer import load_tokenizer
from src.eval.evaluator_runner import generate_code
from src.evaluator.comparator import semantic_equal

ROOT = os.path.join(os.path.dirname(__file__), "..")
HUMAN = os.path.join(ROOT, "artifacts", "datasets", "human_test.jsonl")

# Map operation -> arity & arg types for building the call signature.
OPS = {
    "add": 2, "sub": 2, "mul": 2, "max_of": 2, "min_of": 2,
    "abs_of": 1, "list_sum": 1, "list_len": 1, "first_element": 1,
    "cond_abs_max": 2, "abs_add": 2, "sub_abs": 2, "sum_of_abs": 1,
    "max_add": 2, "double_first": 1, "len_minus_one": 1,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=os.path.join(ROOT, "artifacts", "checkpoints", "stage1.pt"))
    ap.add_argument("--tok", default=os.path.join(ROOT, "artifacts", "tokenizer", "pilot_tok.json"))
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    args = ap.parse_args()

    tok = load_tokenizer(args.tok)
    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)
    m = GPT(cfg); m.load_state_dict(torch.load(args.ckpt)); m.eval()

    cases = [json.loads(l) for l in open(HUMAN)]
    print(f"=== human-written test set ({len(cases)} prompts) on {os.path.basename(args.ckpt)} ===")
    ok = 0
    for c in cases:
        op = c["operation"]; prompt = c["prompt"]; expected = c["expected"]; args_list = c["args"]
        gen = generate_code(m, tok, prompt)
        # execute the generated program in the sandbox on the test args
        try:
            from src.sandbox import sandbox
            out = sandbox.execute_function(gen, args_list)
            passed = semantic_equal(out, expected)
        except Exception as e:
            out = None; passed = False
        if passed: ok += 1
        print(f"  [{op:12s}] {'PASS' if passed else 'FAIL'}  expected={expected} got={out!r}")
        print(f"      prompt: {prompt[:48]!r}")
        print(f"      gen   : {gen.replace(chr(10),' | ')[:48]!r}")
    print(f"\n=> {ok}/{len(cases)} human-written prompts solved")
    return ok/len(cases) if cases else 0.0


if __name__ == "__main__":
    main()
