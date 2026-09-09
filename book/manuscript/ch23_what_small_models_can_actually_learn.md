# 23. What Small Models Can Actually Learn

We have run a small, disciplined set of experiments and measured a coherent boundary.
Let us now state, carefully and honestly, what the experiments showed — the
synthesis the whole book has been assembling.

Everything below is scoped to **our** setup: a ~0.9M–29.3M decoder-only transformer,
trained on a few thousand generated natural-language-to-Python tasks, evaluated by a
mutation-tested execution-based judge. These are claims about this brew, not
universal laws about all small models.

## What the model can do

**It can learn individual operations well.** On in-distribution primitives — `add`,
`sub`, `mul`, `max`, `abs`, `list_sum` — the ~0.9M model solves ~90% of held-out
problems under greedy decoding. It beats a hand-written template rule system (0.900
vs 0.800). This is real, measurable capability on a narrow task.

**It generalizes across instances, not just examples.** It passed 59/60 held-out
prompts and, on a *canary* it had never seen, produced the *general* program rather
than a memorized literal. So for a single operation, the model is a learner, not a
parrot. That is Level-2 distributional generalization, achieved.

## What the model cannot do

**It cannot survive changes to the surface form.** Change the variable names from
`a,b` to `left,right` (identical computation) and performance falls to 0.350.
Rephrase the instruction with a wording family the model never saw (identical
computation) and performance falls to **0.000** — below *both* baselines. This is
Level-3 failure: the model's capability is **anchored to the phrasing**, not grounded
in the computation.

**It cannot compose what it knows.** Train on `add`, `sub`, `abs`, `max`, `list_sum`
as separate primitives; test on `abs_add` (abs then add) and `sum_of_abs` (abs over a
list sum) — operations that combine two things it knows perfectly. The model scores
**0.000**. It did not learn "I know abs and I know add, therefore I can do
abs+abs." This is Level-4 structural failure. And crucially, the baseline systems
*also* scored 0.000 — so the test is fair, and the only way to solve it would be
genuine composition, which the model lacks.

## The two axes of the boundary

Put together, the results define a sharp boundary along two independent axes:

**Axis 1 — Surface form.** The model's knowledge is tied to the exact wording and
identifier names it saw. It does not generalize "sum of two numbers" as an abstract
concept; it generalizes "this sentence shape → this code." Change the surface, and
the capability evaporates.

**Axis 2 — Composition.** Even within a surface form it knows, the model cannot
combine two learned pieces into a novel structure. It has reflexes, not a
compositional engine.

**The honest conclusion in one sentence:**

> A ~0.9M model genuinely learns individual mappings and generalizes them across
> *instances*, but the knowledge is surface-tied (new wording → 0.000) and
> non-compositional (unseen combinations → 0.000) — and neither more capacity
> (up to 29.3M) nor more data (within what we tested) is close to fixing it.

## What it's NOT, and why that matters

This is **not** evidence that the model is "stupid" or that the approach "doesn't
work." It is evidence about *what kind of capability small models acquire from this
kind of data*. The model is good at exactly what it was trained to do — map a narrow
phrasing to a narrow computation — and bad at the two things that separate "reflex"
from "capability": robustness to surface change, and composition.

The value of measuring this precisely is that it tells us *where* to look next. It is
not a shrug and a "small models are limited." It is a specific, falsifiable map: the
boundary is on surface-robustness and composition, not on in-distribution learning.

## Preferring "what these experiments showed"

Throughout, we deliberately avoid claiming things about "all small models." We can
only say what *this* model, on *this* task, with *this* data, did. And what it did is
both genuinely interesting (it learns!) and sharply bounded (it doesn't generalize
or compose).

That boundary — precise, measured, and honest — is the book's real deliverable.
