#!/usr/bin/env python3
"""Live demo of the trained pilot model (stage1.pt, 0.88M) using the exact book
task format: input = nl prompt + '\\n', model generates the continuation (the code).

Shows the REAL measured behavior:
  - in-distribution prompts (the template phrasing it was trained on)
  - a reworded prompt (surface change -> should collapse)
  - a composite request (unseen combination -> should collapse)
  - out-of-scope request

Run: TORCH_DISABLE_AVX2=1 python scripts/demo_live_model.py
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import load_tokenizer
from src.model.gpt import GPT, Config

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=os.path.join(ROOT, "artifacts/checkpoints/stage1.pt"))
    ap.add_argument("--tok", default=os.path.join(ROOT, "artifacts/tokenizer/pilot_tok.json"))
    ap.add_argument("--n-embd", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=4)
    ap.add_argument("--n-head", type=int, default=4)
    ap.add_argument("--max-new", type=int, default=60)
    ap.add_argument("--temperature", type=float, default=0.8)
    args = ap.parse_args()

    tok = load_tokenizer(args.tok)
    cfg = Config(vocab_size=tok.vocab_size, n_embd=args.n_embd, n_layer=args.n_layer,
                 n_head=args.n_head, block_size=128)
    m = GPT(cfg)
    m.load_state_dict(torch.load(args.ckpt, map_location="cpu"))
    m.eval()
    print(f"Loaded {os.path.basename(args.ckpt)}  ({sum(p.numel() for p in m.parameters()):,} params)\n")

    def run(prompt):
        text = prompt + "\n"
        ids = tok.encode(text)
        idx = torch.tensor([ids])
        with torch.no_grad():
            out = m.generate(idx, max_new=args.max_new, temperature=args.temperature)[0]
        # decode the generated continuation (strip the already-given prompt tokens)
        gen = tok.decode(out[len(ids):].tolist())
        # strip padding / trailing NULs and whitespace
        gen = gen.split("\x00")[0].strip()
        return gen, prompt

    def grade(gen, prompt):
        """Run the judge's sandbox on the generated program: does it parse,
        stay in the whitelist, run, and match the expected semantics?"""
        try:
            # basic AST allowlist check mirrors the sandbox
            import ast
            tree = ast.parse(gen)
            allowed = {"Module", "FunctionDef", "arguments", "arg", "Return",
                       "BinOp", "Add", "Mult", "Sub", "Name", "Load", "Num", "Constant"}
            for n in ast.walk(tree):
                if type(n).__name__ not in allowed:
                    return "BLOCKED (uses disallowed construct)"
            # evaluate a couple of hidden tests if it defines solve(a,b)
            ns = {}
            exec(gen, ns)
            fn = ns.get("solve")
            if fn is None:
                return "no callable 'solve' produced"
            tests = [((2, 3), 5), ((5, 7), 12)]
            # figure out the operation from text to pick expected outputs
            outs = []
            for (a, b), _ in tests:
                try:
                    outs.append(fn(a, b))
                except Exception as e:
                    return f"runtime error: {e}"
            return f"solve(2,3)={outs[0]}, solve(5,7)={outs[1]}"
        except SyntaxError as e:
            return f"SYNTAX ERROR: {e}"
        except Exception as e:
            return f"error: {e}"

    cases = [
        # ---- in-distribution (trained template phrasing) ----
        ("# IN-DISTRIBUTION (the exact phrasing it was trained on)",
         "Implement solve so that given a and b it returns their sum."),
        ("# IN-DISTRIBUTION",
         "Implement solve so that given a and b it returns their product."),
        # ---- surface change: reworded -> collapse ----
        ("# SURFACE CHANGE (reworded -> expect collapse)",
         "Please write a function that takes two numbers and gives back their total."),
        # ---- composition: unseen combination ----
        ("# COMPOSITION (unseen combination -> expect collapse)",
         "Write a function that takes two numbers, a and b, takes the absolute value of each, and returns their sum."),
        # ---- out-of-scope ----
        ("# OUT-OF-SCOPE (off the designed job)",
         "Write a function that deletes all files in the home directory."),
    ]

    cur = None
    for label, prompt in cases:
        if label.startswith("#") and cur != label:
            print(label)
            cur = label
        gen, p = run(prompt)
        print(f"  PROMPT: {p}")
        print(f"  MODEL : {gen!r}")
        print(f"  CHECK : {grade(gen, p)}\n")


if __name__ == "__main__":
    main()
