# Experiment — Chapter 13: Quantity vs. Diversity (the isolation test)

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/diversity.json`.

## Setup
Hold example count (1200) and model/training constant. Compare two datasets of equal
size but different composition:
- **minimal_diversity:** many examples of a FEW phrasings and ONE identifier-set
  (letters), so the model sees many examples of essentially the same surface.
- **high_diversity:** the same example count spread across MANY phrasings and BOTH
  identifier-sets (letters + words).

Measure on each: in-distribution pass@1 AND surface-robustness (new identifiers +
reworded instructions).

## Result

| Mode | in-distribution pass@1 | **surface pass@1** |
|------|------------------------|--------------------|
| **minimal_diversity** | 0.500 | **0.000** |
| **high_diversity**     | **1.000** | **1.000** |

## Interpretation — the hypothesis is confirmed

With the **same number of examples**, the outcome is entirely determined by *diversity*:

1. **Minimal diversity → surface-fragile.** Seeing many examples of few phrasings gets
   the model to 0.500 in-distribution, but it **completely fails (0.000)** when the
   surface changes. It learned to associate specific phrasing with the code, not the
   underlying operation.

2. **High diversity → robust.** Spreading the same examples across many phrasings and
   identifier-sets gets the model to **1.000 in-distribution AND 1.000 on surface
   change.** When the model can't rely on any particular phrasing, it's forced to
   learn the actual computation — and that generalizes.

This cleanly separates the two levers and answers the question Chapter 13 raised:
**it is diversity, not quantity, that creates robust, surface-generalizing
capability.** More examples of the same thing just deepens the phrasing association;
more *variety* is what forces the model to learn the underlying idea.

## Why this matters
This is the strongest direct evidence in the book for what actually drives
generalization. It also reframes the earlier surface and composition results: the
surface fragility of the pilot model was a *data-diversity* problem, one that is
fixable by training on more diverse phrasings/identifiers. (Composition — Chapter 16 —
is a separate, deeper limit not resolved by surface diversity.)

## Reproduce
```bash
python scripts/run_diversity.py --steps 900 --n-train 1200
```
