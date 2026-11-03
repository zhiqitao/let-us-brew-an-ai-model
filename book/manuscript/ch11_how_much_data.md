# 11. How Much Data?

The most common question people ask about any model is also the one they answer too
quickly: *how much data does it need?* We set out to measure it directly — holding the
model and the training method fixed, and varying the number of examples.

It is like studying for a test. Read one page and we fail. Read a bit more
and we still fail. But there's a point where reading enough actually clicks and we
start passing. Where's that point for a model? That is what this experiment was built
to find out.

It is a question worth measuring rather than guessing, because the folklore answer —
"just add more data" — is both plausible and unexamined. *How* data
helps, and *where* the help stops being worth it, is where the real information is —
and, as the audit note below shows, our own first attempt did not isolate it.

## How to read the evidence

This chapter opens the experimental part of the book, so we consolidate here the
small set of caveats that the chapters that follow would otherwise re-justify in
near-identical words. Each later result still carries its own local caveat,
immediately next to the number it bounds; what lives only in this table is the
shared *justification*. Where a chapter repeats one of these points, it now
points back to this table instead of re-arguing it.

**Table 11.1 — How to read the evidence**

| Caveat | What it means | Where it bites |
|---|---|---|
| **Coverage is not transfer.** | A score on prompts, surfaces, or operations the training pool already covers measures *coverage*, not generalization to something never seen. The pilot's 0.897 is single-sample correctness on reused training prompt strings; Chapter 13's 1.000 is coverage of its own training families. | Ch. 10, 11, 13, 14, 20 |
| **The 0.88M baseline denominator.** | Three "familiar-prompt" numbers — 0.897 (pilot, 300-record test), 0.900 (Stage-3 surface, 600 records), 0.9167 (Stage-4 baseline, n=60) — are three different evaluation sets, not a discrepancy. The figure they agree on is composition 0.000. | Ch. 12, 16, 19, 20 |
| **Model-size budget differences.** | The size sweep varied training budget and tokenizer alongside size (1,500 / 1,000 / 800 / 800 steps; pilot vs. composition tokenizer), so it is not a size-only intervention. | Ch. 12, 19, 20 |
| **Old vs. new novelty audits.** | The pilot was audited on the original scored files; the Stage-3 and Stage-4 holdouts were audited on *regenerated* reproductions with the current generator — corroborating, but not proof on the scored artifacts. | Ch. 13, 15, App. C |
| **Flawed historical constructions.** | Ch. 11's data-scaling sweep (P0-01: operation coverage), Ch. 13's diversity comparison (P0-02: 42 vs. 1,200 records), and Ch. 15's surface rows (P0-03: mixed factors; P0-04: 480-record denominator) are preserved as records of flawed runs. We draw no causal claim from any of them. | Ch. 11, 13, 15, 19, 20 |

**What a later code audit showed — read this before the numbers.** The sweep does not
change only the data count. The script builds one pool with
`pool = generate_dataset(n_per_op=400, ...)` and trains on `train = pool[:size]` — a
*prefix* of a pool the generator appends record by record **in operation order**. The
100- and 300-record arms therefore train on **one operation out of ten** (`add`), the
1,000-record arm on **three**, and the 3,000-record arm on **eight** — while the
evaluation set spans all ten operations. The sweep is thus **confounded with operation
coverage**: what changes across the four arms is not just how many records the model
saw, but *which operations it saw at all*. The recorded curve is preserved below as a
**flawed historical run of operation coverage**, not a data-count scaling result. We
draw no threshold, no knee, and no data-efficiency lesson from it, and the earlier
claim that "only the data count changes" was wrong. A balanced, operation-stratified
rerun — the same number of records per operation at every size, one fixed tokenizer,
matched step budgets — is what this question needs before any causal answer is
possible; that rerun has not been done. The numbers below are what the original,
confounded sweep recorded.

## The setup

We train the same ~0.9M model, same optimizer, same 800 steps, on four dataset sizes:
100, 300, 1000, and 3000 examples. Then we measure in-distribution pass@1 on a
held-out pool.

The *intent* was the one-variable discipline: hold the model and optimizer fixed,
change only the data count, and attribute any movement in the score to the amount of
data. The construction did not deliver that intent — as the audit note above states,
the arms also differ in which operations they cover (and the tokenizer was refitted
per size, a further changing variable). We report the run as it was actually built,
with the confound stated, rather than as the clean one-variable claim we meant to run.

## The result (a flawed historical run)

| dataset size | operations trained (of 10) | final train loss | **pass@1 (held-out)** |
|--------------|----------------------------|------------------|-----------------------|
| 100          | 1 (`add` only)             | ~0.000           | **0.100**             |
| 300          | 1 (`add` only)             | ~0.000           | **0.098**             |
| 1000         | 3                          | 0.022            | **0.300**             |
| 3000         | 8                          | 0.025            | **0.641**             |

## What it tells us
![Data scaling — flawed historical run of operation coverage](figures/fig_data_scaling.png)

*Flawed historical run (operation coverage, not data count): every point is one run on
a common held-out test set (one `pool_test`, 540 records = 10 operations × 54 each
after the per-op train/test split, reused across sizes), so the rates are integer
fractions over 540 (54/540 = 0.100, 53/540 = 0.098, 162/540 = 0.300, 346/540 =
0.641). The arms cover 1/1/3/8 of the 10 operations while the test covers all ten —
the coverage confound stated in the audit note above — so the curve is kept as a
record of how an innocent slice construction invalidates a comparison, not as a
scaling result.*

One honest caveat about what "more data" means here, on top of the coverage confound.
Within a single operation family,
the records we generate share the same prompt→program mapping and differ only in
hidden-test *input values*; across the whole run, the pilot's 1,400 records contain only
**21 distinct prompt–program pairs**. So increasing the dataset size from 100 to 3000
records does **not** give the model 30× more distinct information — it gives it more
records of mostly the same mappings, *and* (the audit's finding) a different slice of
the operation list. Also, since the step
count is held fixed, a larger dataset means **fewer passes** over each record, not more
optimizer exposure. So the curve is best read as "given this coverage and this
repetition pattern, accuracy rose" rather than "more information bought more accuracy."
That is part of why Chapter 13 — which was *designed* to vary the wording families —
was meant to be the proper test of information content (though, as that chapter now
records, its own construction was flawed too), and it is why we do not claim this
chapter shows a composition result (it measured familiar-task performance only).

**The scores rise as the pool grows — but the rise is confounded with operation
coverage.** pass@1 climbs from 0.10 at 100 examples to 0.64 at 3000; because the small
arms trained on one or a few operations while the test spans all ten, we cannot
separate "more records helped" from "more operations were covered." We therefore state
no minimum-data requirement, no plateau, and no knee: those lessons would be readings
of an operation-coverage curve. The honest statement is **four descriptive
measurements from a confounded sweep**, kept because the failure is instructive (it is
logged as P0-01 in Appendix B); the balanced, operation-stratified rerun that would
replace it is specified in the audit note above.

## The motif, restated

Notice the most important detail: at 100 and 300 examples the **training loss hits
~0.000** — the model has *memorized* its tiny training set — yet pass@1 is only ~0.10.
A loss of zero on a small set buys almost nothing on the held-out score. (With the
coverage confound in view, part of that ~0.10 gap is simply that nine of the ten
evaluated operations never appeared in a 100-record arm — which only sharpens the
point: a perfect fit to what it was shown said nothing about what it could do on the
full test.)

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
useless on new tasks" — is the single most instructive thing about this run. It is the
reason we never trust a training loss, and it is the reason the
whole book is organized around held-out measurement rather than training curves. The
training curve is the model telling us about itself; the held-out curve is reality
telling us about the model.

## The honest caveat

This experiment was *intended* to measure quantity, and did not even manage that
cleanly: the arms differ in operation coverage, so quantity was never isolated. It
also did not separate *quantity* from *diversity* —
whether 3000 examples of the same handful of phrasings behave the same as fewer
examples spread across more variety. That distinction (Chapter 13) is where the deeper
limits were expected to live: our surface and composition experiments suggest the model's real weakness
is a *diversity and structure* gap, not a *quantity* gap — though, again, Chapter 13's
own equal-count comparison did not survive code audit either, so neither lever has a
clean causal measurement yet.

### A note on uncertainty

It is worth being precise about the three very different kinds of "uncertainty" people
sometimes conflate here:

- **Fixed test score.** A pass@1 like 0.641 is the exact measured score on *this* test
  set, under this decoding and evaluation procedure. It is a property of that dataset.
- **Uncertainty over a target distribution.** If we wanted to say "the model scores
  ~0.64 on new tasks of this type," we'd need a sense of how much 0.641 would vary
  across different test sets. We report **descriptive scores only**: we did not estimate
  uncertainty for a defined target prompt distribution. (We did later re-run every
  dataset size under two additional seeds — see the multi-seed note below — but three
  seeds at two step budgets is a robustness check, not an estimated interval.) (We could in principle
  analyze conditional sampling uncertainty by examining repeated fresh generations for the
  same prompts, and designed/grouped evaluation could support other intervals under stated
  assumptions — but we did not do that here, so we do not claim those either.)
- **Seed variation.** The original sweep ran each condition with a single seed; the
  data-scaling sizes were later re-run under two more seeds (below). That does not mean every
  kind of interval is impossible — it means *seed variance* is only sampled at three
  seeds across two step budgets, and it does not
  quantify uncertainty over an arbitrary future prompt distribution. We treat the numbers
  as measured for the run we did, and as approximate for the underlying capability, rather
  than as a tight estimate.

A further caution against a naive confidence interval: the test set is not a set of
independent, uniformly-drawn examples. It comes from one generator, reuses a handful of
wording families and operation templates, and (in some splits) shares prompts across
conditions. So a standard binomial interval can be misleadingly tight, and a "3/n" upper
bound for a zero result assumes independent draws that this generator does not
provide. We therefore report raw counts and do not attach invented error bars.

### A note on multi-seed replication

One experiment we *did* re-run under more than one seed is the Stage-3 surface
test. Fresh trainings under seeds 1 and 2 reproduce the seed-0 run closely:
in-distribution 0.900 / 0.900 / 0.898, new identifiers 0.350 / 0.348 / 0.348,
and held-out wording 0.000 / 0.004 / 0.000 for seeds 0 / 1 / 2 (report
`docs/reviews/loop/multiseed_replication.md`). The shape of the result — a
familiar-prompt score near 0.90, a partial fall to ~0.35 on new identifiers,
and a collapse to ~0.00 on held-out wording — is stable across seeds, so it is
not a single-seed accident. Two carried-over caveats: the
RETRIEVAL baseline printed 0.000 on seeds 1 and 2 (seed 0 gave 1.000
in-distribution), a baseline-harness artifact of the re-runs rather than a
model result; and the new-identifier arm changes wording-family coverage along with
identifiers (Chapter 15, P0-03), so its ~0.35 is a mixed shift on every seed.

The data-scaling conditions have since been re-run the same way, under seeds 1 and 2
(same report). In-distribution pass@1 by dataset size:

| size | seed 0 (800 steps) | seed 1 (1000 steps) | seed 2 (1000 steps) |
|------|--------------------|----------------------|----------------------|
| 100  | 0.100 | 0.094 | 0.076 |
| 300  | 0.098 | 0.100 | 0.100 |
| 1000 | 0.300 | 0.300 | 0.300 |
| 3000 | 0.641 | 0.748 | 0.748 |

The monotone pattern reproduces on every seed — but every seed re-ran the *same*
prefix-of-an-operation-ordered-pool construction, so the re-runs replicate the
**confound**, not a data-count effect: seeds 1 and 2 cover the same 1/1/3/8 operation
slice at each size. Replication of a flawed design says the flaw is deterministic, not
that the causal reading is right. One further honest caveat: the step budget was
not identical across seeds — seed 0 ran at this chapter's 800 steps, seeds 1 and 2 at
1000 — and the size-3000 absolute moves with it: 0.641 at 800 steps versus 0.748 at
1000, with seed 1 = seed 2 = 0.748 at the same 1000-step budget.

## The practical answer

Four points, each read honestly.

First, these four points are **not** a data-count trend: 0.100 at 100 examples →
0.098 at 300 → 0.300 at 1000 → 0.641 at 3000 come from a sweep whose arms cover
1/1/3/8 of the ten operations, and the multi-seed re-runs reproduce the
same confounded construction on every seed. We therefore make **no** claim of the form
"performance improves as example count grows" or "there is a knee at 3000" — those
would require the balanced, operation-stratified rerun specified in the audit note
above, which is pending (Appendix B, P0-01).

Second, the recorded numbers are for a **multi-operation pool sliced by prefix**, not
a per-operation requirement. The 3000-record arm trains on eight of the
**ten seen operation IDs** (the operational "primitive"
pool; `cond_abs_max` is structurally composite — Chapter 16) because the pool is
built per-operation and then concatenated, and the prefix stops mid-list. So "the
model reached 0.641" is the aggregate
over the whole 3000-record pool with two operations never shown — it does **not** mean every individual
operation needed 3000 examples, nor that one operation on its own requires 3000. The
1,400-record pilot is likewise the whole task family, not 1,400 per primitive. (The
pilot's own 0.897 is coverage of seen prompt strings, not prompt generalization —
the "coverage is not transfer" row of the evidence table above; see Chapter 10.)

Third, the comparison is against a *common* held-out set within the run (one
`pool_test` reused at every size), which at least keeps the evaluation constant across
arms — the one part of the design that did hold fixed. It is a different set from the pilot's 300-case test, so these scores are
not directly comparable to the pilot's 0.897 (denominator row, evidence table above).

Fourth — and anticipating the rest of the book — the reworded-wording experiment
(Chapter 15) found the trained model surface-fragile on held-out rewordings, so a higher
familiar-task score does not by itself indicate surface robustness. Composition is a
separate question that this chapter did not measure; we do not yet know whether more data
of any kind would help it, and we say so rather than assume the answer.

The practical takeaway is thus deliberately empty on the quantity question, and that
is the honest state of it: **this chapter does not establish what more data buys**,
because its sweep changed operation coverage along with count. What it does establish
is the motif — a perfect fit to a tiny set bought ~0.10 on the full held-out pool —
and the method lesson: an innocent `pool[:size]` slice can turn a one-variable
experiment into a two-variable one, which is exactly why the failure ledger exists
(Appendix B). Whether robustness to rephrasing or compositional
generalization is purchased by data is a separate question: this chapter only measured the
familiar-task score, so it does **not** answer it. Chapter 13 asks whether more *diverse*
data buys surface robustness (its own construction also needs correction before it can
answer), and Chapter 16 asks about composition — each with its own
caveats about what it can and cannot show.