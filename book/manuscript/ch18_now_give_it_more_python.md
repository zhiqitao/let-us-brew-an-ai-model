# 18. Now Give It More Python

Our pilot model lived inside a deliberately small corner of Python — a bit of
arithmetic, a couple of comparisons, a few list operations, some basic if/else. That
tiny corner is what let us measure capability cleanly: change one small thing at a
time and watch what happens.

But a capability map drawn on one tiny corner only tells you where the boundary is
*for that corner.* Real capability grows by letting the model use more of the language.
This chapter is about the **capability ladder** — the discipline of widening what the
model may do, one controlled step at a time, so we can watch exactly where it starts
to fall apart.

## The ladder

We planned a progression of controlled Python capabilities:

| Level | Capability | Example |
|-------|-----------|---------|
| 1 | arithmetic | `return a + b` |
| 2 | variables | `total = 0` |
| 3 | comparisons / conditionals | `if a > b` |
| 4 | lists | `xs[0]`, `len(xs)` |
| 5 | indexing | `xs[i]` |
| 6 | loops | `for x in xs` |
| 7 | nested composition | two operations at once |
| 8 | simple functions | `def f(x): ...` |

For each we would: define it, generate data for it, train on it, evaluate it, audit
shortcuts, and record the result — *before* moving to the next rung.

## What the pilot showed us about the ladder

We did not climb the whole ladder in this book's first pass — we built the mechanism
that *allows* climbing it. But the pilot already revealed where the ladder's later
rungs get hard, and it is not where you'd guess.

The pilot handled arithmetic and simple lists well in-distribution (Level 1–4, ~0.90).
The break came at **composition** — combining two learned operations — which is the
heart of Level 7. And crucially, that break was *not* about adding more Python syntax.
The model already knew the syntax of `abs` and `add`; it just couldn't put them
together.

So the ladder's real dividing line is not "how much Python," it is "can it *compose*
the Python it already knows." That is the boundary the book is really about.

## The discipline that matters

The ladder enforces the one-variable-at-a-time rule. You do not add lists, loops,
and functions all at once — you add one and re-measure. This is what lets you attribute
a change in capability to a specific change in allowed Python.

And it is a *ladder*, not a guarantee. The model may stop climbing at any rung, and
that stopping point is itself a result. We found the stop at composition: the model
can do each rung's primitives, but cannot combine them. That finding — cheap and
specific — is worth more than a glossy claim of having "reached Python Level 8."
