# 19. The Capability Ladder Revisited

We've climbed parts of the ladder through the experiments. This chapter pulls together
what we found into the picture the ladder was always meant to give us: a map of where
capability appears, where it holds, and where it breaks.

The ladder is a staircase of increasingly demanding skills. We can see how many steps the model climbed — and, more interestingly, the exact step where it
stopped, and what it took to get there.

The funny thing about building a ladder is that the interesting discovery is rarely how high we can climb. It is finding the precise rung where the footing gives out, and trying everything we can to get past it — so that we know, with real confidence, where the boundary lies.

## The ladder, with the measured results

| Level | Capability | Measured result |
|-------|-----------|-----------------|
| 1 | arithmetic | ✅ learned, ~0.90 in-dist |
| 2–3 | variables, conditionals | ✅ learned |
| 4–5 | lists, indexing | ✅ learned |
| 6 | loops | ✅ learned |
| 7 | **composition** | ❌ **0.000** — the wall |
| 8 | simple functions | not isolated |

The model climbed the early rungs cleanly. It stopped at **composition**.

## Where capability appears, holds, and breaks

**Appears:** individual operations are learned reliably (~0.90 in-distribution) and
generalize across *instances* (held-out + canary → general program). The model is a
genuine learner for a single operation.

**Holds only within a surface form.** The moment the surface changes — different
variable names, or a different way of saying the same instruction — the capability
collapses (0.350 on new identifiers, **0.000** on new wording). So the early rungs are
not *robust*; they are *phrasing-tied*.

**Breaks at composition.** The most important boundary: the model cannot combine two
things it knows. `abs` + `add` → 0.000, even though it knows both. And this break is
**invariant to scale** — it survives across the full size range we tested.

## The model-size and data-size boundaries

This is where the breadth of the brew matters. We did not test just one bigger model;
we tested four, and we also scaled the data. Here are the real numbers.

- **Model size:** we ran the composition test across a ~33× range of capacity — a
  0.88M pilot, a 6.5M model, a 10.2M model, and a 29.3M model. All four scored
  **0.000** on composition. (Their in-distribution scores were 0.900, 0.897, 0.773,
  and 0.897 respectively — a stable plateau. One earlier 10.2M reading of 0.383
  turned out to be a training-run artifact.) The composition wall is not a capacity
  ceiling in this regime.
- **Data size:** 100 → 3000 examples improved in-distribution (0.10 → 0.64) but did not
  touch composition. More quantity helps the shallow score, not the deep boundary.

## The failure map

| Failure mode | On what the model breaks |
|--------------|--------------------------|
| Surface fragility | new wording → 0.000; new identifiers → 0.350 |
| Composition | unseen combination of known primitives → 0.000 |
| Continual forgetting | sequential A→B destroys A (0.000); replay fixes (1.000) |

## What the ladder finally tells us

The ladder is not a shelf of "caps" the model unlocks. It is a map of *where the
boundary lies*. For our ~0.9M model:

- it genuinely climbs the individual-capability rungs,
- but each rung is **surface-tied**, not robust,
- and the ladder stops at **composition** — the one thing that separates "a bag of
  reflexes" from "capability."

And the most useful part: this map is honest about *what doesn't change it*. The
composition boundary survived a ~33× capacity increase and a 30× data increase. That
is a strong, falsifiable statement about where the limit lives and where it does *not*
live — which points the next investigation at *structural* data and inductive bias,
not at scaling.

There is also a quiet lesson in the shape of the map. The model is not uniformly good
or uniformly bad. It is good at one thing — reproducing a single operation it was
shown — and bad at everything that requires putting operations together. That shape
is far more informative than a single performance number, because it tells us exactly
where nature of the limitation lives and where it does not.
