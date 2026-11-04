# 13. Same Data, More Diverse Data

Chapter 11 asked *how much* data. There's a subtler question that often matters more:
what *kind* of data. Specifically, is it better to have lots of examples of a few
things, or the same number of examples spread across more variety?

The easy answer is to treat "more data" as one lever. It isn't. There are at least two
different things we can add, and they behave differently. It is like teaching a
kid shapes. Show them a hundred triangles and they'll recognize triangles. Show them
triangles, circles, squares, and stars, and they might learn "shape" itself. Same
number of examples, very different kind of learning.

- **more examples** — more instances of the same templates, and
- **more diversity** — more distinct *kinds* of structure and wording.

The distinction is important enough to state as a rule:

> **More data ≠ more information ≠ more diversity.**

And this is the chapter where we stopped treating it as a hunch and measured it
directly. The design: hold the *count* fixed and vary only the *spread*. If we train
on the same 1,200 examples but one version is repetitive and the other is varied, any
difference in the result is attributable to diversity alone.

The first attempt at that comparison failed its own premise (a code audit found the
arms were 42 versus 1,200 records — P0-02). We rebuilt it. The numbers below are the
**corrected, equal-count rerun**: both arms exactly 1,200 records, 10 of 10 operations
at 120 records per operation, one fixed tokenizer, and a matched training protocol.
The flawed first run is preserved as labeled history at the end of the chapter.

## What our experiments hinted

![Diversity at equal count — low vs high diversity, in-distribution and held-out family](figures/fig_diversity.pdf)

*Corrected equal-count run (three seeds; P0-02 fixed): both arms hold **1,200
records**, 10/10 operations at 120 per operation, under one fixed tokenizer and a
matched 1,000-step protocol. The low-diversity arm (2 phrasing families per
operation, letter identifiers — 20 unique prompt/program pairs) scores **0.950**
in-distribution but **0.000** on a genuinely held-out phrasing family; the
high-diversity arm (all training families × 5 identifier sets — 605 unique pairs)
gives up some in-distribution sharpness (**0.743** mean) and reaches **0.550** mean
on the held-out family. Bars are three-seed means; the whiskers span the per-seed
range.*

The data-scaling curve (Chapter 11) recorded that scores rise with the pool size —
0.10 at 100, 0.64 at 3000 — but that sweep is now known to be confounded with
operation coverage (P0-01), so it does not establish a quantity effect either. The
corrected version of *that* lever (Chapter 11) came back flat.

The *surface* experiment (Chapter 15) exposed the limit of a narrow training
surface: the model's capability collapsed the moment we changed to a wording it
hadn't seen. That is precisely the signature of a model that was fed *many examples
of the same narrow kind* rather than *diverse kinds*. It learned the particular
phrasings well because it saw many of them, and it learned nothing general because
the diversity was low.

In other words, the narrowness that produced the impressive in-distribution score
is what made it surface-fragile. The model was well-fed but narrow.

## The direct test: same count, different diversity

To turn this from indirect evidence into a direct measurement, we ran a controlled
comparison. The design keeps the example count **identical** — 1,200 examples in
each arm — across two training sets:

- **low diversity:** 2 phrasing families per operation, letter identifiers only.
  That is the entire spread: **20 unique (prompt, program) pairs**, repeated to fill
  1,200 records.
- **high diversity:** all of the generator's training phrasing families per
  operation crossed with **5 identifier sets** (letters, words, Greek letters,
  colors, animals) — **605 unique (prompt, program) pairs** across 121
  (operation, family) pairs, repeated to fill 1,200 records.

Everything else is matched. Both arms cover **10 of 10 operations at exactly 120
records per operation**; both use **one fixed tokenizer** (vocabulary 293, fit once
on the union of the two arms' training texts and never refit per arm or seed — the
SHA-256 is pinned in every manifest, Appendix C); and both train for **1,000 steps**
on the 884,224-parameter model with batch 16, learning rate 1e-3, and the *same*
initialization within each run seed — identical initial weights, so only the data
differs. The low arm's (family, identifier) space is a strict subset of the high
arm's, so the two arms differ in spread, not in operations or count.

Because count, operation coverage, tokenizer, and protocol are all held fixed, any
difference in the result is caused by the diversity — a clean one-variable
experiment, and the strongest test of the hypothesis.

## Two tests, shared by both arms

Each trained model is scored on the same two fixed task sets, identical across arms
and seeds, 100 tasks each (10 per operation, 10 of 10 operations):

- **in-distribution:** the low arm's families with letter identifiers — familiar to
  *both* arms by construction (the low space is a subset of the high space), held
  out only at the instance level (new construction seeds, new hidden tests).
- **held-out family:** two phrasing families per operation (`h01`, `h02`) that
  **no training arm ever sees**, with letter identifiers, so the *wording* is the
  only thing that changed. The run's audit checks family identity, not just string
  disjointness: **zero** (operation, family) collisions, zero prompt collisions, and
  zero prompt/program-pair collisions between the held-out families and *both* arms'
  training sets.

The baselines are scored on the identical records. TEMPLATE (a hand-written rule
system) and RETRIEVAL (a TF-IDF retriever over the arm's own training pool) both
score the same task sets, so every number below shares one denominator.

## The measured result

Here is what came out, model pass@1 per seed (seeds 0, 1, 2) with the three-seed
mean:

| Training set | in-distribution (100 tasks) | held-out family (100 tasks) |
|--------------|-----------------------------|-----------------------------|
| **LOW diversity** — 1,200 records, 20 unique pairs | 0.950 / 0.950 / 0.950 (mean **0.950**) | 0.000 / 0.000 / 0.000 (mean **0.000**) |
| **HIGH diversity** — 1,200 records, 605 unique pairs | 0.820 / 0.570 / 0.840 (mean **0.743**) | 0.640 / 0.300 / 0.710 (mean **0.550**) |

Baselines on the same task sets (identical across seeds):

| System | in-distribution | held-out family |
|--------|-----------------|-----------------|
| TEMPLATE | 0.800 | 0.700 |
| RETRIEVAL (low arm's pool) | 1.000 | 0.600 |
| RETRIEVAL (high arm's pool) | 1.000 | 1.000 |

Let us read this carefully.

- **Low diversity:** in-distribution 0.950, held-out family **0.000** — 0 of 100, in
  every seed, on all ten operations. The model did the narrow task *better* than the
  diverse model did, and was completely brittle to a wording family it had never
  seen. It learned the few phrasings it was given and nothing about the *idea*.
- **High diversity:** in-distribution 0.743 mean, held-out family **0.550** mean
  (0.640 / 0.300 / 0.710). The same 1,200 records, the same operations, the same
  tokenizer and protocol — and the model now solves more than half of a phrasing
  family that appears nowhere in its training data. It sits below TEMPLATE (0.700)
  and RETRIEVAL (1.000) on that test, so this is partial generalization, not mastery.

That is the trade, measured at equal count: **diversity buys generalization to an
unseen phrasing family (0.000 → 0.550 mean) and costs some in-distribution
sharpness (0.950 → 0.743 mean).** The low arm's 0.950 is the sharpest
in-distribution score in this comparison, and it is worth exactly nothing on a
wording the model never saw.

The retrieval row deserves one note: RETRIEVAL is built over each arm's *own*
training pool, so on the held-out family it scores 0.600 from the low arm's 20-pair
pool and 1.000 from the high arm's 605-pair pool — the diverse pool covers the
operations under more surface forms, which is what a retriever exploits. The model
at 0.550 is below both its own arm's retrieval score, so diversity did not make the
model the best system in the room; it made the model *transfer*, which the narrow
model did not do at all.

### The corrected run is natively three-seed

One run can be a fluke, so the corrected experiment was built as a three-seed run
from the start (manifests: `artifacts/manifests/diversity_corrected_seed{0,1,2}.json`)
rather than re-run afterward. The pattern holds across all three seeds: the low arm
is 0.950 / 0.000 (in-distribution / held-out family) in *every* seed, and the high
arm is positive on the held-out family in every seed (0.640, 0.300, 0.710) while
scoring lower than the low arm in-distribution in every seed (0.820, 0.570, 0.840
against 0.950). The seed-1 dip (0.570 / 0.300) moves both of the high arm's numbers
down together; it does not change the sign of either finding. Final training losses
tell the same story from the training side: the low arm fits its 20 pairs almost
perfectly (0.0174 / 0.0215 / 0.0167) while the high arm's loss stays higher
(0.0432 / 0.0457 / 0.0445) — 605 distinct pairs are simply more to learn at the same
step budget.

## What this really means

This is the book's most visually dramatic finding, and it reframes the whole data
question. It is not that "more data is better." It is that **the kind of variation
in the data changes what the model can do** — and now that count and operation
coverage are truly matched, the effect is attributable to that variation alone.

A model fed 1,200 examples of 20 phrasings memorizes the phrasings: 0.950 where it
was trained, 0.000 the moment the wording changes family. A model fed the same
1,200 examples spread across 605 phrasings and five identifier sets gives up some
sharpness on the familiar surface and keeps more than half of its capability on a
wording family it was never shown. The narrow model's impressive in-distribution
score and its total brittleness are the same fact seen from two sides: it learned
the surface, not the operation.

The corrected result also settles what the earlier, flawed run could not say. The
first version of this experiment reported 0.000 versus **1.000** — but its
high-diversity pool realized only **42 records** against the low arm's 1,200, and
its "surface" test drew from families that pool already contained, so the 1.000 was
**coverage of 42 exact mappings**, not transfer. That run is preserved below as
flawed history (P0-02). The corrected run replaces both of its numbers: the honest
held-out-family comparison is **0.000 versus 0.550 mean**, not 0.000 versus 1.000,
and the honest in-distribution comparison is **0.950 versus 0.743**, not 0.500
versus 1.000.

## Coverage vs. generalization: the distinction, now tested both ways

The distinction between *covering* a surface and *generalizing* to one is what made
the first run misleading, so it is worth keeping explicit. A test whose wording
lives inside the training family set measures **coverage**: the model saw that
surface. A test on a family excluded from training measures **generalization**: the
model did not.

![Coverage is not a held-out family test](figures/fig_coverage.pdf)

The figure makes the distinction explicit: a surface test drawn from the training
family set measures coverage, whereas a true held-out-family test trains on some
families and tests on one that is never shown. The corrected run *is* the second
kind — the `h01`/`h02` families are excluded from both arms and audited for zero
family, prompt, and pair collisions — so its 0.550 is a generalization number, and
the flawed run's 1.000 was a coverage number. Both kinds of test now exist in this
book, and they are labeled differently everywhere they appear.

### This chapter vs. Chapter 15: two different "surface" tests

It is easy to blur these two, so let us keep them apart. Both test surface change,
but they answer different questions. As two labeled notes:

**CHAPTER 13: EQUAL-COUNT DIVERSITY, HELD-OUT FAMILY (corrected; P0-02 fixed)**
- **Training:** two arms of exactly 1,200 records each, 10/10 operations at 120/op,
  one fixed tokenizer, matched 1,000-step protocol — LOW = 2 families/op × letters
  (20 unique pairs), HIGH = all training families × 5 identifier sets (605 unique
  pairs).
- **Evaluation:** an in-distribution test familiar to both arms, and a held-out-family
  test (`h01`/`h02`, 100 tasks each) audited disjoint from *both* arms.
- **Finding:** LOW 0.950 / 0.000, HIGH 0.743 / 0.550 (three-seed means) — diversity
  drives transfer to a never-seen family, at a small in-distribution cost.
- **Scope:** one task family, one model size, three seeds; phrasing/identifier
  diversity only — not structural (composition) diversity.

**CHAPTER 15: EXCLUDED-FAMILY EVALUATION (also flawed — see Chapter 15)**
- **Training:** specified families, with one family excluded per operation.
- **Evaluation:** that excluded family, on the scored data — **480 records** (8
  operations × 60; two operations have no held-out family), not 600.
- **Finding:** the reported samples yielded zero complete-test successes.
- **Scope:** the novelty audit and the denominator must match the scored run.

The Chapter 15 result is a held-out-family test with an important provenance note:
the Appendix C novelty audit reports **zero exact prompt-string overlap** between the
training split and the held-out wording family, but that audit was run on
**regenerated samples** with the current generator, not on the originally scored
files, and zero string overlap does not by itself prove family exclusion. The
Chapter 13 corrected result is stronger on that specific point: its exclusion is
checked by (operation, family) identity with collision counts recorded in the
manifest — zero against both arms — so the family exclusion is a property of the
scored run itself, not of a regeneration. The two chapters agree in direction
(wording-family novelty breaks the narrow model); Chapter 13 adds the controlled
comparison that says *diversity* is what moves the number.

## The honest caveat

The corrected experiment delivers the fixed count and the audited holdout, so the
equal-count causal reading is now supported: with count, operation coverage,
tokenizer, and protocol matched, phrasing diversity is what separates 0.000 from
0.550 on the held-out family. Three limits still bound the claim.

First, this is **surface** diversity — phrasings and identifier names. It does
**not** show that diversity fixes *compositional* generalization (the Question-4
boundary); composition stayed 0.000 throughout the book regardless of data. Second,
the high arm's 0.550 is partial: it is below TEMPLATE (0.700) and its own arm's
RETRIEVAL (1.000) on the same records, and it ranges 0.300–0.710 across seeds, so
"diverse data produces unseen-family transfer" is a measured tendency, not a solved
problem. Third, the scope is one task family, one model size (0.88M), and three
seeds on one fixed tokenizer — the usual "here, in this regime" applies.

So the honest scope of the finding is precise: **at equal count and balanced
operation coverage, phrasing diversity improved generalization to a genuinely
held-out wording family from 0.000 to 0.550 mean, at the cost of in-distribution
sharpness (0.950 to 0.743 mean).** Whether diversity reaches deeper, into
composition, remains open.

## Flawed history: the first run (P0-02), superseded

We keep the original run on the record, clearly labeled, because how it failed is
more instructive than the number it produced. The original generator's diverse
domain for these ten operations was small: the training operations had only
**21 wording-family entries** in total, so one record per family × 2 identifier sets
gave **42 records**, and `pool[:1200]` returned those 42 — while the minimal branch
explicitly created 1,200 (largely repeated) records. The manifest recorded only the
*requested* `n_train=1200`, which hid the realized 42. The arms therefore differed
in **both** count (42 versus 1,200) and diversity, and the "surface" test drew
families from the high arm's own pool.

| Training set | realized records | in-distribution | surface (covered families) |
|--------------|------------------|-----------------|----------------------------|
| minimal diversity | 1,200 | 0.500 | 0.000 |
| high diversity | **42** | 1.000 | 1.000 |

Read that 1.000 as **coverage of 42 exact training mappings**, not as
equal-count causation and not as transfer to an excluded family. The flawed run
repeated across its own seeds (minimal 0.500 / ~0.000, high ~1.000 / ~1.000 in
seeds 0, 1, 2 — Appendix C, Table C.8), which only shows the construction flaw is
deterministic. Both the run and its seed table are marked **superseded flawed
historical** in Appendix C; the corrected run above replaces them, and the
corrected numbers — not these — are the ones the rest of the book cites.

## The lesson

This reframes what "more data" buys, and it now does so with a measurement rather
than a hunch. To make a capability cover more of the surface space, more examples of
one phrasing do not help: the corrected size sweep (Chapter 11) is flat, and the
narrow arm of this chapter scores 0.000 on an unseen family with 1,200 records in
hand. What helps is more *diverse* phrasings, identifiers, and structures — enough
that the model cannot tie the operation to any particular surface form. Our
experiments show the model's weakness for *robustness and generalization* is not a
lack of records (Chapter 11's quantity sweep, corrected, establishes a null) but a
lack of data *diversity* (this chapter, corrected: 0.000 → 0.550 on a held-out
family) — and, deeper, a suspected lack of the structural kind of data needed for
composition (see Chapter 16), which remains open.

The practical implication is worth stating with its scope attached: in this run, on
one task, a practitioner who cannot acquire more data may get a large improvement
just by *diversifying* the data they already have — re-phrasing the same examples,
varying the identifiers, and spreading across template families turned a model that
scores 0.000 on any unseen wording into one that solves 0.550 of a never-seen
family, across all three seeds. Read that in the same breath as its price: the same
diversification cost in-distribution sharpness (0.950 → 0.743 mean), the diverse
model still sits below both baselines on the held-out test, and composition was not
touched at all. That is the kind of result that changes how a dataset *might*
actually be built — a measured, three-seed, equal-count finding on one task, not
universal practitioner advice.