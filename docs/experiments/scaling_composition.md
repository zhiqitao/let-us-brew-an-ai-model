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
| **10M point** | 10,195,776 (10.2M) | **0.383** | **0.000** |
| **30M point** | 29,290,240 (29.3M) | **0.897** | **0.000** |

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


## A surprising side-finding: the 10M model got *worse* in-distribution

On a clean larger-sample re-evaluation, the **10M** model's in-distribution pass@1 is
**0.383** — clearly *below* the 0.900 of both the 0.88M and 6.5M models, and below the
template baseline (0.808). This is not a sampling artifact (it held at 0.350 on a
40-task sample and 0.383 on a 120-task sample).

The likely explanation is training config, not a universal law: the 10M model used a
deeper 10-layer / 288-wide config, trained for only 800 steps (same as the others),
on the same narrow task. A deeper model at this tiny scale, under-trained, can be
*harder* to fit to a simple task than a shallower one — an instance of "bigger isn't
always better" at very small parameter counts. Worth isolating, but it does not change
the headline result.

## The composition result is robust

At all three sizes — 0.88M, 6.5M, and 10.2M — **compositional pass@1 = 0.000**, and the
baselines also collapse to 0.000, confirming the split is fair. So the negative result
"scaling does not buy composition at ~1–10M params" is now supported by three points.
