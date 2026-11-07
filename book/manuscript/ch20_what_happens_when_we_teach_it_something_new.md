# 18. What Happens When We Teach It Something New?

Every chapter so far has asked how the model handles one task. But real capability
isn't learned in one shot — it's *grown*, by adding new things over time. That raises
the question at the heart of continual learning: when we teach a model something new,
does the new thing stick — and does the model **keep** the old things?

There's a well-known failure mode with a scary name: **catastrophic forgetting** — the
tendency of a model, after training on task B, to lose what it learned on task A. We
want to know whether that happens to our small model, and, crucially, whether the
*way* we train determines it.

It is like learning a new language. Study French for a year, then stop
and study Spanish exclusively — how much French is left? A lot depends on whether
French keeps being practiced while Spanish is learned — which is exactly what this
experiment tests. And it is a question almost every learning system faces: a deployed
model is rarely trained once and frozen. It is updated, re-trained, fine-tuned on new
data. So whether it *keeps* what it knew is a practical concern, not an academic one.

## The setup

We split the operations into two capabilities:

- **Capability A — arithmetic:** `add`, `sub`, `mul`, `max_of`, `min_of`.
- **Capability B — lists:** `list_sum`, `list_len`, `first_element`.

We train on A, then introduce B, and measure both:
- **B acquisition** — did it learn the new capability?
- **A retention** — did it keep the old one, or did learning B destroy it?

This double measurement is the crux of the design. Many continual-learning reports
measure only whether the model acquired the *new* task, and that alone can make the
whole thing look like a success. But the interesting failure is usually what was *lost*
to get there. So we insist on measuring both, every time.

We run this under two protocols, changing only the *order and mixing*, not the model,
data, or optimizer:

- **sequential:** learn A fully, then learn B with no A exposure.
- **joint / interleaved (A+B from start):** interleave A and B examples throughout
  (earlier drafts of this chapter labeled this condition "replay"; we now call it
  joint/interleaved, because true replay means continuing from an A-trained checkpoint
  with A examples mixed back in — see the note below).

Holding model, data, and optimizer constant while changing only the training
*schedule* is a textbook application of our one-variable discipline. If the results
differ between the two protocols, the difference cannot be attributed to the model,
the data, or the optimizer — it must be the schedule. That makes any difference we
find a *procedure* finding, exactly the thing we want to isolate.

## The result
![Task accuracy: sequential versus joint/interleaved (A+B from start), with the sequential same-run A-before-B measurement](figures/fig_continual.pdf)

| Protocol | **A right after phase A (same run, pre-B)** | **A accuracy (final)** | **B accuracy (final)** |
|----------|---------------------------|-----------------|-------------------|
| **sequential** | **1.000** | **0.000** | 0.889 |
| **joint/interl.** | — (A and B trained together) | **1.000** | 0.889 |

*Both A measurements in the sequential row come from the **same run**: the 1.000 is
measured right after phase A and before any B exposure, the 0.000 after phase B
(Appendix C.9); the final is measured after phase B.
The **joint/interl.** row is the **joint/interleaved (A+B from start)** condition — the
label is shortened here so the first column does not overflow into the second.
The joint/interleaved model has no separate "after A" point because A and B are trained together from
the start. **Denominators:** A accuracy is on 60 held-out A tasks (12 × 5 operations)
and B accuracy on 36 held-out B tasks (12 × 3); at n = 36 one item = 0.028, so equal
B accuracy = within one test item.*

This is as clean a result as this book produced.

**A note on what "0.000" does and does not show.** We measured the sequential run's A
accuracy **right after phase A and again after phase B** along the same training
trajectory. The pre-B A accuracy was **1.000**; after learning B, A fell to **0.000**. So
the sequential zero is not a case of "A was never acquired" — A was acquired to 1.000 and
then lost. This is a **same-trajectory before/after** measurement, taken on a dedicated
re-run of the sequential pipeline with an intermediate A evaluation inserted right after
phase A and before any B exposure (Appendix C.9; also captured in the `continual_preB`
manifest) — which is what supports reading the sequential drop as genuine forgetting of
learned A competence rather than under-acquisition.

**Sequential training produces a much lower final A accuracy than joint training.** After
learning arithmetic and then lists in sequence, the model's final A accuracy is **0.000**;
when the two are trained together, the final A accuracy is **1.000**, with the same B
accuracy (0.889) in both. So the *training schedule* – whether the first capability stays
in the mix while the second is learned – is what differs, and that scheduling difference
changes the final A outcome. That is a *procedure* finding about final accuracy, and it
reinforces the same-run before/after point above: the sequential drop is genuine
forgetting, not under-acquisition.

**Training A and B together keeps A's final accuracy high.** When A and B are simply trained
together from the start (interleaved throughout), the model's final A accuracy is a
perfect **1.000**, and its final B accuracy is **0.889** — identical to sequential at
seed 0 (32/36 vs 32/36; across seeds the two protocols' B accuracy is within one test
item). So
training both from the start keeps A **with no behavioral trade-off** in B. Note that
this jointly trained model has no separate "after A" point (A and B were trained
together from the start), so its A accuracy is a final accuracy, not a retention score
relative to an A-only checkpoint.

One honest note on the term "replay," which earlier drafts used for the interleaved
condition. This design interleaves A and B **from the start** — which is *joint
training* on both, not "learn A first, then continue to B while replaying A." We have
therefore renamed the condition **joint/interleaved (A+B from start)** wherever it
appeared as "replay," because "replay" properly names a different design. Both designs
are legitimate, but they are different questions. The
sequential condition is a true continual-learning setup (does learning B destroy A? —
yes, 0.000). The interleaved condition is a joint-training control (if both are seen
together, is there a forgetting problem at all? — no, 1.000). The timelines below make
the three designs explicit; note that the third (a true replay-after-A-first) was **not**
run — it is a separate experiment, not the condition this chapter measures.

![Sequential, joint/interleaved A+B from start, and true replay-after-A (not run)](figures/fig_continual_timelines.pdf)

What this establishes is that **the forgetting seen under sequential training disappears
when the model is trained jointly on both.** It does not demonstrate that a replay
*buffer* salvages an already-trained first model — a stronger test would start from one
A-trained checkpoint and compare B-only vs B-plus-A-replay continuation from there.
Also, note what "no trade-off in B" does and does not mean: both protocols used the **same
example set and the same total step budget** (A and B examples; `steps_a + steps_b`), only
the *order and mixing* differed. So the joint result is **not** because joint training got
extra data, a longer run, or a bigger model — it is the same workload, interleaved rather
than sequenced. That is exactly the procedure finding. We did **not** quantify wall-clock
time or compute precisely enough to claim one schedule is "faster" or "cheaper," so we make
no such claim here; the measured comparison is final task accuracy, not resource cost.

**A note on replication across seeds.** The joint/interleaved-vs-sequential distinction
reproduces under fresh trainings at seeds 1 and 2. Sequential training ends with
A-retention **0.000 / 0.000** while still acquiring B (**0.889 / 0.861**); the
interleaved condition (the joint/interleaved arm, formerly labeled "replay" in this
chapter) retains A at
**1.000 / 1.000** while acquiring B at **0.889 / 0.889** (report:
`docs/reviews/loop/multiseed_replication.md`). So across seeds, sequential
forgets A completely while acquiring B (~0.87–0.89), and joint/interleaved keeps A at 1.0
while acquiring B within one test item as well — the distinction is not a single-seed artifact.

**Scope caveat: the seed re-runs were not a seed-only change.** The seed-0 run recorded
in the table above used `steps_a` 700 + `steps_b` 700 (1,400 steps total, `n_per` 70);
the seeds-1 and 2 re-runs used a **smaller step budget**, `steps_a` 600 + `steps_b` 600
(1,200 steps total, `n_per` 80) — exactly as the shipped manifests record
(`continual.json` versus `continual_seed1.json` and `continual_seed2.json`). So the
replication varied **two** variables, the seed *and* the step budget, not the seed alone,
and it is not a single-variable replication of the seed-0 cells. Within each seed the two
protocols still share one budget (both arms of a manifest run at the same
`steps_a + steps_b`), so the sequential-versus-joint/interleaved contrast is controlled
*inside* each run; what is not held fixed is the budget *across* seeds. The
retention/acquisition values above are reported as measured, and the pattern they show —
sequential forgets A while still acquiring B, joint/interleaved keeps A while acquiring B
just as well (B accuracy within one test item in both: 32/36 vs 32/36 seed0; 32/36 vs
31/36 seed2) — repeats under a fresh seed at a nearby budget; we read them as a
robustness check on that pattern, not as like-for-like replications of the seed-0 numbers
(Appendix C, run provenance ledger).

## Why this result is so striking

The symmetry is what makes this remarkable. Under sequential training, the model
forgets A completely (0.000) but learns B fine (0.889). Under joint training, it keeps A
perfectly (1.000) *and* B accuracy within one test item in both (32/36 vs 32/36
seed0; 32/36 vs 31/36 seed2). Nothing about the model, the
data, or the optimizer changed — only whether the old examples stayed in the mix while
the new ones were learned.

This is the clearest case in the book where the **training protocol, not the model or
the data, determines the outcome.** Same model. Same data. Same optimizer. The only
difference is whether the first capability stays "in the mix" while the second is
learned. Sequential forgets; joint retains.

There is an intuition that makes this easy to see. Imagine a muscle being trained on
exercise A. If it then trains exclusively on exercise B and never revisits A, the
muscle's adaptation to A fades. But if A and B alternate, both stay. The model's
weights are like that muscle — the gradient signal from new examples keeps pushing
them, and if nothing pulls them back toward the old behavior, the old behavior
erases. Joint training is simply making sure the old examples are still in the rotation.

The lesson generalizes with a scope caveat: in this experiment, *how* the task was
introduced (interleaved vs. sequenced) determined whether the earlier capability was
retained. That is a finding about **one schedule comparison**, not proof that procedure
always matters more than the model. If the new task is allowed to dominate the gradient
signal and the old data is removed, the old capability collapses; if old and new stay
interleaved, the model can hold both.

## Reframing a common assumption

And it reframes a common assumption. People often reach for "a bigger model" when
confronted with a model that forgets. This experiment shows the forgetting was not
resolved by anything we did to capacity — a ~0.9M model reaches high final scores on
both task groups when trained jointly (A: 1.000, B: 0.889). It was a *training
procedure* effect. We did **not** test a larger model as a forgetting intervention, so
we cannot conclude that a larger model would not also help here; what we can say is
that the forgetting was already fixable by changing the schedule alone, at this scale,
under these schedules.

The pattern here echoes a deeper truth we've seen all book: the headline number
("did it learn the new thing?") hides the interesting failure ("what did it lose to
get there?"). Measuring B acquisition alone would have made sequential training look
like a success — 0.889, great. Measuring A retention reveals the cost. The lesson is
to always measure *both* the new and the old.

## The shortcut audit

1. **Suspected shortcut: the 0.000 A-retention is an artifact of how we score A.**
   **Why it could explain it:** maybe the A test is too hard, or the model just needs
   more steps.
   **Control:** joint (A+B interleaved) training, identical A test — A-retention 1.000.
   **What it rules out:** a broken A test. The same test that scores 0.000 under
   sequential training scores 1.000 under joint training.
   **What remains:** whether the sequential 0.000 reflects *lost* A rather than
   *unacquired* A. The same-run pre-B measurement settles this: A was 1.000 right after
   phase A and 0.000 after B, so it is a genuine drop, not under-acquisition. Also
   whether this holds for three or more capabilities, and whether joint training
   lets the model *compose* A and B.

## The honest summary

This is a controlled, reproducible demonstration that the *training schedule* affects final
task accuracy: the same workload produces a 0.000 final A accuracy when learned sequentially
and a 1.000 final A accuracy when learned jointly, with B accuracy within one test
item in both (32/36 vs 32/36 seed0; 32/36 vs 31/36 seed2). The
same-trajectory pre-B measurement (a dedicated re-run, Appendix C.9) confirms the
sequential drop is genuine forgetting: A was 1.000 right after phase A and fell to 0.000
after B, so it was acquired and then lost rather than never learned. We make no
resource-cost claim: both protocols used the same
example set and step budget, and we did not quantify compute precisely.

What makes it feel like a real discovery is that the right answer was sitting in a
choice we made near-automatically. When we first set up the experiment, sequential
training was the path of least resistance — learn one thing, then the next. The
surprise came from asking the question we almost didn't ask: what did the model lose
to learn the new thing? And the fix — just keeping old examples in the mix — was so
simple it was almost anticlimactic. But that simplicity is the point. Sometimes the
most important finding in an experiment is not a complex technique but a simple
change to the way we were already working.
