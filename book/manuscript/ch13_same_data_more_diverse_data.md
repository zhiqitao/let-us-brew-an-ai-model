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

And this is the chapter where we tried to stop treating it as a hunch and measure it
directly. The design was clean on paper: hold the *count* fixed and vary only the
*spread*. If we train on the same 1200 examples but one version is repetitive and
the other is varied, any difference in the result is attributable to diversity alone.

**What a later code audit showed — read this before the numbers.** The comparison we
actually ran is **not** 1,200 versus 1,200. The high-diversity pool is built one
record per operation × wording family × identifier set, and the generator's domain is
small: the ten training operations have only **21 wording-family entries** in total,
so with two identifier sets `build_pool()` constructs **42 records** — and
`pool[:1200]` returns those 42, not 1,200. The minimal-diversity branch, by contrast,
explicitly creates 1,200 (largely repeated) records. The manifest recorded only the
*requested* `n_train=1200`, which hid the realized 42. So the arms differ in **both**
count (42 versus 1,200) and diversity — the equal-count premise of this chapter is
false, and with it the clean one-variable causal reading. The high-diversity arm's
1.000/1.000 is best read as **coverage of 42 exact training mappings**, not as a
quantity-versus-diversity result. We preserve the run as a flawed historical
construction (Appendix B, P0-02); a real answer needs a larger, varied-family
generator that can actually fill both arms to the same count.

## What our experiments hinted
![Diversity vs quantity — flawed historical run (42 vs 1,200 records)](figures/fig_diversity.png)

*Flawed historical run, relabeled as coverage: the arms were **not** the same count —
the high-diversity pool realized only **42 records** against the minimal-diversity
arm's 1,200 (P0-02; how the 42 arises is in the audit note above). The minimal-diversity
condition's surface test falls outside its narrow training surface → 0.000; the
high-diversity condition's surface test is within its training family set → 1.000
(coverage of 42 exact mappings, not transfer to an excluded family, and not an
equal-count comparison; see the caveat below).*

The data-scaling curve (Chapter 11) recorded that scores rise with the pool size —
0.10 at 100, 0.64 at 3000 — but that sweep is now known to be confounded with
operation coverage (P0-01), so it does not establish a quantity effect either.

But the *surface* experiment (Chapter 15) exposed the limit of a narrow training
surface: the model's
capability collapsed the moment we changed to a wording it hadn't seen. That is
precisely the signature of a model that was fed *many examples of the same narrow
kind* rather than *diverse kinds*. It learned the particular phrasings well because it
saw many of them, and it learned nothing general because the diversity was low.

In other words, the narrowness that produced the impressive in-distribution score
is what made it surface-fragile. The model was well-fed but narrow.

## The direct test: same count, different diversity — as designed, and as built

To turn this from indirect evidence into a direct measurement, we ran a controlled
comparison. The design kept the example count **identical** — the same 1200 examples — across
two training sets:

- **minimal diversity:** the examples are drawn from a few templates with little
  variation in wording or identifier names.
- **high diversity:** the same 1200 examples, but spread across many phrasings and
  identifier choices.

Because the count was meant to be identical, any difference in the result would be caused *only* by the
diversity — a clean one-variable experiment, and the strongest test of the
hypothesis.

As built, the second arm could not reach 1,200: the realized training sets were **42
(high diversity) versus 1,200 (minimal diversity)** — the generator's whole diverse
domain for these ten operations is 42 records (mechanism in the audit note above). The count is not identical — it
differs by a factor of ~28, in the *opposite* direction from the diversity advantage.
Any causal reading "diversity alone caused the swing" is therefore unsupported: the
arms differ in count and diversity at once, and the manifest recorded only the
requested count.

## The measured result

Here is what came out. Read it as a coverage demonstration from a flawed
construction, not as the equal-count causal result the design intended.

| Training set | realized records | in-distribution | surface |
|--------------|------------------|-----------------|---------|
| **minimal diversity** | 1,200 | 0.500 | **0.000** |
| **high diversity** | **42** | **1.000** | **1.000** |

Let us read this carefully. The two
models behaved completely differently — but the arms were not the same size.

- **Minimal diversity (1,200 records):** in-distribution 0.500, surface 0.000. The model did okay on
  the narrow task (0.500) but was completely brittle to any surface change (0.000). It
  learned the few phrasings it was given and nothing about the *idea*.
- **High diversity (42 records):** in-distribution **1.000**, surface **1.000**. What this
  establishes (see the coverage caveat below) is broad **coverage** of the surfaces that
  were in its training family set — all 42 model-visible mappings —; it does not by itself prove generalization to a
  wording family it never saw, and it is not a like-for-like comparison against the
  1,200-record arm. We say "covers more alternate surfaces," not "learned the
  operation as an abstract idea," and not "diversity beat quantity at equal count."

That is a swing from 0.500/0.000 to 1.000/1.000 — but with 42 records on one side and
1,200 on the other, we cannot attribute it to *how* the examples varied alone. The
same model family, two different training sets that differ in count **and** diversity:
this is a **flawed historical construction**, preserved honestly (Appendix B,
P0-02), not the clean one-variable experiment we set out to run.

### Multi-seed replication

One run can be a fluke, so we re-ran both conditions from scratch under training
seeds 1 and 2 (report: `docs/reviews/loop/multiseed_replication.md`):

| Training set | seed 0 | seed 1 | seed 2 |
|--------------|--------|--------|--------|
| minimal (in-dist / surface) | 0.500 / 0.000 | 0.500 / 0.033 | 0.500 / 0.000 |
| high (in-dist / surface) | 1.000 / 1.000 | 1.000 / 1.000 | 0.983 / 0.983 |

The pattern is stable across seeds — but every seed re-built the same 42-versus-1,200
pools, so the replication repeats the construction flaw rather than fixing it. What is
repeatable is the *coverage* pattern: the arm whose pool covers the surface test
scores ~1.0 on it, the narrow arm scores ~0. The coverage-vs-generalization caveat
below is unchanged — replication says the effect is repeatable, not that it proves
equal-count causation or transfer to a never-seen wording family.

## What this really means

This is the book's most visually dramatic finding, and it reframes the whole data
question — with an asterisk we now put first. It is not that "more data is better."
It is that **the kind of variation in the data changes what the model can do** — and
our own attempt to isolate that lever at equal count did not isolate it.

A model fed many examples of few phrasings memorizes the phrasings. A model fed a
small pool that spans many phrasings comes to cover far more of the
surface space. We cannot say from this experiment alone that it has "learned the
underlying operation" in the strong sense — that would require a wording family it
was *never* trained on, which this design does not test (see the caveat below) — and
we cannot say the swing was caused by diversity alone, because the arms' counts
differed (42 versus 1,200). What
the result shows is a large and real shift in coverage: the diverse-pool model gets 1.000
where the narrow-pool model gets 0.000. That is a strong *lead*, even before we claim it forces abstraction — and it is a lead that
a corrected, equal-count rerun has to confirm before it becomes a causal claim.

## An honest limit: coverage vs. generalization

Before we claim too much, we have to be precise about what that 1.000 surface score
actually measured. The surface test used word-identifiers and a *randomly-chosen*
wording family per operation. The high-diversity training set, however, contained
*all* the wording families and *both* identifier-sets — all 42 records of the
generator's diverse domain. So the surface test's wording
(and its identifiers) may well have been *present in the high-diversity training set*
— which makes the 1.000 at least partly a measure of **coverage** (the model had seen
that surface), not of generalization to a surface it had never encountered.

The minimal→0.000 result is unambiguous about the factor that changed: that model saw
only a narrow slice (one identifier-set, one wording family per operation), so the
surface test — which used different identifiers and a *randomly-chosen different*
wording family per operation — was genuinely unseen on the identifier axis. It scores
0.000. But note precisely what this isolates: a *surface* shift (different identifiers
and, per operation, a different family). It does not by itself establish that the
specific wording family was excluded from training for every operation (in the minimal
condition the family-set is narrow but still overlaps the test's family pool in
principle), so we read the zero as strong evidence that a surface shift breaks the
minimal model, not as proof that a particular family was provably absent. The
high→1.000 result, by contrast, is
strongest as a statement about **coverage**: diverse training covers more surfaces.
Whether it generalizes to a wording *family it never saw* is a separate question this
design does **not** answer — that would need a held-out family excluded from the
diverse pool. We flag this honestly, because the strong reading ("diversity produces
generalization to unseen surfaces") is not fully established by this experiment as run
— and the equal-count reading ("diversity alone caused the swing") is not established
at all, because the counts were 42 versus 1,200.

### This chapter vs. Chapter 15: two different "surface" tests

It is easy to blur these two, so let us keep them apart. Both test surface change, but
they answer different questions. As two labeled notes:

**CHAPTER 13: ALTERNATE-SURFACE COVERAGE (flawed construction)**
- **Training:** a narrow pool (1,200 records) or a broad pool (**42 realized records**;
  all families, both identifier-sets).
- **Evaluation:** the same alternate-surface test, with the pool's families; overlap
  differs by condition.
- **Finding:** the broader pool performs better on covered surfaces.
- **Not established:** equal-count causation (the arms were 42 vs 1,200), or transfer
  to a never-seen wording family by the broader model.

**CHAPTER 15: EXCLUDED-FAMILY EVALUATION (also flawed — see Chapter 15)**
- **Training:** specified families, with one family excluded per operation.
- **Evaluation:** that excluded family, on the scored data — **480 records** (8
  operations × 60; two operations have no held-out family), not 600.
- **Finding:** the reported samples yielded zero complete-test successes.
- **Scope:** the novelty audit and the denominator must match the scored run.

The Chapter 15 result is a held-out-family test, with an important provenance note: the
Appendix C novelty audit reports **zero exact prompt-string overlap** between the training
split and the held-out wording family, but that audit was run on **regenerated samples**
with the current generator, not on the originally scored files. Zero string overlap also
does not by itself prove the *family* was excluded — construction intent and a regenerated
diagnostic corroborate that the family was meant to be held out, but we did not
independently verify exclusion on the historical scored artifacts (the old-vs-new novelty
audits row of the evidence table, Chapter 11). The Chapter 13 result,
by contrast, is a coverage demonstration on a 42-record pool. Only Chapter 15 speaks to generalization to a
*never-seen* wording; Chapter 13 shows diversity widens the covered surface.

![Coverage is not a held-out family test](figures/fig_coverage.png)

The figure makes the distinction explicit: the high-diversity surface test lives
*inside* the training family set (so its 1.000 is coverage), whereas a true
held-out-family test would train on some families and test on one that is never shown.

## The honest caveat

It is worth noting that this experiment was *intended* to measure *surface* diversity at
fixed count, and did not deliver the fixed count (P0-02; the audit note above). What the run shows is that
varying phrasing and identifiers makes the model cover the alternate surfaces *within
the tested family set* (the Question-3 boundary) — a coverage result on unequal arms.
It does **not** show that diversity
fixes *compositional* generalization (the Question-4 boundary) — that is a separate,
harder question — and it does not show a diversity effect isolated from record count.
Whether the same lever helps a model combine two things it knows is the
most natural next experiment, and it is called out in the conclusion.

So the honest scope of the finding is precise: **surface diversity improved coverage of
the alternate surfaces within the tested family set — a coverage result on a
42-versus-1,200 construction, not an equal-count causal result and not transfer to
a wording family the model never saw.** Whether diversity reaches deeper, into
composition, remains open.

## The lesson

This reframes what "more data" buys — as a hypothesis, not yet a measurement. To make a capability cover more of the surface
space, we would expect to need not just more examples of a phrasing, but more *diverse* phrasings,
identifiers, and structures — enough that the model cannot tie the operation to any
particular surface form. Our experiments show the model's weakness, for *robustness and
generalization*, is not a lack of more records (Chapter 11's quantity sweep is
confounded and establishes little; Chapter 13's diversity sweep is also confounded),
but a suspected lack of data *diversity* (and, deeper, a suspected lack of the structural kind of
data needed for composition — see Chapter 16). Both levers need corrected controls
before either can carry a causal lesson.

The practical implication is worth stating as a lead, with its scope attached: in one run, on one
task, a practitioner who cannot
acquire more data may get a large improvement just by *diversifying* the data
they already have — re-phrasing the same examples, varying the identifiers, and
spreading across template families turned a brittle 0.500/0.000 model into one that
covers 1.000/1.000 of the tested surfaces in our run. Read that
1.000/1.000 narrowly, in the same breath as we report it: it is a coverage result
for surfaces *within the tested family set* on this one task — repeatable across
seeds 0, 1, and 2 (see the multi-seed note above) — on the 42-versus-1,200 pools, so
the scope limits stated in the honest caveat above apply in full. That is the kind
of result that changes how a dataset *might* actually be built — as a measured,
single-run lead worth re-testing under corrected controls, not universal practitioner advice.