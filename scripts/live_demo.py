#!/usr/bin/env python3
"""LIVE demo: show the pilot model generating code from an IN-DESIGN (template)
prompt vs a HUMAN-phrased prompt. Real output from the saved checkpoint.
Run: python scripts/live_demo.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from src.tokenizer.tokenizer import load_tokenizer
from src.model.gpt import GPT, Config
from src.eval.evaluator_runner import generate_code
from src.evaluator.evaluator import Judge

ROOT = os.path.join(os.path.dirname(__file__), "..")
tok = load_tokenizer(os.path.join(ROOT, "artifacts", "tokenizer", "pilot_tok.json"))
cfg = Config(vocab_size=tok.vocab_size, n_embd=128, n_layer=4, n_head=4, block_size=128)
m = GPT(cfg); m.load_state_dict(torch.load(os.path.join(ROOT, "artifacts", "checkpoints", "stage1.pt"))); m.eval()
judge = Judge()

# A template prompt EXACTLY like the training distribution (this is what the model is designed for)
design_prompt = ("implement solve so that given a and b it returns their sum.")
# A human-phrased equivalent (out of design)
human_prompt = "Take two numbers and give me back their total."

for name, prompt in [("IN-DESIGN (template)", design_prompt), ("HUMAN-PHRASED", human_prompt)]:
    code = generate_code(m, tok, prompt, max_new=80)
    print("=" * 60)
    print(f"PROMPT [{name}]: {prompt}")
    print("MODEL GENERATED:")
    for line in code.splitlines():
        print("   ", line)
    # quick syntax check
    import ast
    try:
        ast.parse(code); print("   -> syntactically OK")
    except Exception as e:
        print(f"   -> SYNTAX ERROR: {type(e).__name__}: {e}")
