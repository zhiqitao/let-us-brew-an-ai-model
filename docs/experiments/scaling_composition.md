# Experiment — Model-size scaling vs. composition

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/stage4_scaling.json`.

## Setup
Same composition experiment (train on primitives, test on unseen composite
operations), but with a **7.4× larger model** to isolate whether capacity buys
composition. Tokenizer and data identical.

| Model | params | in-dist pass@1 | composition pass@1 |
|-------|--------|----------------|--------------------|
| Stage-4 baseline | 884,224 (0.88M) | 0.900 | **0.000** |
| **Scaling** | 6,500,352 (6.5M) | 0.900 | **0.000** |

## Interpretation — a clean negative result

- **More capacity does not buy composition at this scale.** Going from ~0.9M to 6.5M
  parameters (7.4×) leaves composition at **0.000**. The bigger model reproduces the
  primitives identically (in-dist 0.900) but still cannot combine them in unseen ways.
- This directly addresses the central question *"does more brain buy genuine
  capability or merely more memorization?"* — here it buys **neither** for
  composition at this scale. It neither improves composition nor obviously worsens
  anything; the boundary is invariant.
- **Implication for the book's thesis:** the compositional generalization failure we
  found is **not a capacity ceiling** in the 1–7M regime. It is a structural
  learning limit that scaling alone does not resolve. Something else is required —
  more *structural* training data (exposure to combinations), or a fundamentally
  different inductive bias — not just more parameters.

## Outstanding
- Does *data* help (more compositional examples / diversity)? [data-scaling,
  diversity experiments prepared]
- Would exposure to a few composites during training unlock composition?

## Reproduce
```bash
python scripts/run_composition.py --steps 1000 --n-embd 256 --n-layer 8 --n-head 8 \
  --seed 0 --comp-per-op 40
python scripts/eval_ckpt.py --sample 40   # re-eval saved ckpt quickly
```
