# Experiment — Composition structural diversity: does diversifying composite exposure unlock composition?

Status: `[MEASURED]` — real run, manifest at `artifacts/manifests/composition_diversity_pilot.json`.

## The question

The reviews flagged: is composition, like surface robustness in ch13, a **diversity**
lever? The naive exposure experiment (run_composition_exposure.py) showed that feeding
a FEW composites does not unlock composition on unseen ones (held-out 0.000). That
leaves one possibility: maybe what's missing is DIVERSITY of composite exposure, not
just any exposure. This mirrors the ch13 finding where the SAME example count, spread
across many phrasings, built surface robustness that minimal diversity did not.

## Setup

Hold out ONE composite operation entirely (the transfer test):
- **HELD OUT:** `len_minus_one` (never seen in any form)

Expose the other FIVE composite ops (`abs_add, sub_abs, sum_of_abs, max_add,
double_first`) to training, under two diversity conditions (same 120-example budget):

- **minimal_diversity:** `letters` id-set only (narrow surface)
- **high_diversity:** both `letters` + `words` id-sets (diverse surface)

Train on primitives + exposed composites (1500 steps, 0.88M pilot). Test on:
in-dist primitives, exposed composites, and the HELD-OUT composite op.

## Result

| mode | in-dist | exposed composite | HELD-OUT composite |
|------|---------|-------------------|--------------------|
| minimal_diversity | 1.000 | 0.592 | **0.000** |
| high_diversity    | 1.000 | 0.550 | **0.000** |

## Interpretation — composition is NOT a diversity lever

**Both conditions fail identically on the held-out composite (0.000).** Even with
high structural diversity (diversified surface across five composite operations), the
model cannot combine primitives into a composite operation it never saw — exactly as
it could not with minimal diversity. The 5 composite ops it WAS shown are learned
(~0.55–0.59), but the transfer to a never-seen combination does not happen.

This is a decisive negative on the diversity hypothesis:

- Surface robustness (ch13) IS a diversity lever — diversifying phrasings/identifiers
  builds it. Composition is NOT, at least not via diversifying the *surface* of
  composites.
- Diversifying the *expression* of combinations does not teach the *operator*. The
  model learns the specific combinations as new primitives, not a general
  "combine two operations" rule.

### What it rules out and doesn't

**Rules out:** "diversify the phrasing of the composite examples" as the fix. The
diversity lever that worked for surface (ch13) does not transfer to composition.

**Still open:** diversifying the *structure* of the combinations themselves — i.e.
exposing the model to many DIFFERENT primitive-pairings (not just different phrasings
of the same 5 pairings). That is a genuinely different axis. The ch13 analogy is only
partial: surface diversity diversifies the "outer form"; composition would need
diversity of the "inner structure." This experiment tested the former and it failed;
testing the latter is the remaining open question.

## Reproduce

```bash
TORCH_DISABLE_AVX2=1 python scripts/run_composition_diversity.py \
  --steps 1500 --n-embd 128 --n-layer 4 --n-head 4 --seed 0 \
  --exposed-budget 120 --out artifacts/checkpoints --tag _pilot
```
