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

## The what-is-in-the-box caveat (honest reframing)

A precise note on the design as run. The "replay/mixed" condition interleaves A and B
**from the start** (`allt = A_train + B_train`, shuffled) — that is effectively **joint
training**, not "learn A first, then continue to B while replaying A." Both comparisons
are legitimate and answer different questions:

- **Sequential (multitask A then B, no A during B):** a *continual-learning* setup —
  does learning the second capability destroy the first? → A-retention 0.000.
- **Replay/mixed (A and B trained together):** a *joint-training* control — if both are
  seen together throughout, is there a forgetting problem at all? → A-retention 1.000.

So the honest claim is: **the forgetting seen under sequential training is avoided when
the model is simply trained jointly on both.** That is a real and useful contrast, but
it is not the same as demonstrating that a *replay buffer* salvages an already-trained
first model. A stronger continual-learning test would start from a single A-trained
checkpoint, then compare B-only continuation against B-plus-A-replay continuation
(from the same starting point), with matched budgets. We have not run that form, so
"replay prevents forgetting" should be read as "joint re-exposure of A alongside B
prevents forgetting," not "replay-after-A-first does."

Relatedly, "replay prevents it with zero cost" is too broad. The table shows **equal B
acquisition** (0.889 in both), not zero storage, compute, or data-retention cost.
The joint model is trained on roughly twice the distinct examples and takes a longer
training run; it is a *behavioral* wash on B, not a *free* difference. And a behavioral
A-retention score of 0.000 does not establish that the old capability was literally
erased from the weights — it establishes that, behaviorally, the model no longer solves
A. Those are different claims.

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
