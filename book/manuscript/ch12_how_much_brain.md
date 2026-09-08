# 12. How Much Brain?

The most instinctive answer to "the model failed to compose" is: **make it bigger.**
More parameters, more capacity, more "brain." If a ~0.9M model can't combine what it
knows, surely a larger one can.

This chapter tests that instinct directly, and the answer is one of the cleanest
negative results in the book.

## The setup

We hold everything constant except model size. Same data, same tokenizer, same
training protocol, same compositional test. We train **two** models on the same
primitive-only training set and test both on (a) in-distribution held-out primitives
and (b) the held-out composite operations.

| Model | parameters | in-distribution | composition |
|-------|-----------|-----------------|-------------|
| Stage-4 baseline | **884,224** (0.88M) | 0.900 | **0.000** |
| Scaling | **6,500,352** (6.5M) | 0.900 | **0.000** |

That is a **7.4×** increase in parameters. Almost nothing changed.

## The result

Going from ~0.9M to 6.5M parameters:

- **In-distribution stays at 0.900.** The bigger model reproduces the primitives
  exactly as well as the small one. Capacity didn't hurt; it just didn't add anything
  here.
- **Composition stays at 0.000.** The bigger model is *just as* unable to combine two
  learned primitives as the small one. Seven and a half times the capacity bought
  exactly zero compositional generalization.

## What this means

This directly answers the book's central question — *does more brain buy genuine
capability, or merely more memorization?* — with a decisive answer at this scale:

> **It buys neither. At ~1–7M parameters, the compositional failure is invariant to
> model size.**

The boundary we found in Chapter 16 is **not a capacity ceiling**. It is a
structural/learning limit that scaling alone does not resolve. A bigger model at this
scale just does the same narrow thing slightly more efficiently; it does not develop
the ability to compose.

## The audit: is this a fair comparison?

We must be careful: a single size point doesn't prove there's no capacity curve. But
the shape of the result is telling. If capacity were the binding constraint, we'd
expect a *move* — even a small one — between 0.88M and 6.5M. We see none: composition
is 0.000 at both. And crucially, both models are already at ceiling (0.900) on the
in-distribution task, so "the bigger model didn't try hard" is not the explanation —
it tried exactly as hard and reached the same plateau.

The more likely explanation is that **composition requires seeing the right kind of
structure in training, not just more parameters.** A model that only ever sees
`add` and `abs` as separate problems has no reason to build a "compose" operator; a
7× bigger network just represents the same two reflexes more richly. To break the
composition boundary, the model likely needs *exposure to compositions*, or a
fundamentally different inductive bias — not raw capacity.

## The honest framing

This is a *useful* negative result. It tells us where not to look (raw scaling in the
1–7M regime) and points at where to look instead (structural data / inductive bias).
And it reframes the whole book: the interesting question is not "how big should the
model be?" but "what kind of capability emerges from what kind of training — and where
does scaling stop being the answer?"

The model was the instrument. The experiment — and the boundary it revealed — was the
subject.
