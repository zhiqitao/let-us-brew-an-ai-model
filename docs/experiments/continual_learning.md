# Experiment — Stage 7: Continual Learning / Capability Retention

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/continual.json`.

## Setup
Train on capability A (arithmetic: add, sub, mul, max_of, min_of), then introduce
capability B (lists: list_sum, list_len, first_element). Compare two protocols:
- **sequential:** learn A fully, then learn B (no A exposure during B).
- **replay/mixed:** interleave A and B examples throughout.

Measure: B acquisition (did it learn the new capability?) and A retention (did it keep
the old one, or did learning B destroy it?).

## Result

| Protocol | **A-retention** | **B-acquisition** |
|----------|-----------------|-------------------|
| **sequential** | **0.000** | 0.889 |
| **replay**     | **1.000** | 0.889 |

## Interpretation — a clean, textbook result

1. **Sequential training causes catastrophic forgetting.** After learning arithmetic
   (A) and then lists (B) sequentially, the model's A-retention is **0.000** — it has
   completely forgotten the first capability. But it learned B fine (0.889). So
   "learning the new thing" did not preserve the old thing; it destroyed it.

2. **Replay/mixed training preserves A with zero cost.** Interleaving A and B
   throughout training gives A-retention **1.000** (perfect) *and* B-acquisition
   0.889 (identical to sequential). So replay bought complete retention with **no
   trade-off** in acquiring the new capability.

3. This is the continual-learning result the design's Stage-4→7 ladder predicted:
   acquiring a new capability can destroy an old one, and the *way* you train (replay
   vs sequential) determines whether it does.

## Why this matters for the book

This is the single cleanest case in the book where the **training protocol — not the
model, data, or capacity — determines the outcome.** Same model, same data; the only
difference is whether A stays in the mix while learning B. Sequential forgets;
replay retains. It is a direct, controlled demonstration that catastrophic
forgetting is a *procedure* problem, not a fate — echoing the alignment chapter of the
earlier draft but here measured cleanly on the compositional task.

## Outstanding
- Does replay's benefit extend to *three* capabilities, or to composing A and B after
  sequential? (Composition after continual learning — could be a follow-up.)
- Is A-retention loss also surface-tied? (Does forgetting hit primitives uniformly or
  surface-dependent ones first?) — future.

## Reproduce
```bash
python scripts/run_continual.py --steps-a 700 --steps-b 700 --n-per 70
```
