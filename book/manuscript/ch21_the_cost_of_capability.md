# 19. The Cost of Capability

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

Before the matrix, the conclusion this chapter helps build, in the conservative form we
now adopt (third external review, 2026-11-02), strengthened by the corrected reruns: the
model frequently produced executable, correct Python for training-seen prompt strings even
on new input values, but that does not establish generalization to new natural-language
requests; severe failures appeared under altered wording and on untrained structures; the
corrected data-scaling sweep is flat (~0.90 from 10 to 300 examples per operation), so
record count buys nothing in this regime; and the corrected surface factorial collapses
to ~0 on any prompt-surface change. The corrected equal-count diversity rerun now
prices surface diversity: at 1,200 records per arm it moves a genuinely held-out
phrasing family from **0.000 to 0.550 mean**, at a small in-distribution cost
(**0.950 → 0.743 mean**). One row of the
matrix below is the superseded flawed study, and we price nothing from it; the
data-scaling, surface, and diversity rows now carry their corrected replacements.

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
evaluation denominator. The continual rows count generated tasks, derived from
`run_continual.py` at `n_per=70` (per `continual.json`): capability A is 5 operations
(350 tasks), capability B is 3 operations (210 tasks), and the joint run interleaves
all 560 — the 1,400 in the steps column is the separate 700 + 700 step budget.

| Run | data records / unique pairs | parameters | steps |
|------------------|-----------------------------|------------|-------|
| `stage1` | 1,400 / 21 | 0.88M | 1,500 |
| `stage3_surface` (superseded, P0-03/P0-04) | 600 (10 op × 60) familiar/new-ID; **480** (8 op × 60) reworded | 0.88M | 1,500 |
| `surface_corrected` (fixes P0-03/P0-04) | 600 train (60 op × 10); cells of 600 / 600 / **480** / **480** | 0.88M | 1,500 |
| `data_scaling` (superseded, P0-01) | 100, 300, 1000, 3000 (**prefix of an operation-ordered pool: 1/1/3/8 of 10 ops**) | 0.88M | 800 |
| `data_scaling_corrected` (per size; fixes P0-01) | 100 / 300 / 1000 / 3000, balanced **10/30/100/300 per op, 10/10 ops** | 0.88M | 1,000 |
| `diversity` (Ch13 — superseded flawed historical, P0-02) | requested 1,200; **realized 42** (high) vs 1,200 (minimal) | 0.88M | 900 |
| `diversity_corrected` (Ch13; fixes P0-02) | **1,200 / 1,200** (low/high), balanced 120 per op, 10/10 ops; 20 vs 605 unique pairs | 0.88M | 1,000 |
| `stage4_exposure` | not recorded | 0.88M | 1,500 |
| `compdiv_minimal` / `compdiv_high` | not recorded | 0.88M | 1,500 |
| size sweep | not recorded | 0.88M / 6.5M / 10.2M / 29.3M | 1,500 / 1,000 / 800 / 800 |
| `continual_seq` | 350 + 210 | 0.88M | 1,400 |
| `continual_joint` | 560 interleaved | 0.88M | 1,400 |

**Table 19.2 — Measured outcomes, by run** (the neural **MODEL**'s score; baselines are in
Chapters 15 and 16, not here). Run keys match Table 19.1. The three **corrected** rows
(`surface_corrected`, `data_scaling_corrected`, `diversity_corrected`) give the model's
per-seed scores on the
four factorial cells, on the flat size sweep, and on the equal-count diversity
comparison; the superseded rows keep the original
`stage3_surface` / `data_scaling` / `diversity` values for the record. `0.875`/`0.683`
belong to the
TEMPLATE/RETRIEVAL baselines and are not the model's.

| Run | in-dist | new IDs | new wording | composes |
|------------------|---------|---------|-------------|----------|
| `stage1` | 0.897 | — | — | 0.000* |
| `stage3_surface` (superseded†‡) | 0.900 | 0.350† | 0.000‡ | — |
| `surface_corrected` | 0.898 / 0.900 / 0.940 | 0.000 / 0.003 / 0.005 ¶ | 0.000 (both changes: 0.000 / 0.025 / 0.000) ¶ | — |
| `data_scaling` (superseded§) | 0.100 / 0.098 / 0.300 / 0.641 § | — | — | — |
| `data_scaling_corrected` | 0.893–0.997, **flat** across 100→3000 ¶ | — | — | — |
| `diversity` (superseded‖) | 0.500 minimal / 1.000 high | — | 1.000 high (covered families) | — |
| `diversity_corrected` | 0.950 low / 0.743 high ‖ | — | 0.000 low / **0.550** high ‖ | — |
| `stage4_exposure` | 1.000 | — | — | 0.667 / 0.000 |
| `compdiv_minimal` | 1.000 | — | — | 0.592 / 0.000 |
| `compdiv_high` | 1.000 | — | — | 0.550 / 0.000 |
| size 0.88M | 0.9167 (n=60; see Appendix C.5) | — | — | 0.000 |
| size 6.5M | 0.897 | — | — | 0.000 |
| size 10.2M | 0.773 | — | — | 0.000 |
| size 29.3M | 0.897 | — | — | 0.000 |
| `continual_seq` | A 1.000→0.000; B 0.889 | — | — | — |
| `continual_joint` | A 1.000; B 0.889 | — | — | — |

*`stage1`'s composes value (0.000) is from the stage-4 re-evaluation of that pilot
checkpoint. † the new-identifier arm changes identifiers and wording-family coverage
together (P0-03), so 0.350 is a mixed-factor shift — superseded by the identifiers-only
cell of `surface_corrected`, which is ~0. ‡ the reworded arm has 480 records over 8
operations, not 600 over 10 (P0-04) — superseded by the corrected factorial's
wording-only cell, 0.000 over 480 in every seed. § the data-scaling arms are prefixes of
an operation-ordered pool covering 1/1/3/8 of the ten operations (P0-01), so this row is a
confounded historical run of operation coverage, not a record-count curve — superseded by
`data_scaling_corrected`, which is flat; we price nothing from the old row. ¶ corrected
runs (Appendix C, Tables C.13/C.14): `surface_corrected` cells are scored over
600/600/480/480 records with `abs_of` and `cond_abs_max` excluded from the held-out cells
(8 ops × 60); `data_scaling_corrected` arms are balanced 10/10 operations under one fixed
tokenizer against one shared 300-task test, so the row is a flat curve, not a trend. ‖
corrected equal-count diversity (Appendix C, Table C.15): both arms exactly 1,200
records, 10/10 operations at 120 per operation, one fixed tokenizer, matched
1,000-step protocol; the "new wording" cell is the genuinely held-out phrasing family
(h01/h02, 100 tasks, zero family/prompt collisions against both arms), per seed LOW
0.000 / 0.000 / 0.000 vs HIGH 0.640 / 0.300 / 0.710 (means 0.000 vs 0.550), with
in-distribution LOW 0.950 in every seed vs HIGH 0.820 / 0.570 / 0.840 (means 0.950 vs
0.743); the superseded `diversity` row realized 42 records against 1,200 (P0-02), so we
price nothing from it. The
`stage4_exposure` and `compdiv_*` composes values are reported as
*exposed* / *held-out* (e.g. 0.667 exposed, 0.000 held-out, over n=120 exposed records
each); the held-out composite — the transfer test — was 0.000, and for the run where we
analyzed it (the composition-exposure run, Appendix B.10) the held-out candidates failed
parsing before semantic evaluation. We do not extend that parsing finding to the other
size checkpoints, whose recorded stage rates we did not analyze the same way. The
continual rows test
task *retention*, not composition, so their "composes" cell is `—`. Note that the
`compdiv_*` rows (both in-dist 1.000, composes 0.592/0.550) are the **composition-
diversity** intervention runs from Chapter 16/Appendix C (`composition_diversity_pilot`,
1,500 steps) — a different experiment from Chapter 13's quantity-vs-diversity
comparison, now reported as the corrected equal-count run `diversity_corrected`
(1,000 steps; LOW arm in-distribution 0.950), whose flawed first version
(`diversity`, 900 steps, minimal in-distribution 0.500) is superseded. They
are not the same run, so the different in-distribution numbers are not a conflict.*

*Legend: `—` = that specific breakdown was not separately reported for that run (or the run
did not test it). We reserve an explicit `0.000` for outcomes we measured and that came out
negative, and use `—` when the run did not report that figure.*

A few cautions before reading this as a budget — the shared justifications live in the
evidence table at the start of Chapter 11; what follows is what each caution means for
*these* rows. First, the Stage-1 pilot's "1,400 records"
is the **ten-operation familiar-prompt family** total, which contained only **21 distinct
prompt–program pairs**; it is not a measured per-operation data requirement, and its 0.897
is single-sample correctness for repeated previously-seen prompt strings under fresh
execution values, not prompt generalization. Second, the
size sweep changed training budgets (1,500 / 1,000 / 800 / 800 steps) and tokenizer, so it
is not a size-only intervention. Third, three rows are **superseded flawed constructions**
(Appendix B) with corrected replacements now in the matrix: the old `data_scaling` row is
a prefix of an operation-ordered pool (arms cover 1/1/3/8 of the ten operations — P0-01),
replaced by the flat `data_scaling_corrected` row; the old `stage3_surface` rows mixed
factors and denominators (P0-03, P0-04), replaced by the `surface_corrected` factorial;
and the old `diversity` row realized **42 records against 1,200** (P0-02), replaced by
the equal-count `diversity_corrected` row — we draw no budget lesson from the flawed row
itself. Fourth, the exposed-composite scores varied (0.550, 0.592,
0.667); the held-out composite — the transfer test — was **0.000** at every size we tried.
For the run where we analyzed stage rates (the composition-exposure run, Appendix B.10) the
held-out candidates failed parsing before semantic evaluation; we do not extend that to the
other size checkpoints, whose recorded stage rates we did not analyze the same way, and the
0.88M baseline has a different recorded profile (0.183 of held-out candidates parsed, none
executable). So the cause of that zero is unresolved across the size sweep (Chapter 16). We
do not know how much data would be needed to achieve composition; we only know it was not
achieved within the budgets we tried.

## What the costs tell us

**Capability is cheap; robustness is not.** Learning the ten-op familiar family cost
~1,400 records and a few minutes on a 0.88M model, and it "works" in-distribution (0.897).
So the *apparent* cost of a capability is low. But that number is misleading: it measures
only in-distribution correctness on prompts the model has seen.

**The real cost appears when we ask for generalization.** Two levers were meant to price
robustness, and both now have measurements. *More data of the same kind* is priced at
**zero marginal return**: the corrected sweep (Chapter 11) is flat at ~0.90 from 10 to
300 examples per operation, so record count buys nothing — not capability, not
robustness — in this regime. *More diverse data* is priced by the corrected equal-count
rerun (Chapter 13): at the same 1,200-record budget, spreading the data across more
phrasings and five identifier sets moves a genuinely held-out phrasing family from
**0.000 to 0.550 mean** (three seeds) and costs some in-distribution sharpness
(**0.950 → 0.743 mean**) — so "train on diverse identifiers and wording" is a measured
price, not just a lead, and capacity was never the
promising lever either. What the corrected surface factorial does price is the failure
itself: the same 600-record budget that yields ~0.90 on the familiar surface yields 0–3
of 600 on new identifiers and 0 of 480 on held-out wording — robustness to surface change
was not bought at any budget we tried. And composition was not achieved at any size we tried: it stayed 0.000 on
held-out at 0.88M, 6.5M, 10.2M, and 29.3M. As the cautions above state, the parsing
finding applies only to the composition-exposure run, so the cause of that zero is
unresolved.

**The cost matrix makes a dangerous pricing error visible.** If we only look at the
"in-dist" column, we would conclude capability is nearly free and scale up naively. The
generalization and composition columns reveal that the cheap number hides a much more
expensive requirement — robust, compositional capability. On that requirement, capacity
scaling was tested on composition and remained 0.000 at every size we ran; the
superseded diversity row supports no pricing at all, while the corrected diversity row
prices phrasing diversity as the lever that buys held-out-family transfer
(0.000 → 0.550 mean) at a small in-distribution cost (0.950 → 0.743 mean), and the
corrected data-count sweep prices
record count at **zero marginal return** (flat ~0.90 across a 30× range). The rows we
*can* price are the
ones with intact controls: the pilot's familiar-prompt cost, the corrected surface
factorial's robustness failure, the corrected data-scaling sweep's flat curve, the
corrected diversity comparison's diversity price, and the
continual-learning schedule comparison.

## The price of each column, read honestly

Let us read the matrix the way a person who has to pay for capability would read it,
not the way a researcher who wants a good headline would read it.

- **The ten-operation familiar-prompt family "costs" about 1,400 records and a few
  minutes.** That is the cheap row. Its in-distribution score was 0.897; the pilot itself
  did not run a reworded surface test (the Stage-3 surface run did, and scored 0.000 there).
  So we have bought a capability that works on the prompts it was trained with.
- **New-identifier and reworded robustness** (the corrected surface factorial) costs the
  same 600-record budget and still fails — the model drops to 0.000–0.005 on new
  identifiers alone (0–3 of 600) and to 0.000 on held-out wording in every seed (0 of
  480; both changes at once: 0.000–0.025), while TEMPLATE holds 0.800 / 0.875 and
  RETRIEVAL 1.000 / 0.125 on the same records. The superseded Stage-3 row's 0.350 was a
  mixed-factor reading (P0-03) and priced nothing. We cannot buy this robustness with
  more of the same data either — the corrected size sweep is flat (Chapter 11).
- **Held-out-wording robustness bought with diversity** (the corrected equal-count
  comparison, Chapter 13) costs the same 1,200-record budget in both arms: spending it
  on 605 distinct phrasings and five identifier sets rather than 20 lifts the
  genuinely held-out phrasing family from **0.000** (0 of 100, every seed) to **0.550
  mean** (0.640 / 0.300 / 0.710), while in-distribution falls from 0.950 to 0.743 mean.
  The diverse model still sits below TEMPLATE (0.700) and its own arm's RETRIEVAL
  (1.000) on that test, so the price of *partial* transfer is a little in-distribution
  sharpness — and the flawed 42-record first run (P0-02) priced nothing.
- **Composition** is the row that tells the sharpest story. It was 0.000 on held-out
  composites at every parameter size we tried (0.88M, 6.5M, 10.2M, 29.3M), and the
  parameter column alone did not change that in the runs we ran. But the failure cause is
  unresolved — the parsing finding is scoped to the composition-exposure run (see the
  cautions above) — so this is a recorded
  negative result, not a demonstrated mechanism. The exposed composites (0.550–0.667) also
  fell short of mastery on the *training-covered* combinations, so the model did not even
  fully learn those it was shown.
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
in-distribution *look* capable while it collapses to 0.000 on a reworded instruction and
to 0.000–0.005 on a new identifier — any change to the surface. In a deployed
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
