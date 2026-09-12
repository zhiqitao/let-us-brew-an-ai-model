# Experiment — Composition exposure: does seeing some combinations unlock composition on unseen ones?

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/composition_exposure_pilot.json`.

## The question

The book's central open question: is composition a *learnable structural skill* (expose
the model to some combinations → it transfers to new ones), or is it *memorization of
seen combinations* (exposure only helps the seen combos, held-out ones stay 0.000)?

This answers the "suggestive" claim in ch22 — that composition failure is likely
*structural-data* (exposure to combinations), not capacity.

## Setup

Same 0.88M pilot architecture (emb=128, 4 layers), same primitives-only split. But now
we add a **small number of composite operations to the training set**, split by
operation:

- **EXPOSED (trained):** `abs_add`, `sub_abs`, `sum_of_abs`  (120 examples)
- **HELD-OUT (tested):** `max_add`, `double_first`, `len_minus_one`  (120 examples)

Train on primitives + the 3 exposed composite ops (1500 steps, loss 5.79 → 0.019).
Then evaluate on three sets: held-out primitives (in-dist), exposed composites, and
held-out composites (the key question).

## Result

| Split | MODEL | TEMPLATE | RETRIEVAL |
|-------|-------|----------|-----------|
| In-distribution (held-out primitives) | **1.000** | 0.800 | 1.000 |
| Exposed composites (seen in training) | **0.667** | 0.000 | 0.000 |
| **Held-out composites (never seen)** | **0.000** | 0.000 | 0.000 |

## Interpretation

**Exposure does NOT unlock composition on unseen combinations.** The model learns the
*specific* composites it was shown (0.667 on exposed), but when asked to combine in a
way it never saw — even using primitives it knows perfectly (in-dist 1.000) — it
score **0.000**, exactly as before.

This is a **decisive negative result** on the book's central question:

- The composition wall is **not** simply "the model was never shown a combination."
- Seeing *some* combinations does **not** teach a general "combine two operations" skill.
- The learned behavior is **instance-specific**, not structural. The model memorized
  `abs_add` as a *new primitive*, not as "do abs, then add."

### What it rules out and doesn't

**Rules out:** the naive "just add some composites to the data" fix. Exposure to a
few combinations does not produce compositional generalization.

**Still open:** whether exposing the model to a much *larger* and more *systematic*
set of combinations (covering many primitive pairings) could teach the general
compose-operator — i.e. whether composition needs *structural* data (the generality of
the rule, not just a few instances). The diversity-vs-quantity finding suggests this
is plausible: diversity (many phrasings of the same meaning) is what built surface
robustness, so diversity of *combinations* might be what builds composition. But that's
now the next experiment, not something we've measured.

## Reproduce

```bash
TORCH_DISABLE_AVX2=1 python scripts/run_composition_exposure.py \
  --steps 1500 --n-embd 128 --n-layer 4 --n-head 4 --seed 0 \
  --out artifacts/checkpoints/stage4_exposure.pt --tag _pilot
```
