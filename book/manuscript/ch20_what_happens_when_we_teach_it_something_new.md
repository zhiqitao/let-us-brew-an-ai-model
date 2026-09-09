# 20. What Happens When We Teach It Something New?

Every chapter so far has asked how the model handles one task. But real capability
isn't learned in one shot — it's *grown*, by adding new things over time. That raises
the question at the heart of continual learning: when you teach a model something new,
does the new thing stick — and does the model **keep** the old things?

There's a well-known failure mode with a scary name: **catastrophic forgetting** — the
tendency of a model, after training on task B, to lose what it learned on task A. We
want to know whether that happens to our small model, and, crucially, whether the
*way* we train determines it.

Think of it like learning a new language. If you study French for a year, then stop
and study Spanish exclusively, how much French do you still have? It depends a lot on
whether you keep practicing French while learning Spanish — which is exactly what this
experiment tests.

## The setup

We split the operations into two capabilities:

- **Capability A — arithmetic:** `add`, `sub`, `mul`, `max_of`, `min_of`.
- **Capability B — lists:** `list_sum`, `list_len`, `first_element`.

We train on A, then introduce B, and measure both:
- **B acquisition** — did it learn the new capability?
- **A retention** — did it keep the old one, or did learning B destroy it?

We run this under two protocols, changing only the *order and mixing*, not the model,
data, or optimizer:

- **sequential:** learn A fully, then learn B with no A exposure.
- **replay / mixed:** interleave A and B examples throughout.

## The result
![Continual learning](figures/fig_continual.png)

| Protocol | **A-retention** | **B-acquisition** |
|----------|-----------------|-------------------|
| **sequential** | **0.000** | 0.889 |
| **replay**     | **1.000** | 0.889 |

This is as clean a result as this book produced.

**Sequential training causes catastrophic forgetting.** After learning arithmetic and
then lists in sequence, the model's A-retention is **0.000** — it completely forgot
the first capability. That is not "degraded"; it is gone. Learning the lists overwrote
the arithmetic.

**Replay prevents it, with zero cost.** When A and B are interleaved throughout, the
model's A-retention is a perfect **1.000**, and B-acquisition is **0.889** — identical
to sequential. So replay bought complete retention of the old capability with **no
trade-off whatsoever** in learning the new one.

## What this teaches

This is the clearest case in the book where the **training protocol, not the model or
the data, determines the outcome.** Same model. Same data. Same optimizer. The only
difference is whether the first capability stays "in the mix" while the second is
learned. Sequential forgets; replay retains.

The lesson generalizes directly: when you add a new capability to a model, *how* you
do it matters more than any property of the model itself. If you let the new task
dominate the gradient signal and remove the old data, the old capability collapses.
If you keep old and new interleaved, the model can hold both.

And it reframes a common assumption. People often reach for "a bigger model" when
confronted with a model that forgets. This experiment shows the forgetting was never
a capacity problem — a ~0.9M model holds both capabilities perfectly under replay. It
was a *training procedure* problem.

The pattern here echoes a deeper truth we've seen all book: the headline number
("did it learn the new thing?") hides the interesting failure ("what did it lose to
get there?"). Measuring B acquisition alone would have made sequential training look
like a success — 0.889, great. Measuring A retention reveals the cost. The lesson is
to always measure *both* the new and the old.

## The shortcut audit

1. **Suspected shortcut: the 0.000 A-retention is an artifact of how we score A.**
   **Why it could explain it:** maybe the A test is too hard, or the model just needs
   more steps.
   **Control:** replay mode, identical A test — A-retention 1.000.
   **What it rules out:** a broken A test. The same test that scores 0.000 in
   sequential scores 1.000 in replay.
   **What remains:** whether this holds for three or more capabilities, and whether
   replay-adds support *composition* of A and B after the fact.

## The honest summary

Acquiring a new capability can destroy an old one — and it is entirely up to how you
train. Sequential training forgets; replay retains with no cost. This is a controlled,
reproducible demonstration that catastrophic forgetting is a procedure problem, and
it is one of the most practically useful results in the book.
