# 11. How Much Data?

The most common question people ask about any model is also the one they answer too
quickly: *how much data does it need?* We set out to measure it directly — holding the
model, the tokenizer, the operation mix, and the training method fixed, and varying only
the number of examples.

It is a question worth measuring rather than guessing, because the folklore answer —
"just add more data" — is both plausible and unexamined. Our own first attempt at the
measurement did not survive code audit: the sweep changed the operation mix along with
the count, so its rising curve was an artifact of coverage, not of data (Appendix B,
P0-01). The balanced, operation-stratified rerun that audit called for has since been
done — three seeds, one fixed tokenizer, one fixed test set — and its answer is the
opposite of the folklore: **no consistent monotonic effect on familiar-prompt accuracy is
detected here.** Once every size covers the same ten operations, the scores sit in a
narrow band around 0.90 across a 30× range in the number of examples per operation —
with one flagged outlier (seed 2 at size 1,000, 0.997), called out below.

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
| **Coverage is not transfer.** | A score on prompts, surfaces, or operations the training pool already covers measures *coverage*, not generalization to something never seen. The pilot's 0.897 is single-sample correctness on reused training prompt strings; the corrected data-scaling sweep's ~0.90 is an instance-level holdout (new construction seeds and new hidden tests) over the same 21 prompt strings; Chapter 13's superseded flawed-run 1.000 was coverage of its own training families; its corrected equal-count run tests an audited held-out family instead (0.550 mean). | Ch. 10, 11, 13, 14, 20 |
| **The 0.88M baseline denominator.** | The familiar-prompt numbers — 0.897 (pilot, 300-record test), 0.898–0.940 (corrected surface factorial, 600 records), 0.9167 (Stage-4 baseline, n=60) — are different evaluation sets, not a discrepancy. The figure they agree on is composition 0.000. | Ch. 12, 16, 19, 20 |
| **Model-size budget differences.** | The size sweep varied training budget and tokenizer alongside size (1,500 / 1,000 / 800 / 800 steps; pilot vs. composition tokenizer), so it is not a size-only intervention. | Ch. 12, 19, 20 |
| **Old vs. new novelty audits.** | The pilot was audited on the original scored files; the Stage-3 and Stage-4 holdouts were audited on *regenerated* reproductions with the current generator — corroborating, but not proof on the scored artifacts. | Ch. 13, 15, App. C |
| **Superseded flawed historical runs.** | Ch. 11's original data-scaling sweep (P0-01: operation coverage) and Ch. 15's original surface rows (P0-03: mixed factors; P0-04: 480-record denominator) are preserved as labeled flawed records in the failure ledger (Appendix B) and as superseded rows in Appendix C; their corrected reruns are this chapter's and Chapter 15's actual results. Ch. 13's diversity comparison (P0-02: 42 vs. 1,200 records) now has a corrected
equal-count rerun (Table C.15), which finds diversity drives held-out-family generalization. | Ch. 11, 13, 15, 19, 20 |

**What a later code audit showed — read this before the numbers.** The original sweep
did not change only the data count. The script builds one pool with
`pool = generate_dataset(n_per_op=400, ...)` and trains on `train = pool[:size]` — a
*prefix* of a pool the generator appends record by record **in operation order**. The
100- and 300-record arms therefore trained on **one operation out of ten** (`add`), the
1,000-record arm on **three**, and the 3,000-record arm on **eight** — while the
evaluation set spanned all ten operations. That sweep was thus **confounded with
operation coverage**: what changed across its four arms was not just how many records
the model saw, but *which operations it saw at all*. The recorded curve is preserved in
the failure ledger (Appendix B, P0-01) as a **flawed historical run of operation
coverage**, not a data-count scaling result. We draw no threshold, no knee, and no
data-efficiency lesson from it, and the earlier claim that "only the data count changes"
was wrong. The balanced, operation-stratified rerun the audit called for — the same
number of records per operation at every size, one fixed tokenizer, matched step
budgets — has now been run, and it is the experiment reported in the rest of this
chapter. The confounded curve reappears once below, kept only so a reader can see what
the flaw looked like.

## The setup

We train the same ~0.9M model (128 embedding / 4 layers / 4 heads, block size 128), the
same optimizer and schedule — 1,000 steps, batch 16, learning rate 1e-3 — on four
dataset sizes: 100, 300, 1,000, and 3,000 examples. Three things are held fixed that
the first attempt let drift:

- **Operation coverage.** Every arm draws the *same* balanced slice: 10, 30, 100, and
  300 records **per operation**, so all four sizes cover all ten operations (the pool is
  400 records per operation; the slices are nested across sizes and shuffled). What
  changes across arms is only how many records each operation contributes.
- **The tokenizer.** One tokenizer, fit once on the union of the training texts at the
  largest size and reused unchanged across every size and every seed (vocabulary 291;
  SHA-256 `361f6d89e4f18642fac9d1d9077d6a5cab0e5d97701bafc1641ab09ec2b10eb5`).
- **The test set.** One fixed held-out set of 300 tasks — 30 per operation × 10
  operations — generated once and reused for every size and every seed, so all twelve
  arms are scored against the identical denominator.

The test set is an *instance-level* holdout: new construction seeds and new hidden test
inputs, but the same 21 prompt strings the generator produces for these ten operations —
so, per the evidence table above, its ~0.90 is coverage of seen prompt strings on fresh
instances, not transfer to new requests. Each arm is trained from scratch under seeds
0, 1, and 2, giving twelve measurements.

## The result

Model pass@1 on the shared 300-task test:

| training size | per operation | seed 0 | seed 1 | seed 2 |
|---------------|---------------|--------|--------|--------|
| 100           | 10            | 0.897 (269/300) | 0.893 (268/300) | 0.900 (270/300) |
| 300           | 30            | 0.900 (270/300) | 0.900 (270/300) | 0.900 (270/300) |
| 1,000         | 100           | 0.893 (268/300) | 0.900 (270/300) | 0.997 (299/300) |
| 3,000         | 300           | 0.897 (269/300) | 0.900 (270/300) | 0.900 (270/300) |

Eleven of the twelve arms land between 0.893 and 0.900; the twelfth (seed 2 at size
1,000) is 0.997. The baselines barely move either: TEMPLATE scores 0.800 (240/300) in
all twelve arms, RETRIEVAL 1.000 in eleven of them and 0.943 (283/300) in the twelfth.
Final training losses sit in a narrow band, 0.0177–0.0243, with no trend by size.

## What it tells us
![Data scaling — corrected balanced sweep](figures/fig_data_scaling.pdf)

*Corrected sweep (fixes P0-01): every point is one run on the shared 300-task test set
(30 per operation × 10 operations, generated once and reused across sizes and seeds), so
the rates are integer fractions over 300 (seed 0: 269/300, 270/300, 268/300, 269/300).
All four arms cover all ten operations — 10/30/100/300 records per operation — under one
fixed tokenizer and one 1,000-step budget, so the only thing that changes along the axis
is the record count. **No consistent monotonic effect on familiar-prompt accuracy is
detected here** once operation coverage is held fixed: eleven of the twelve arms sit at
0.893–0.900, and the twelfth — seed 2 at size 1,000, 0.997 (299/300) — is the outlier
flagged below, not a trend. The earlier 0.100 → 0.641 rise was the
operation-coverage confound, preserved only as a labeled flawed historical run in the
failure ledger (Appendix B, P0-01). Decoding is temperature-0.8 single-sample.*

The near-flat line is the result. Across a 30× range — from 10 to 300 examples per
operation — pass@1 stays at ~0.90, and no consistent monotonic effect on familiar-prompt
accuracy is detected here. Whatever the model learns from these records, it has
learned essentially all of it by the smallest arm; the additional records at the largest
arm move the score by hundredths, within seed noise. This is what a one-variable data
experiment looks like when it is actually one variable: no knee, no threshold, no ramp —
just a plateau (one seed-2 outlier excepted) that was already there at 100 records.

The per-operation picture sharpens the same point. Nine of the ten operations score
0.967–1.000 in every arm (one exception: `list_len` at 0.433 in seed 1's smallest arm).
The lone persistent failure is `cond_abs_max`, which scores 0.0 in nine of the twelve
arms — and more data does not rescue it: at the largest size, 300 examples per
operation, it is still 0.0 in all three seeds. An aggregate over operations can hide a
per-operation hole, and record count did not fill this one.

**The one aggregate that breaks the band is flagged, not smoothed over:** seed 2 at size
1,000 scores **0.997 (299/300)**, the only arm above 0.900. Its per-operation breakdown
shows it is a one-arm fluke, not a data-size effect: that is the arm where
`cond_abs_max` scored 1.0 — the same operation that scores 0.0 in nine of the twelve
arms — and its only miss is `max_of` at 29/30. So the outlier is the per-operation hole
above happening to close in one arm, not evidence that 100 records per operation beat
300.

**The earlier curve was an operation-coverage confound.** The first sweep recorded
0.100 → 0.641 from 100 to 3,000 records and was read as data scaling. It was not: the
arms were prefixes of an operation-ordered pool, covering 1/1/3/8 of the ten operations
while the test spanned all ten, so the rise tracked *which operations the model had
seen at all*, not how many records it had. With coverage held fixed, the rise disappears
entirely. The old numbers are kept below and in the failure ledger as a record of the
flaw, not as a result.

## The flawed historical run, preserved

| dataset size | operations trained (of 10) | final train loss | pass@1 (held-out) |
|--------------|----------------------------|------------------|-------------------|
| 100          | 1 (`add` only)             | ~0.000           | **0.100**         |
| 300          | 1 (`add` only)             | ~0.000           | **0.098**         |
| 1000         | 3                          | 0.022            | **0.300**         |
| 3000         | 8                          | 0.025            | **0.641**         |

*Flawed historical run (P0-01), preserved for the failure ledger only: one seed, one
540-record `pool_test` (10 operations × 54), arms covering 1/1/3/8 of the ten
operations, tokenizer refit per size. Its multi-seed re-runs (0.076–0.748 by size;
Appendix C, Table C.9) repeated the same construction, so they replicate the confound,
not a data-count effect. We draw no threshold, no knee, and no data-efficiency lesson
from any of these numbers; they are superseded by the corrected sweep above.*

## The motif, restated

The book's central motif — **a low training loss is not evidence of learning** — was
first made concrete by this experiment's flawed first run: at 100 and 300 examples the
training loss hit ~0.000, the model had memorized its tiny training set, yet pass@1 on
the full test was only ~0.10 (part of that gap was simply that nine of the ten evaluated
operations never appeared in a 100-record arm). A perfect fit to what the model was
shown said nothing about what it could do on the full test.

The corrected sweep adds the motif's second half: the training losses now sit in a
narrow band (0.0177–0.0243) across every size and seed, and the held-out scores sit in
an equally narrow band (~0.90). Neither curve moves when the record count moves
thirty-fold. Only the held-out number tells us about actual capability — and in this
experiment, once the design was fixed, it told us the same thing at every size.

## The brewing experience

The instructive moment in this chapter is watching the corrected curve come back flat.
The folklore answer predicted a rise; the first (flawed) run had produced a beautiful
rising curve; the balanced rerun produced a horizontal line from the first arm to the
last. The surprise is not that the line is flat — it is that an innocent `pool[:size]`
slice had manufactured a convincing rising curve out of pure coverage, and that the
manufactured curve survived multi-seed replication before anyone read the script against
the claim.

That is why the book is organized around held-out measurement *and* code–claim
auditing: a held-out score tells us what the model can do, but only reading the
arm-building code tells us what the experiment actually varied. The training curve is
the model telling us about itself; the construction is the experiment telling us about
itself; both have to be audited before either means anything.

## The honest caveat

This experiment now measures quantity cleanly, and the answer is a null: within this
regime — one ~0.9M model, one task family, 100 to 3,000 balanced records — more records
of the same kind do not raise the familiar-prompt score. What it does *not* measure is
whether more *diverse* data would help. Quantity and diversity are different levers:
within an operation family, records share the same prompt→program mapping and differ
only in hidden-test input values, so 3,000 records are not 30× more distinct
information than 100. Chapter 13's first attempt at varying the wording families did
not survive code audit (42 versus 1,200 records — P0-02), but Chapter 13 subsequently
ran an equal-count diversity comparison — both arms exactly 1,200 records, three seeds —
that measures the diversity lever cleanly: held-out-family pass@1 of 0.000 (low
diversity) versus 0.550 mean (high diversity). Chapter 15 — now backed by a
corrected factorial — shows the model's real weakness is a *surface* gap: it collapses on
any prompt-surface change, which none of this same-surface data addressed. Composition
(Chapter 16) is a separate question this sweep did not test: the corrected arms were
scored on the in-distribution test only, so "more data does not help composition" remains
untested and unclaimed.

### A note on uncertainty

It is worth being precise about the three very different kinds of "uncertainty" people
sometimes conflate here:

- **Fixed test score.** A pass@1 like 0.897 is the exact measured score on *this* test
  set, under this decoding and evaluation procedure. It is a property of that dataset.
- **Uncertainty over a target distribution.** If we wanted to say "the model scores
  ~0.90 on new tasks of this type," we'd need a sense of how much 0.897 would vary
  across different test sets. We report **descriptive scores only**: we did not estimate
  uncertainty for a defined target prompt distribution. The corrected sweep ran three
  seeds at one step budget (below) — a robustness check, not an estimated interval. (We
  could in principle analyze conditional sampling uncertainty by examining repeated fresh
  generations for the same prompts, and designed/grouped evaluation could support other
  intervals under stated assumptions — but we did not do that here, so we do not claim
  those either.)
- **Seed variation.** The corrected sweep ran seeds 0, 1, and 2 from the start (the
  table above), so seed variance is sampled at three seeds across a single 1,000-step
  budget; that does not quantify uncertainty over an arbitrary future prompt
  distribution. We treat the numbers as measured for the run we did, and as approximate
  for the underlying capability, rather than as a tight estimate.

A further caution against a naive confidence interval: the test set is not a set of
independent, uniformly-drawn examples. It comes from one generator, reuses a handful of
wording families and operation templates, and shares its 21 prompt strings with the
training pool (only the construction seeds and hidden inputs are new). So a standard
binomial interval can be misleadingly tight, and a "3/n" upper bound for a zero result
assumes independent draws that this generator does not provide. We therefore report raw
counts and do not attach invented error bars.

### A note on multi-seed replication

The corrected data-scaling sweep was built as a three-seed experiment (seeds 0/1/2, table
above), so its flatness is not a single-seed accident. Two earlier replications survive
as historical records only: the *flawed* sweep's re-runs under seeds 1 and 2
(0.076–0.748 by size; Appendix C, Table C.9) replicated the coverage confound, not a
data-count effect — replication of a flawed design says the flaw is deterministic — and
the Stage-3 surface re-runs (in-distribution 0.900 / 0.900 / 0.898, new identifiers
0.350 / 0.348 / 0.348, held-out wording 0.000 / 0.004 / 0.000 for seeds 0 / 1 / 2)
replicated a mixed-factor construction. Both are superseded: the surface numbers were
replaced by the corrected 2×2 factorial of Chapter 15 (familiar 0.898 / 0.900 / 0.940;
identifiers-only 0.000 / 0.003 / 0.005; wording-only 0.000 in every seed), and the
data-scaling numbers by the corrected sweep above. The old rows remain in Appendix C,
labeled as superseded flawed historical runs.

## The practical answer

Four points, each read honestly.

First, the corrected sweep gives the quantity question a real answer: **no consistent
monotonic effect on familiar-prompt accuracy detected here** — 0.893–0.997 across
100 → 3,000 records (eleven of the twelve arms 0.893–0.900; the twelfth is the flagged
seed-2 size-1,000 outlier at 0.997), with all ten operations covered at every size, one
fixed tokenizer, and one shared 300-task test. We make **no** claim of the form "performance improves as example count
grows," because the measurement says it does not — within this regime. The earlier
0.100 → 0.641 curve is not a data-count trend at all; it is the coverage confound,
preserved only as a labeled flawed historical run (Appendix B, P0-01).

Second, the sizes are per-operation counts inside one ten-operation family: 10, 30, 100,
and 300 records per operation, aggregated over the ten. So "the model reached ~0.90 at
size 100" means ten records per operation sufficed for nine of the ten operations — not
that one operation needed 100 records, and not that the pilot's 1,400-record family
translates into a per-primitive requirement. The exception is `cond_abs_max`, still 0.0
at 300 records per operation, a per-operation hole that record count did not fill
(Chapter 16 notes it is structurally composite).

Third, the comparison is against one *common* held-out set within the run (the same 300
tasks at every size and seed) — the evaluation is constant across arms by construction.
It is a different set from the pilot's 300-case test, so these scores are not directly
comparable to the pilot's 0.897 (denominator row, evidence table above), and both are
coverage of seen prompt strings rather than prompt generalization.

Fourth — and anticipating the rest of the book — a flat ~0.90 familiar-prompt score says
nothing about surface robustness: Chapter 15's corrected factorial shows the same model
collapsing to ~0 on new identifiers, on held-out wording, and on both together, so even
a higher familiar-task score would not indicate surface robustness. Composition is a
separate question this sweep did not measure; we do not claim anything about whether
data of any kind would help it, and we say so rather than assume the answer.

The practical takeaway on quantity is therefore a genuine result: **more of the same data
produced no consistent monotonic effect on familiar-prompt accuracy detected here, and we
measured that rather than assumed it.** What remains is the method
lesson — an innocent `pool[:size]` slice can turn a one-variable experiment into a
two-variable one, and the corrected rerun is what it takes to get the variable back,
which is exactly why the failure ledger exists (Appendix B). Chapter 13 answers whether
more *diverse* data buys surface robustness — its corrected equal-count rerun moves a
held-out family from 0.000 to 0.550 mean — and Chapter 16 asks about composition — each
with its own caveats about what it can and cannot show.