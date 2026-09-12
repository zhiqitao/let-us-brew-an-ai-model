# 13. Same Data, More Diverse Data

Chapter 11 asked *how much* data. There's a subtler question that often matters more:
what *kind* of data. Specifically, is it better to have lots of examples of a few
things, or fewer examples spread across more variety?

The easy answer is to treat "more data" as one lever. It isn't. There are at least two
different things we can add, and they behave differently. It is like teaching a
kid shapes. Show them a hundred triangles and they'll recognize triangles. Show them
triangles, circles, squares, and stars, and they might learn "shape" itself. Same
number of examples, very different kind of learning.

- **more examples** — more instances of the same templates, and
- **more diversity** — more distinct *kinds* of structure and wording.

The distinction is important enough to state as a rule:

> **More data ≠ more information ≠ more diversity.**

And this is the chapter where we stop treating it as a hunch and measure it directly.
Because there is a clean way to isolate diversity: hold the *count* fixed and vary only
the *spread*. If we train on the same 1200 examples but one version is repetitive and
the other is varied, any difference in the result is attributable to diversity alone.

## What our experiments hinted
![Diversity vs quantity](figures/fig_diversity.png)

The data-scaling curve (Chapter 11) showed that simply adding *examples* of the same
sort climbs in-distribution performance — 0.10 at 100, 0.64 at 3000. So more examples
clearly helped the model fit the pilot task better.

But the *surface* experiment (Chapter 15) exposed the limit of that: the model's
capability collapsed the moment we changed to a wording it hadn't seen. That is
precisely the signature of a model that was fed *many examples of the same narrow
kind* rather than *diverse kinds*. It learned the particular phrasings well because it
saw many of them, and it learned nothing general because the diversity was low.

In other words, the very quantity that produced the impressive in-distribution score
is what made it surface-fragile. The model was well-fed but narrow.

## The direct test: same count, different diversity

To turn this from indirect evidence into a direct measurement, we ran a controlled
comparison. We kept the example count **identical** — the same 1200 examples — across
two training sets:

- **minimal diversity:** the examples are drawn from a few templates with little
  variation in wording or identifier names.
- **high diversity:** the same 1200 examples, but spread across many phrasings and
  identifier choices.

Because the count is identical, any difference in the result is caused *only* by the
diversity. This is a clean one-variable experiment, and it is the strongest test of the
hypothesis.

## The measured result

Here is what came out. This is, in our view, the single most actionable number in the
whole book.

| Training set | in-distribution | surface |
|--------------|-----------------|---------|
| **minimal diversity** | 0.500 | **0.000** |
| **high diversity** | **1.000** | **1.000** |

Let us read this carefully. Same number of examples — 1200 in both cases. But the two
models behaved completely differently.

- **Minimal diversity:** in-distribution 0.500, surface 0.000. The model did okay on
  the narrow task (0.500) but was completely brittle to any surface change (0.000). It
  learned the few phrasings it was given and nothing about the *idea*.
- **High diversity:** in-distribution **1.000**, surface **1.000**. The model mastered
  the task *and* held up perfectly under surface change. It learned the actual
  operation, not a phrasing.

That is a swing from 0.500/0.000 to 1.000/1.000 — all from changing *how* the examples
varied, not *how many* there were. The same count. The same model. Only the diversity
differed.

## What this really means

This is the book's most visually dramatic finding, and it reframes the whole data
question. It is not that "more data is better." It is that **the kind of variation in
the data changes what the model can do.**

A model fed many examples of few phrasings memorizes the phrasings. A model fed the
same number of examples spread across many phrasings comes to cover far more of the
surface space. We cannot say from this experiment alone that it has "learned the
underlying operation" in the strong sense — that would require a wording family it
was *never* trained on, which this design does not test (see the caveat below). What
the result shows is a large and real shift in coverage: the diverse model gets 1.000
where the narrow model gets 0.000, and the *only* change is diversity of the training
set. That is a strong lever, even before we claim it forces abstraction.

## An honest limit: coverage vs. generalization

Before we claim too much, we have to be precise about what that 1.000 surface score
actually measured. The surface test used word-identifiers and a *randomly-chosen*
wording family per operation. The high-diversity training set, however, contained
*all* the wording families and *both* identifier-sets. So the surface test's wording
(and its identifiers) may well have been *present in the high-diversity training set*
— which makes the 1.000 at least partly a measure of **coverage** (the model had seen
that surface), not of generalization to a surface it had never encountered.

The minimal→0.000 result is unambiguous: that model saw only a narrow slice, so the
surface test was genuinely unseen and it failed. But the high→1.000 result is
strongest as a statement about **coverage**: diverse training covers more surfaces.
Whether it generalizes to a wording *family it never saw* is a separate question this
design does **not** answer — that would need a held-out family excluded from the
diverse pool. We flag this honestly, because the strong reading ("diversity produces
generalization to unseen surfaces") is not fully established by this experiment as run.

### This chapter vs. Chapter 15: two different "surface" tests

It is easy to blur these two, so let us keep them apart. Both test surface change, but
they answer different questions:

| | Chapter 13 (this chapter) | Chapter 15 (Stage 3) |
|---|---------------------------|----------------------|
| Training wording | minimal (few families) or high (all families, both id-sets) | all-but-the-last family per op |
| Test surface | same family set the model trained on (coverage) | the **held-out last family** the model never saw |
| What 1.000 / 0.000 means | coverage of surfaces *within* the training family | generalization to a wording family *excluded* from training |
| Valid conclusion | high diversity covers more surface | narrow training fails on a genuinely unseen family |

The Chapter 15 result is a genuine held-out-family test (a dedup audit confirms the
held-out wording family does not appear in training). The Chapter 13 result is a
coverage demonstration. Only Chapter 15 speaks to generalization to a *never-seen*
wording; Chapter 13 shows diversity widens the covered surface.

## The honest caveat

It is worth noting that this experiment measured *surface* diversity. It showed that
varying phrasing and identifiers makes the model robust to surface change (the Level-3
boundary). It does **not** show that diversity fixes *compositional* generalization
(the Level-4 boundary) — that is a separate, harder question. Whether the same lever
helps a model combine two things it knows is the most natural next experiment, and it
is called out in the conclusion.

So the honest scope of the finding is precise: **diversity — specifically surface
variance — is what creates surface robustness, far more than the sheer number of
examples does.** Whether diversity reaches deeper, into composition, remains open.

## The lesson

This reframes what "more data" buys. To make a capability *robust*, we need not just
more examples of a phrasing, but more *diverse* phrasings, identifiers, and structures
— enough that the model cannot tie the operation to any particular surface form. Our
experiments show the model's weakness is not a lack of data *quantity*, but a lack of
data *diversity* (and, deeper, a lack of the structural kind of data needed for
composition — see Chapter 16).

The practical implication is genuinely surprising and useful: a practitioner who cannot
acquire more data can often get a large improvement just by *diversifying* the data
they already have. Re-phrasing the same examples, varying the identifiers, and
spreading across template families can turn a brittle 0.500/0.000 model into a robust
1.000/1.000 — with zero additional data. That is the kind of result that changes how a dataset would actually be built.
