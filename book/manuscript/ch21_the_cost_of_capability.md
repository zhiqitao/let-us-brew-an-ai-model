# 21. The Cost of Capability

We've measured what the model can do and where it breaks. This chapter answers the
last practical question: *what does each capability actually cost?*

The obvious "costs" — data, parameters, training time — are the easy ones. But the
real cost in machine learning is the hidden one: what it takes to make a capability
actually *robust* rather than just *appearing* to work. That's where the expensive and
surprising part lives.

## The two kinds of cost

There is a trap in how we usually talk about cost. We say "this model is 0.9M
parameters" or "this took 3,000 examples" or "it trained in an hour." Those are real
numbers, and they are *easy* to measure. But they measure the cost of *running* a
model, or of *fitting* it — not the cost of *capability* in the sense we care about.

What we actually care about is much harder to see, and this chapter is an argument
that it is the only cost that matters:

> **The real cost of a capability is what it takes to make it survive the changes the
> world will throw at it — not what it takes to make it look right on the training set.**

That distinction is the key to reading the results in this chapter. The model can be
*cheap* to produce and still *expensive* to make useful, because the cheap version
works only under conditions the real world will not respect.

## The cost matrix

Each row is a **run** from our experiments, identified by its checkpoint and evaluation so
the provenance is explicit. Because a six-column table is too wide for a 6×9 page, the
matrix is split into two linked tables: the first is the **resource budget** (the input),
the second the **measured outcome** (the evaluation). Where an outcome was **not**
measured for that row we mark it `NT` (not tested) rather than a cross or a dash, because
"not run" and "failed" are different.

**Table 19.1 — Resource budget, by run**

| Run (checkpoint, evaluation) | data (records / unique prompt-program pairs) | parameters | steps |
|------------------------------|----------------------------------------------|------------|-------|
| Pilot, ten-op familiar-prompt family (stage1, pilot eval) | 1,400 / 21 | 0.88M | 1,500 |
| Pilot, stage-4 re-eval | 1,400 / 21 | 0.88M | 1,500 |
| New-identifier robustness | 1,400 / 21 | 0.88M | 1,500 |
| Surface, exposed (stage3_surface) | 600 | 0.88M | — |
| Data-scaling, smallest (pool_test) | 540 | 0.88M | — |
| Data-scaling, largest (pool_test) | 540 | 0.88M | — |
| Composition exposure (0.88M) | — | 0.88M | 1,500 |
| Composition exposure (0.88M, diversity) | — | 0.88M | 1,500 |
| Composition, size sweep | — | 0.9–29.3M | 1,000 / 800 |
| Continual: A then B (sequential) | 1,400 + 1,400 | 0.88M | 1,400 |
| Continual: A+B (joint) | 2,800 interleaved | 0.88M | 1,400 |

**Table 19.2 — Measured outcomes, by run**

| Run (checkpoint, evaluation) | in-dist | surface | composes |
|------------------------------|---------|---------|----------|
| Pilot, ten-op familiar-prompt family (stage1, pilot eval) | 0.897 | 0.000 (new wording) | NT |
| Pilot, stage-4 re-eval | 0.900 | NT | NT |
| New-identifier robustness | 0.900 | 0.350 (new IDs) | NT |
| Surface, exposed (stage3_surface) | 0.875 | 0.683 | NT |
| Data-scaling, smallest (pool_test) | 0.100 | — | NT |
| Data-scaling, largest (pool_test) | 0.641 | — | NT |
| Composition exposure (0.88M) | 0.900 (in-dist) | — | 0.667 exposed; 0.000 held-out |
| Composition exposure (0.88M, diversity) | 1.000 (in-dist) | — | 0.550 / 0.592 exposed; 0.000 held-out |
| Composition, size sweep | — | — | 0.897 / 0.000 (6.5M); 0.000 (10.2M, 29.3M) |
| Continual: A then B (sequential) | B 0.889 | NT | NT |
| Continual: A+B (joint) | A 1.000; B 0.889 | NT | NT |

*Legend: `NT` = not tested for that run; `—` = that breakdown was not separately
reported; a bare number is a measured score. We reserve a cross for an outcome we
actually measured and that came out negative, and use `NT` when the run did not test that
question at all. The continual rows test task *retention*, not composition — so their
"composes?" column is `NT`, and their "surface" column is likewise `NT` because only
in-distribution accuracy was measured for those runs.*

A few cautions before reading this as a budget. First, the pilot's "1,400 examples" is
the **ten-operation familiar-prompt family** total, which contained only **21 distinct
prompt–program pairs**; it is not a measured per-operation data requirement. Second, the
size sweep changed training budgets and tokenizer, so it is not a size-only intervention.
Third, the exposed-composite scores varied (0.550, 0.592, 0.667); the held-out composite —
the transfer test — was **0.000** in every run. We do not know how much data would be
needed to achieve composition; we only know it was not achieved within the budgets we
tried.

## What the costs tell us

**Capability is cheap; robustness is not.** Learning the ten-op familiar family cost
~1,400 records and a few minutes on a 0.88M model, and it "works" in-distribution (0.897).
So the *apparent* cost of a capability is low. But that number is misleading: it measures
only in-distribution correctness on prompts the model has seen.

**The real cost appears when we ask for generalization.** To make a single primitive
robust to *surface* change (new identifiers, new wording), the experiments suggest the data
would need to change substantially — diverse identifiers and wording — not just add
capacity. And composition was not achieved at any size we tried: it stayed 0.000 on
held-out at 0.88M, 6.5M, 10.2M, and 29.3M — though, as Chapter 16 notes, the held-out
composites all failed parsing, so the cause of that zero is unresolved.

**The cost matrix makes a dangerous pricing error visible.** If we only look at the
"in-dist" column, we would conclude capability is nearly free and scale up naively. The
generalization and composition columns reveal that the cheap number hides a much more
expensive requirement — robust, compositional capability — which we did not achieve by
scaling data or capacity within our tested range.

## The price of each column, read honestly

Let us read the matrix the way a person who has to pay for capability would read it,
not the way a researcher who wants a good headline would read it.

- **A ten-operation familiar-prompt family "costs" about 1,400 records and a few
  minutes.** That is the cheap row. But its surface-generalization test (new wording) was
  0.000, and composition was not tested for the pilot. So we have bought a capability that
  works on the prompts it was trained with.
- **New-identifier robustness** costs the *same* 1,400 records, and still fails (0.350 on
  new identifiers). We cannot buy this with more of the same from this run.
- **Composition** is the row that tells the sharpest story. It was marked 0.000 on
  held-out composites at every parameter size we tried (0.88M, 6.5M, 10.2M, 29.3M), and the
  parameter column alone did not change that in the runs we ran. But the failure cause is
  unresolved (the held-out candidates failed parsing), so this is a recorded negative
  result, not a demonstrated mechanism.
- **Continual learning** is the most interesting row for a practitioner. Sequential
  training loses A (final A accuracy 0.000); fitting on A and B jointly keeps A at 1.000
  with B acquisition unchanged at 0.889. This says a *jointly trained* model retains both
  tasks, not that replay recovered a lost capability in a deployed model. The same nominal
  total step budget was used for both, but resource use was not benchmarked, and the true
  replay-after-A-first design was not run (see Chapter 18). Cost is not always toward
  "more expense"; the right procedure can make a capability cheaper to *retain*.

## The brewing experience: discovering the hidden cost

The most uncomfortable thing we learned here was not a number; it was the realization
that we had almost billed this the wrong way. Early in the project, the model looked
cheap: tiny, fast to train, scoring 0.900. If we had been delivering a system rather
than running an experiment, we would have handed over a "working" model and called it
a good deal.

Then we reworded a single prompt. The model collapsed to 0.000. The capability we
thought we had bought was not really there — it only existed inside a narrow surface
form. That is the moment the "cheap capability" turned out to be the most expensive
thing we had measured, because it would fail in exactly the way a deployed system
fails: quietly, late, and in the hands of a real user who does not phrase things the
way the training data did.

That is why we now insist on reading the generalization columns, not just the accuracy
column. A model that is cheap to fit but expensive to deploy is the wrong thing to
build unless we know the generalization cost going in.

## The honest framing

The most honest "cost" we measured is the cost of **mistaking surface association for
grounded capability**. That cost is high: it makes a model that scores 90%
in-distribution *look* capable while it collapses to 0.000 on any change to the
surface. In a deployed system, that is precisely the failure that appears late and
costs the most.

So the real answer to "what does each capability cost?" is: the easy-to-see cost
(data, parameters, steps) is small and scales predictably; the hard-to-see cost —
making the capability actually generalize and compose — is where the true expense
lies, and at this scale it is simply not purchasable with more of the same resource.

And there is a bright spot in the matrix worth holding onto. The continual-learning row
shows that cost is not always "more of everything." Under the same nominal step budget, the
*jointly trained* model retained both tasks whereas the sequentially trained one lost A. We
did not benchmark resource use, and the true replay-after-A-first design was not run, so the
takeaway is about *schedule*, not about recovering a lost capability for free in a deployed
model. Cost, like capability, is often about *how* we do things, as well as *how much* we
spend.
