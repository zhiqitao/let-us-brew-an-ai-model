# 20. What Happens When We Teach It Something New?

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
- **replay / mixed:** interleave A and B examples throughout.

Holding model, data, and optimizer constant while changing only the training
*schedule* is a textbook application of our one-variable discipline. If the results
differ between the two protocols, the difference cannot be attributed to the model,
the data, or the optimizer — it must be the schedule. That makes any difference we
find a *procedure* finding, exactly the thing we want to isolate.

## The result
![Continual learning](figures/fig_continual.png)

| Protocol | **A-retention** | **B-acquisition** |
|----------|-----------------|-------------------|
| **sequential** | **0.000** | 0.889 |
| **replay**     | **1.000** | 0.889 |

This is as clean a result as this book produced.

**Sequential training causes catastrophic forgetting.** After learning arithmetic and
then lists in sequence, the model's A-retention is **0.000** — it completely forgot
the first capability. That is not "degraded"; it is gone. Learning the lists overwrote
the arithmetic.

**Training A and B together prevents the forgetting.** When A and B are simply trained
together from the start (interleaved throughout), the model's A-retention is a perfect
**1.000**, and B-acquisition is **0.889** — identical to sequential. So keeping the old
capability in the mix alongside the new one preserves A with **no behavioral trade-off**
in learning B.

One honest note on the term "replay." This design interleaves A and B **from the start**
— which is really *joint training* on both, not "learn A first, then continue to B
while replaying A." Both answers are legitimate, but they are different questions. The
sequential condition is a true continual-learning setup (does learning B destroy A? —
yes, 0.000). The interleaved condition is a joint-training control (if both are seen
together, is there a forgetting problem at all? — no, 1.000). The timelines below make
the three designs explicit; note that the third (a true replay-after-A-first) was **not**
run — it is a separate experiment, not the one labeled "replay" in this chapter.

![Sequential vs joint vs replay](figures/fig_continual_timelines.png)

What this establishes is that **the forgetting seen under sequential training disappears
when the model is trained jointly on both.** It does not demonstrate that a replay
*buffer* salvages an already-trained first model — a stronger test would start from one
A-trained checkpoint and compare B-only vs B-plus-A-replay continuation from there.
Also, "zero cost" means **zero behavioral cost on B** (both reached 0.889), not zero
compute, storage, or
data-retention cost — the joint model is trained on more distinct examples and takes
longer.

## Why this result is so striking

The symmetry is what makes this remarkable. Under sequential training, the model
forgets A completely (0.000) but learns B fine (0.889). Under replay, it keeps A
perfectly (1.000) *and* learns B just as well (0.889). Nothing about the model, the
data, or the optimizer changed — only whether the old examples stayed in the mix while
the new ones were learned.

This is the clearest case in the book where the **training protocol, not the model or
the data, determines the outcome.** Same model. Same data. Same optimizer. The only
difference is whether the first capability stays "in the mix" while the second is
learned. Sequential forgets; replay retains.

There is an intuition that makes this easy to see. Imagine a muscle being trained on
exercise A. If it then trains exclusively on exercise B and never revisits A, the
muscle's adaptation to A fades. But if A and B alternate, both stay. The model's
weights are like that muscle — the gradient signal from new examples keeps pushing
them, and if nothing pulls them back toward the old behavior, the old behavior
erases. Replay is simply making sure the old examples are still in the rotation.

The lesson generalizes directly: when a new capability is added to a model, *how* it
is done matters more than any property of the model itself. If the new task is allowed
to dominate the gradient signal and the old data is removed, the old capability
collapses. If old and new stay interleaved, the model can hold both.

## Reframing a common assumption

And it reframes a common assumption. People often reach for "a bigger model" when
confronted with a model that forgets. This experiment shows the forgetting was never
a capacity problem — a ~0.9M model reaches high final scores on both task groups when
trained jointly (A: 1.000, B: 0.889). It was a *training procedure* problem. Here, as
with composition, the instinctive fix ("make it bigger") would have been exactly wrong.

The pattern here echoes a deeper truth we've seen all book: the headline number
("did it learn the new thing?") hides the interesting failure ("what did it lose to
get there?"). Measuring B acquisition alone would have made sequential training look
like a success — 0.889, great. Measuring A retention reveals the cost. The lesson is
to always measure *both* the new and the old.

## The shortcut audit

1. **Suspected shortcut: the 0.000 A-retention is an artifact of how we score A.**
   **Why it could explain it:** maybe the A test is too hard, or the model just needs
   more steps.
   **Control:** replay mode, identical A test — A-retention 1.000.
   **What it rules out:** a broken A test. The same test that scores 0.000 in
   sequential scores 1.000 in replay.
   **What remains:** whether this holds for three or more capabilities, and whether
   replay-adds support *composition* of A and B after the fact.

## The honest summary

Acquiring a new capability can destroy an old one — and it is largely up to how we
train. Sequential training forgets; keeping both in the mix preserves them. This is a
controlled, reproducible demonstration that destructive forgetting is a procedure
problem, and it is one of the most practically useful results in the book. ("No cost"
here means no behavioral cost on the new capability — not zero compute, storage, or
data-retention cost, and not a true replay-after-A-first demonstration; see above.)

What makes it feel like a real discovery is that the right answer was sitting in a
choice we made near-automatically. When we first set up the experiment, sequential
training was the path of least resistance — learn one thing, then the next. The
surprise came from asking the question we almost didn't ask: what did the model lose
to learn the new thing? And the fix — just keeping old examples in the mix — was so
simple it was almost anticlimactic. But that simplicity is the point. Sometimes the
most important finding in an experiment is not a complex technique but a simple
change to the way we were already working.
