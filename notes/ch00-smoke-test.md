# Chapter 0 — The Smoke Test: proving the pipeline is alive

> This is the first brew. Not a real model — a proof that this machine can train
> one. Everything here is the *actual* log from running
> `artifacts/ch00_smoke_test.py` on a 4-core CPU laptop (Intel i5-3210M, 15 GB RAM).

## The Architect's Question

Before committing to any model size, data, or architecture, we must answer one
question: **does the training pipeline run end-to-end on this machine?** If we
cannot make loss go down on a toy, no amount of clever architecture matters.

## What the smoke test covers (`artifacts/ch00_smoke_test.py`)

A single script that, in order:

1. Builds a tiny character-level dataset (a few repeated "sentences" over a 28-char
   alphabet — enough gradient signal to learn within seconds).
2. Defines a minimal GPT-style transformer (~0.46M params) using only core PyTorch:
   token + positional embeddings, blocks of causal self-attention
   (`scaled_dot_product_attention`) + GELU MLP, final LayerNorm + linear head.
3. Runs forward → cross-entropy loss → backward → AdamW step for 30 steps.
4. Samples text from the trained weights to confirm it actually learned structure.

## Measured results (real run, CPU only)

| Metric | Value |
|---|---|
| Model params | **459,100** (~0.46M) |
| Vocab | 28 chars (character-level) |
| Loss (step 0 → step 29) | **3.3854 → 2.2080** (↓ ~35%) |
| Time | 30 steps in **3.9 s** (~130 ms/step) |
| Sample output | `"the quick …jump…"` — learned word-like structure |
| Hardware | CPU only (Intel i5-3210M, 4 cores, 15 GB RAM) |
| Software | PyTorch 2.14.0+cpu, NumPy 2.4.6 |

## The decisions (why this specific setup)

- **Character-level, not BPE.** For a smoke test we want zero tokenizer complexity —
  the goal is to prove training, not tokenization. BPE comes in Chapter 1.
- **~0.46M, not smaller.** At 0.1M–0.5M the model is in the "interesting but trivial"
  band: big enough to show real loss dynamics and structure, small enough that every
  decision re-runs in seconds.
- **CPU, not GPU.** Deliberate. This removes the entire class of driver/kernel
  compatibility risk from the first proof, so the only thing under test is the
  math and the pipeline. (This matters especially here — the original plan used a
  GPU whose training stack was unproven; CPU sidesteps it entirely.)

## What it proves

1. **The pipeline is real.** Forward, backward, optimizer, and generation all work.
2. **Loss actually descends.** 35% drop over 30 steps confirms the gradient flow
   and the task are well-posed.
3. **The machine is enough.** A 4-core CPU trains a 0.46M model in ~4 seconds —
   so the book's "time to feedback" is seconds, ideal for teaching.

## What it does NOT prove (honest limits)

- Not a "real" dataset or meaningful task — the text is synthetic repetition.
- Down ~35% on a toy is not evidence of *deliberate* learning; it's evidence the
  plumbing works. Real capability needs Chapter 1+.
- 30 steps is trivial; no learning-rate schedule, no eval, no generalization test.

## Verdict

**SMOKE TEST: PASS.** The training stack is alive on this machine. The journey can
begin at any scale; next is the tokenizer and data (Chapter 1), then a 10M
from-scratch pre-train (Chapter 2) where the loss curves start to mean something.
