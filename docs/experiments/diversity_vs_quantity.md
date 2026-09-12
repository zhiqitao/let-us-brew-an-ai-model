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

## Interpretation — the hypothesis is confirmed (with an important caveat)

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

## Caveat — coverage vs. generalization (an honest limitation)

The reviewer's question is fair, and we have to be precise about what the surface
score actually measures here. In `run_diversity.py`, the surface test is built with
`id_set="words"` and **no explicit `family`**, so the renderer picks a *random* family
per operation (`family=None` → `rng.choice(fams)`). The high-diversity training pool,
however, contains **all** families × **both** id-sets (letters + words).

That means the surface test's word-identifiers *and* its (randomly-chosen) family were
**both present in the high-diversity training set**. So the high-diversity **1.000** on
the surface test is, at least in part, **coverage** — the model had seen that surface —
rather than generalization to a wording family it had never seen. By contrast, the
minimal-diversity model saw only the first family × letters, so the surface test was
genuinely unseen for it, and its 0.000 is a real generalization failure.

**Consequence:** the minimal→0.000 vs high→1.000 gap is real and reproducible, but the
strong reading — "diversity produces generalization to *unseen* surfaces" — is **not**
fully established by this design. What it does establish is that
**diverse training covers more surfaces.** Whether the diverse model generalizes to a
genuinely held-out *family* (not just held-out identifiers) is a separate, untested
question — it would need a test family excluded from the diverse training pool. This is
recorded as a known limitation and is exactly the kind of control the book should run
before claiming the strong version.

## Reproduce
```bash
python scripts/run_diversity.py --steps 900 --n-train 1200
```
