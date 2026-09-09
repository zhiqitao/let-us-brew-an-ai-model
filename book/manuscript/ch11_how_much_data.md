# 11. How Much Data?

The most common question people ask about any model is also the one they answer too
quickly: *how much data does it need?* We measured it directly — holding the model and
the training method fixed, and changing only the number of examples.

Think of it like studying for a test. Read one page and you'll fail. Read a bit more
and you'll still fail. But there's a point where reading enough actually clicks and
you start passing. Where's that point for a model? That's what this experiment finds.

## The setup

We train the same ~0.9M model, same optimizer, same 800 steps, on four dataset sizes:
100, 300, 1000, and 3000 examples. Then we measure in-distribution pass@1 on a
held-out pool.

## The result

| dataset size | final train loss | **pass@1 (held-out)** |
|--------------|------------------|-----------------------|
| 100          | ~0.000           | **0.100**             |
| 300          | ~0.000           | **0.098**             |
| 1000         | 0.022            | **0.300**             |
| 3000         | 0.025            | **0.641**             |

## What it tells us
![Data scaling](figures/fig_data_scaling.png)

**More data clearly helps in-distribution.** pass@1 climbs as the dataset grows, from
0.10 at 100 examples to 0.64 at 3000. The model needs substantial data to learn even
this narrow mapping.

**There is a small-data plateau.** At 100 and 300 examples the model is essentially
identical (~0.10). The improvement only becomes substantial between 1000 and 3000. So
there is a *threshold* below which the model gets almost nothing and above which
performance climbs. That threshold is a real, measurable property of the task and
model.

## The motif, restated

Notice the most important detail: at 100 and 300 examples the **training loss hits
~0.000** — the model has *memorized* its tiny training set — yet pass@1 is only ~0.10.
A loss of zero on a small set buys almost nothing on unseen examples.

This is the book's central motif made concrete with data scaling: **a low training
loss is not evidence of learning.** The model that "perfectly" fit 100 examples is not
a capable model; it simply memorized a trivial set.

## The honest caveat

This experiment measured *quantity*. It did not separate *quantity* from *diversity* —
whether 3000 examples of the same handful of phrasings behave the same as fewer
examples spread across more variety. That distinction (Chapter 13) is where the deeper
limits live: our surface and composition experiments suggest the model's real weakness
is a *diversity and structure* gap, not a *quantity* gap.

## The practical answer

For a single narrow operation on a ~0.9M model, you need on the order of thousands of
examples before in-distribution performance becomes workable. Below that, the model
memorizes its tiny set and gains nothing on unseen problems. And — anticipating the
rest of the book — even at 3000 examples the model is still surface-fragile and
non-compositional, because those limits come from the *kind* of data and the model's
inductive structure, not from the sheer *amount*.
