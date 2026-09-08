# 13. Same Data, More Diverse Data

Chapter 11 asked *how much* data. There's a subtler question that often matters more:
what *kind* of data. Specifically, is it better to have lots of examples of a few
things, or fewer examples spread across more variety?

The easy answer is to treat "more data" as one lever. It isn't. There are at least two
different things you can add, and they behave differently. Think of it like teaching a
kid shapes. Show them a hundred triangles and they'll recognize triangles. Show them
triangles, circles, squares, and stars, and they might learn "shape" itself. Same
number of examples, very different kind of learning.

- **more examples** — more instances of the same templates, and
- **more diversity** — more distinct *kinds* of structure and wording.

The distinction is important enough to state as a rule:

> **More data ≠ more information ≠ more diversity.**

## What our experiments hinted

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

## The lesson

This reframes what "more data" buys. To make a capability *robust*, you need not just
more examples of a phrasing, but more *diverse* phrasings, identifiers, and structures
— enough that the model cannot tie the operation to any particular surface form. Our
experiments show the model's weakness is not a lack of data *quantity*, but a lack of
data *diversity* (or, deeper, a lack of the structural kind of data needed for
composition — see Chapter 16).

## A caution on the distinction

We have not fully separated "more examples" from "more diversity" in a single
controlled experiment — that factor is worth isolating. But the *indirect* evidence is
strong and consistent: quantity alone drove up the surface-fragile in-distribution
score, while the failures that matter (new wording, new identifiers, composition) all
point to a diversity and structure gap, not a quantity gap.

The honest conclusion is that these are different levers, we have strong evidence that
quantity helps the narrow score, and we have reason to believe diversity — not quantity
— is what robustness requires. Isolating that directly is a natural next experiment.
