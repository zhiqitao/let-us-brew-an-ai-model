# 11. How Much Data?

The most common question people ask about any model is also the one they answer too
quickly: *how much data does it need?* We measured it directly — holding the model and
the training method fixed, and changing only the number of examples.

It is like studying for a test. Read one page and we fail. Read a bit more
and we still fail. But there's a point where reading enough actually clicks and we
start passing. Where's that point for a model? That's what this experiment finds.

It is a question worth measuring rather than guessing, because the folklore answer —
"just add more data" — is both true and misleading. More data does help. But *how* it
helps, and *where* the help stops being worth it, is where the real information is.
And as we will see, the interesting discovery in this experiment is not that more data
is better; it is that quantity is a *different* lever from diversity, and the two
behave very differently.

## The setup

We train the same ~0.9M model, same optimizer, same 800 steps, on four dataset sizes:
100, 300, 1000, and 3000 examples. Then we measure in-distribution pass@1 on a
held-out pool.

Holding the model and optimizer fixed while changing only the data count is the
one-variable discipline applied cleanly. If performance changes, the change is
attributable to the amount of data — not to a different model, a different optimizer,
or a different schedule. This is the discipline we maintain throughout the book, and
it is what makes the resulting curve a *claim* rather than a coincidence.

## The result

| dataset size | final train loss | **pass@1 (held-out)** |
|--------------|------------------|-----------------------|
| 100          | ~0.000           | **0.100**             |
| 300          | ~0.000           | **0.098**             |
| 1000         | 0.022            | **0.300**             |
| 3000         | 0.025            | **0.641**             |

## What it tells us
![Data scaling](figures/fig_data_scaling.png)

*Every point is one run on a common held-out test set (one `pool_test`, 540 records = 10
operations × 54 each after the per-op train/test split, reused across sizes), so the
rates are integer fractions over 540 (54/540 = 0.100, 53/540 = 0.098, 162/540 = 0.300,
346/540 = 0.641). Four points describe a trend under these budgets, not a sharp
threshold.*

One honest caveat about what "more data" means here. Within a single operation family,
the records we generate share the same prompt→program mapping and differ only in
hidden-test *input values*; across the whole run, the pilot's 1,400 records contain only
**21 distinct prompt–program pairs**. So increasing the dataset size from 100 to 3000
records does **not** give the model 30× more distinct information — it gives it more
records of mostly the same mappings, and because the per-operation pools are built
separately and then concatenated, the *selection order* matters. Also, since the step
count is held fixed, a larger dataset means **fewer passes** over each record, not more
optimizer exposure. So the curve is best read as "given this coverage and this
repetition pattern, accuracy rose" rather than "more information bought more accuracy."
That is part of why Chapter 13 — which genuinely varies the wording families — is the
proper test of information content, and it is why we do not claim this chapter shows a
composition result (it measured familiar-task performance only).

**More data clearly helps in-distribution.** pass@1 climbs as the dataset grows, from
0.10 at 100 examples to 0.64 at 3000. Under these budgets, this narrow mapping needs
more records to reach a higher score — though, as noted above, the "more data" here is
more records of a small set of mappings, not more distinct information.

**There is a small-data plateau.** At 100 and 300 examples the model is essentially
identical (~0.10). The improvement only becomes substantial between 1000 and 3000. So
under these budgets, there is a *plateau-then-rise* pattern: below roughly 1000 examples
the model gets almost nothing, and above that it climbs. This is an **observed trend on
four points with one run each**, not an inferred sharp threshold with a precisely
locatable knee. Call it a qualitative plateau, and read no more into the exact
crossover point than the four points support.

This is the shape that matters. It is not a smooth, gentle rise. Under these budgets it
reads as a flat line, then a climb. That flat-then-steep shape is *consistent* with the
model needing more records before the familiar-task score rises — but we cannot state a
clean minimum-data requirement, because we did not audit which operations and unique
prompt–program pairs actually occur in the small (100/300) subsets. A score near 0.10
across ten operations could reflect restricted operation coverage rather than an
inability to learn from a few hundred records. So we present this as **four descriptive
measurements with coverage unresolved**, not as a recommended minimum-data budget for a
practitioner. We would not oversell the crossover as a precisely located knee either,
because it is read from four single runs with no repeated seeds.

## The motif, restated

Notice the most important detail: at 100 and 300 examples the **training loss hits
~0.000** — the model has *memorized* its tiny training set — yet pass@1 is only ~0.10.
A loss of zero on a small set buys almost nothing on unseen examples.

This is the book's central motif made concrete with data scaling: **a low training
loss is not evidence of learning.** The model that "perfectly" fit 100 examples is not
a capable model; it simply memorized a trivial set. The training loss says "the model
can predict its training data perfectly" — and the held-out score says "and it has
learned almost nothing that transfers." These two facts sit side by side, and they are
both true. Only the held-out number tells us about actual capability.

## The brewing experience

There is a specific moment in this experiment worth recalling. Running on 100 examples
was fast — a blink. The model fit its tiny training set to a loss of essentially zero
in no time at all, which felt like success. Then we evaluated on held-out problems and
got 0.100. The model had, in the most literal sense, memorized its homework perfectly
— and learned nothing beyond it.

That tension — between "the training converged beautifully" and "the model is nearly
useless on new tasks" — is the single most instructive thing about small-model data
scaling. It is the reason we never trust a training loss, and it is the reason the
whole book is organized around held-out measurement rather than training curves. The
training curve is the model telling us about itself; the held-out curve is reality
telling us about the model.

## The honest caveat

This experiment measured *quantity*. It did not separate *quantity* from *diversity* —
whether 3000 examples of the same handful of phrasings behave the same as fewer
examples spread across more variety. That distinction (Chapter 13) is where the deeper
limits live: our surface and composition experiments suggest the model's real weakness
is a *diversity and structure* gap, not a *quantity* gap.

### A note on uncertainty

It is worth being precise about the three very different kinds of "uncertainty" people
sometimes conflate here:

- **Fixed test score.** A pass@1 like 0.641 is the exact measured score on *this* test
  set, under this decoding and evaluation procedure. It is a property of that dataset.
- **Uncertainty over a target distribution.** If we wanted to say "the model scores
  ~0.64 on new tasks of this type," we'd need a sense of how much 0.641 would vary
  across different test sets. We report **descriptive scores only**: we did not estimate
  uncertainty for a defined target prompt distribution, nor did we run multiple training
  seeds per size, so between-training-seed variability is unknown. (We could in principle
  analyze conditional sampling uncertainty by examining repeated fresh generations for the
  same prompts, and designed/grouped evaluation could support other intervals under stated
  assumptions — but we did not do that here, so we do not claim those either.)
- **Seed variation.** We ran each condition with a single seed. That does not mean every
  kind of interval is impossible — it means *seed variance* is unknown, and it does not
  quantify uncertainty over an arbitrary future prompt distribution. We treat the numbers
  as measured for the run we did, and as approximate for the underlying capability, rather
  than as a tight estimate.

A further caution against a naive confidence interval: the test set is not a set of
independent, uniformly-drawn examples. It comes from one generator, reuses a handful of
wording families and operation templates, and (in some splits) shares prompts across
conditions. So a standard binomial interval can be misleadingly tight, and a "3/n" upper
bound for a zero result assumes independent draws that this generator does not
provide. We therefore report raw counts and do not attach invented error bars.

## The practical answer

Four points, each read honestly.

First, these four points support a **trend under these budgets**, not a demonstrated
sharp threshold: 0.100 at 100 examples → 0.098 at 300 → 0.300 at 1000 → 0.641 at 3000.
We only ran each count once, so we cannot pin an exact inflection. Four points describe
"performance improves as example count grows in the range we tried," not "there is a
knee at 3000."

Second, the number is for a **multi-operation dataset**, not a per-operation
requirement. The run trains on all ten primitive operations mixed together (the pool is
built per-operation and then concatenated). So "the model reached 0.641" is the aggregate
over the whole 3000-record, multi-operation pool — it does **not** mean every individual
operation needed 3000 examples, nor that one operation on its own requires 3000. The
1,400-record pilot is likewise the whole task family, not 1,400 per primitive.

Third, the comparison is against a *common* held-out set within the run (one
`pool_test` reused at every size), which is the right thing for isolating the effect of
training count. It is a different set from the pilot's 300-case test, so these scores are
not directly comparable to the pilot's 0.897.

Fourth — and anticipating the rest of the book — even at 3000 examples the model is still
surface-fragile on the reworded test we ran. Composition is a separate question that this
chapter did not measure; we do not yet know whether more data of any kind would help it,
and we say so rather than assume the answer.

The practical takeaway is thus a two-part answer, scoped to what this chapter measured.
To get even the *narrow* score up, more examples help *in the range we tried*. But the
narrow score is not the hard-won prize. Whether robustness to rephrasing or compositional
generalization is purchased by data is a separate question: this chapter only measured the
familiar-task score, so it does **not** answer it. Chapter 13 asks whether more *diverse*
data buys surface robustness, and Chapter 16 asks about composition — each with its own
caveats about what it can and cannot show.
