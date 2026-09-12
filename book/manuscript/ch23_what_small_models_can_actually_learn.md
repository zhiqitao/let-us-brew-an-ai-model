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
list sum) — operations that combine two things it knows. The model scores
**0.000**. It did not learn "I know abs and I know add, therefore I can do
abs+abs." This is a Level-4 failure under these schedules. The baseline systems
(which we designed to be easy) *also* scored 0.000 — a useful cross-check that the
failure is not unique to the learned model, though it is a measured negative, not a
proof that no method or shortcut could ever solve it.

## The two axes of the boundary

Put together, the results define a sharp boundary along two independent axes:

**Axis 1 — Surface form.** The model's knowledge is tied to the exact wording and
identifier names it saw. It does not generalize "sum of two numbers" as an abstract
concept; it generalizes "this sentence shape → this code." Change the surface, and
the capability evaporates.

**Axis 2 — Composition.** Even within a surface form it knows, the model did not
combine two learned pieces into a novel structure in our tests. It behaved as if it
lacked a compositional engine here.

**The honest conclusion in one sentence:**

> A ~0.9M model genuinely learns individual mappings and generalizes them across
> *instances*, but the knowledge is surface-tied (new wording → 0.000) and
> non-compositional (unseen combinations → 0.000) — and neither more capacity
> (up to 29.3M) nor more data (within what we tested) is close to fixing it *under the
> schedules we ran*.

## The capacity grid, in full

The sharpest negative result in the whole book is the model-size sweep, and it
deserves its own table because it is the claim a reader would most want to test.
We ran the composition experiment across a ~33× range of capacity. We did **not** hold
every hyperparameter constant — the runs used different step counts (see Appendix C),
so this is a sweep across capacity with some training-budget variation alongside it,
not a strictly-controlled size-only comparison.

| Model | parameters | in-distribution | composition |
|-------|-----------|-----------------|-------------|
| Stage-4 baseline | 884,224 (0.88M) | 0.900 | **0.000** |
| Scaling | 6,500,352 (6.5M) | 0.897 | **0.000** |
| 10M point | 10,195,776 (10.2M) | 0.773 | **0.000** |
| 30M point | 29,290,240 (29.3M) | 0.897 | **0.000** |

Four sizes. Composition is **0.000 at all four** under the schedules we ran. That is
the same number repeated across a 33× change in the one resource we might otherwise
blame. We would be careful not to over-read it: because the step counts differed,
this is evidence that capacity alone, under these runs, did not produce composition —
it is not a proof that capacity *cannot* (there may be a threshold, or different
training budgets, we did not reach). What we can say is that, across the capacity
range and schedules we tested, composition did not move off 0.000.

Two honest notes on the grid. First, in-distribution scores sit in a healthy plateau
(0.773–0.900) across all four sizes — capacity neither helped nor hurt the narrow task.
(One 10.2M reading of 0.383 turned out to be a training-run artifact.) Second,
in-distribution scores do not predict the composition result at all: the models that
reached 0.900 in-distribution scored 0.000 on composition, same as the one that
reached 0.773. Capacity that helps the shallow score does nothing for the deep one.

## What it's NOT, and why that matters

This is **not** evidence that the model is "stupid" or that the approach "doesn't
work." It is evidence about *what kind of capability small models acquire from this
kind of data*. The model is good at exactly what it was trained to do — map a narrow
phrasing to a narrow computation — and bad at the two things that separate "reflex"
from "capability": robustness to surface change, and composition.

The value of measuring this precisely is that it tells us *where* to look next. It is
not a shrug and a "small models are limited." It is a specific, falsifiable map: the
boundary is on surface-robustness and composition, not on in-distribution learning.

## What this means for the bigger picture

There is a tendency, when reading results like these, to draw a bleak conclusion:
"small models can't really learn, so this was a waste." That reading would be wrong
on both halves.

On the first half — small models *do* genuinely learn. The model reliably maps
natural language to correct Python at ~90% in-distribution, and it does so by
generalizing across instances, not by memorizing. That is real learning of a narrow
kind, and it should not be discounted.

On the second half — the effort was far from wasted. We now hold a precise,
measurement-backed boundary: on surface robustness (Level 3) and composition (Level 4),
this model's capability stops *under the setups we tested*. We are careful with the
word "structural" — we observe a boundary, we do not prove its cause; it could in
principle be an internal-representation limit, an optimization / training-budget
limit, or a generation-length limit, and we have not isolated which. That is the kind
of knowledge that changes what someone would try next. If a practitioner wants robust,
compositional capability, the map says: do not just scale up, and do not just add more
of the same data — instead consider changing the *structure* of the data (more
diversity, exposure to combinations) or the *inductive bias* of the model. Those are
directions worth testing; our results show the naive ones (more capacity, more of the
same data) did not work here, but they do not prove the tested alternatives will either.

So the honest takeaway is not "small models are inadequate." It is "small models
learn narrow mappings well, and the path to broader capability runs through different
kinds of data and different inductive structures — not merely more of what we already
have." That is a useful, and slightly counterintuitive, answer.

## Preferring "what these experiments showed"

Throughout, we deliberately avoid claiming things about "all small models." We can
only say what *this* model, on *this* task, with *this* data, did. And what it did is
both genuinely interesting (it learns!) and sharply bounded (it doesn't generalize
or compose).

That boundary — precise, measured, and honest — is the book's real deliverable.
