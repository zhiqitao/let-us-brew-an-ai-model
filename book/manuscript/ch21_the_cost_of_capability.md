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

**Table 19.1 — Resource budget, by run**. The data column is the **training-record count
and distinct prompt–program pairs** (where known); it is not the evaluation-set size.
Where a record/pair count is not separately recorded, we say so rather than borrow an
evaluation denominator.

| Run | data records / unique pairs | parameters | steps |
|------------------|-----------------------------|------------|-------|
| `stage1` | 1,400 / 21 | 0.88M | 1,500 |
| `stage3_surface` | 600 (10 op × 60) | 0.88M | 1,500 |
| `data_scaling` (per size) | 100, 300, 1000, 3000 | 0.88M | 800 |
| `stage4_exposure` | not recorded | 0.88M | 1,500 |
| `compdiv_minimal` / `compdiv_high` | not recorded | 0.88M | 1,500 |
| size sweep | not recorded | 0.88M / 6.5M / 10.2M / 29.3M | 1,500 / 1,000 / 800 / 800 |
| `continual_seq` | 1,400 + 1,400 | 0.88M | 1,400 |
| `continual_joint` | 2,800 interleaved | 0.88M | 1,400 |

**Table 19.2 — Measured outcomes, by run** (the neural **MODEL**'s score; baselines are in
Chapters 15 and 16, not here). Run keys match Table 19.1. `0.350`/`0.000` are the model's
scores on the new-identifier and reworded splits; `0.875`/`0.683` belong to the
TEMPLATE/RETRIEVAL baselines and are not the model's.

| Run | in-dist | new IDs | new wording | composes |
|------------------|---------|---------|-------------|----------|
| `stage1` | 0.897 | — | — | 0.000* |
| `stage3_surface` | 0.900 | 0.350 | 0.000 | — |
| `data_scaling` | 0.100 / 0.098 / 0.300 / 0.641 | — | — | — |
| `stage4_exposure` | 1.000 | — | — | 0.667 / 0.000 |
| `compdiv_minimal` | 1.000 | — | — | 0.592 / 0.000 |
| `compdiv_high` | 1.000 | — | — | 0.550 / 0.000 |
| size 0.88M | 0.900 | — | — | 0.000 |
| size 6.5M | 0.897 | — | — | 0.000 |
| size 10.2M | 0.773 | — | — | 0.000 |
| size 29.3M | 0.897 | — | — | 0.000 |
| `continual_seq` | A 1.000→0.000; B 0.889 | — | — | — |
| `continual_joint` | A 1.000; B 0.889 | — | — | — |

*`stage1`'s composes value (0.000) is from the stage-4 re-evaluation of that pilot
checkpoint. The `stage4_exposure` and `compdiv_*` composes values are reported as
*exposed* / *held-out* (e.g. 0.667 exposed, 0.000 held-out, over n=120 exposed records
each); the held-out composite — the transfer test — was 0.000 in every composition run,
and those held-out candidates failed parsing (Appendix B.10). The continual rows test
task *retention*, not composition, so their "composes" cell is `—`. Note that the
`compdiv_*` rows (both in-dist 1.000, composes 0.592/0.550) are the **composition-
diversity** intervention runs from Chapter 16/Appendix C (`composition_diversity_pilot`,
1,500 steps) — a different experiment from Chapter 13's quantity-vs-diversity run
(`diversity`, 900 steps), whose minimal-diversity in-distribution score was 0.500. They
are not the same run, so the different in-distribution numbers are not a conflict.*

*Legend: `—` = that specific breakdown was not separately reported for that run (or the run
did not test it). We reserve an explicit `0.000` for outcomes we measured and that came out
negative, and use `—` when the run did not report that figure.*

A few cautions before reading this as a budget. First, the Stage-1 pilot's "1,400 records"
is the **ten-operation familiar-prompt family** total, which contained only **21 distinct
prompt–program pairs**; it is not a measured per-operation data requirement. Second, the
size sweep changed training budgets (1,500 / 1,000 / 800 / 800 steps) and tokenizer, so it
is not a size-only intervention. Third, the exposed-composite scores varied (0.550, 0.592,
0.667); the held-out composite — the transfer test — was **0.000** in every run, and those
held-out candidates all failed parsing, so the cause of that zero is unresolved (Chapter 16
and Appendix B.10). We do not know how much data would be needed to achieve composition;
we only know it was not achieved within the budgets we tried.

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

- **The ten-operation familiar-prompt family "costs" about 1,400 records and a few
  minutes.** That is the cheap row. Its in-distribution score was 0.897; the pilot itself
  did not run a reworded surface test (the Stage-3 surface run did, and scored 0.000 there).
  So we have bought a capability that works on the prompts it was trained with.
- **New-identifier and reworded robustness** (the Stage-3 surface run) costs the same
  1,400-class budget and still fails — the model drops to 0.350 on new identifiers and to
  0.000 on a reworded instruction. We cannot buy this with more of the same from this run.
- **Composition** is the row that tells the sharpest story. It was 0.000 on held-out
  composites at every parameter size we tried (0.88M, 6.5M, 10.2M, 29.3M), and the
  parameter column alone did not change that in the runs we ran. But the failure cause is
  unresolved (the held-out candidates failed parsing), so this is a recorded negative
  result, not a demonstrated mechanism. The exposed composites (0.550–0.667) also fell
  short of mastery on the *training-covered* combinations, so the model did not even fully
  learn those it was shown.
- **Continual learning** is the most interesting row for a practitioner. Sequential
  training loses A (final A accuracy 0.000, measured 1.000 right after phase A); fitting on
  A and B jointly keeps A at 1.000 with B acquisition unchanged at 0.889. This says a
  *jointly trained* model retains both tasks, not that replay recovered a lost capability in
  a deployed model. The same nominal total step budget was used for both, but resource use
  was not benchmarked, and the true replay-after-A-first design was not run (see Chapter
  18). Cost is not always toward "more expense"; the right procedure can make a capability
  cheaper to *retain*.

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
in-distribution *look* capable while it collapses to 0.000 on a reworded instruction
(and drops to 0.350 on a new identifier) — a change to the surface. In a deployed
system, that is precisely the failure that appears late and costs the most.

So the real answer to "what does each capability cost?" is: the easy-to-see cost
(data, parameters, steps) is small and scales predictably; the hard-to-see cost —
making the capability actually generalize and compose — is where the true expense
lies, and at this scale it was **not achieved** within the budgets we tried (we do not
claim it is unpurchasable in principle; we only report that our tested budgets did not
reach it).

And there is a bright spot in the matrix worth holding onto. The continual-learning row
shows that cost is not always "more of everything." Under the same nominal step budget, the
*jointly trained* model retained both tasks whereas the sequentially trained one lost A. We
did not benchmark resource use, and the true replay-after-A-first design was not run, so the
takeaway is about *schedule*, not about recovering a lost capability for free in a deployed
model. Cost, like capability, is often about *how* we do things, as well as *how much* we
spend.
