# 12. How Much Brain?

When a model disappoints us, the instinctive response is: *make it bigger.* More
parameters, more capacity, more "brain." If a small model can't combine what it knows,
surely a larger one can.

This chapter tests that instinct directly. And the answer is one of the cleanest
negative results in the book — because it turns out that at our scale, "just make it
bigger" changes almost nothing about composition.

## The setup

We train **four** models on the same primitive-only training set across a ~33× range of
capacity, and test each on (a) in-distribution held-out primitives (new instances of the
training prompts, per the novelty audit in Appendix C) and (b) the held-out composite
operations. To be precise about it, this is **not** a single-variable sweep:
the runs used *different* optimiser step counts (the 6.5M run used 1000 steps, the 10.2M
and 29.3M runs used 800; see Appendix C) and the tokenizer training corpus differed
between the pilot/composition tokenizers. So this is a sweep across capacity **with
training-budget and tokenizer variation alongside it**, not a clean size-only comparison.
We keep that caveat front and center throughout, because it bounds what the result can
say.

| Model | parameters | in-distribution | composition |
|-------|-----------|-----------------|-------------|
| Stage-4 baseline | **884,224** (0.88M) | 0.900 | **0.000** |
| Scaling | **6,500,352** (6.5M) | 0.897 | **0.000** |
| 10M point | **10,195,776** (10.2M) | 0.773 | **0.000** |
| 30M point | **29,290,240** (29.3M) | 0.897 | **0.000** |

That is a **~33×** increase in parameters from the smallest to the largest. On the
thing we care about — composition — nothing changed at all.

![Model size vs composition](figures/fig_model_size.png)

![Illustrative prompts on five selected checkpoints](figures/fig_live_sweep.png)

The first figure is the measured pass@1 grid; the second walks five selected
checkpoints through a battery of *illustrative* prompts — one prompt per case — and
records whether each produced a working program. On the two familiar requests every
checkpoint writes correct code; on a reworded request and a new combination, none
does; on an out-of-scope request (which is not really a task from their training)
none of them declines — the model just writes noise, which is exactly why Gate B
belongs in front of it. The pattern across these *illustrative* prompts is striking: on
the two familiar requests every checkpoint writes correct code, while on the reworded
request and the new combination none does, and on the out-of-scope request none of them
declines — the model just writes noise. (To be precise, these are five illustrative
single prompts, one per condition, not a scored pass@1 grid — the grid is the figure
above.)

### What the models actually say

Scores can feel abstract, so here is the verbatim output for the smallest pilot
(0.88M), exactly as the sweep recorded it. Given the phrasing it was trained on, it
writes clean, correct code:

```
# prompt: returns the sum of two numbers
def solve(a, b):
    return a + b            # correct — and it runs

# prompt: returns the product of two numbers
def solve(a, b):
    return a * b            # correct — and it runs
```

But the moment we change the surface, or combine two things it knows, the same model
produces something that isn't even valid Python:

```
# prompt: give back their total
i solve(a, b:
        return       return b        # syntax error

# prompt: absolute value of each, return their sum
def solve(a, ab                       # syntax error — generation ended early, partial token
```

And given an out-of-scope request, it does not decline at all — it just writes
garbage:

```
# prompt: delete all files
def lenn a.
   .
    nb = abs(b)
    total na > nb:
        return na
    return                             # syntax error — no refusal, just noise
```

The interesting thing is how uniform this is across every model we trained. The 29.3M
model writes the same minimal `return a + b` for the in-distribution phrasing and
falls apart on a reword in exactly the same way. More parameters made the capability
*richer*, not *harder to break*. That is the pattern the heatmap above captures in
one glance.

## The result

Going from ~0.9M to 29.3M parameters:

- **Composition is 0.000 at every size we ran.** The bigger models are *just as* unable to
  combine two learned primitives as the small one. Thirty-three times the capacity
  bought exactly zero compositional generalization *under the training schedules we used*.
- **In-distribution is a roughly stable plateau** (0.773–0.900) — capacity neither
  clearly helped nor hurt the narrow task; it just never helped compose. (The small
  spread needs replication with multiple seeds to interpret precisely; see below.)

## What this means

This directly answers the book's central question — *does more brain buy genuine
capability, or merely more memorization?* — with a decisive answer at this scale:

> **It buys neither, on what we ran.** At ~1–30M parameters, composition stayed at
> 0.000 across every size and schedule we tested.

The boundary we found in Chapter 16 was **not moved by scale in our tests**. We are
careful about calling it a "capacity ceiling": what we observed is that increasing
capacity up to 29.3M, under the schedules we ran, did not produce composition. That is
a statement about what we measured, not a proof that capacity *cannot* in principle.
A bigger model at this scale just did the same narrow thing; it did not develop the
ability to compose in our evaluations.

## The audit: is this a fair comparison?

We must be careful: a few size points don't prove there's no capacity curve anywhere.
But the shape is telling. If capacity were the binding constraint, we'd expect a
*move* — even a small one — across a 33× range. We see none: composition is 0.000 at
all four sizes. The in-distribution scores span 0.773–0.900 across a 33× range. That
spread (0.773 vs 0.900 at 10.2M vs 0.88M) is large enough that we should be honest
that it is **not** an exact flat line — it is a *roughly* stable plateau with some
movement. We did not run multiple training seeds per size, so we cannot put error bars
on these points; the honest claim is that composition did not move (0.000 at every
size), and in-distribution stayed broadly in the same region rather than climbing with
capacity. A clean replication with several seeds per size would let us say whether the
in-distribution differences are real or run-to-run noise; as it is, we treat the
plateau as approximate, not exact.

The more likely explanation is that **composition requires seeing the right kind of
structure in training, not just more parameters.** A model that only ever sees
`add` and `abs` as separate problems has no reason to build a "compose" operator; a
30× bigger network just represents the same reflexes more richly. To break the
composition boundary, the model likely needs *exposure to compositions*, or a
fundamentally different inductive bias — not raw capacity.

## The honest side-finding: the 10M "deficit" was an artifact, not a law

There was a wrinkle we recorded and almost smoothed over. The **10.2M** model
originally measured **0.383** in-distribution — below the 0.897–0.900 of the smaller
models. That looked like "bigger is worse." We flagged it as an open question rather
than a rule.

But when we retrained the 10.2M point with the **same config and seed** (on a clean
run, avoiding the CPU-dispatch crash that had interrupted the original training), it
measured **0.773** — squarely in the healthy plateau family. The original run's
checkpoint had a **syntax rate of just 0.45**: over half of its in-distribution
outputs didn't even parse as valid Python. That is the fingerprint of a
partially-converged checkpoint (the original training hit a hardware-level SIGILL
twice), not a property of the architecture.

So the honest conclusion: at this scale, in-distribution performance is a **stable
plateau (~0.9)**, and the earlier 0.383 was a **training-run artifact** — the kind of
thing that happens when a run is interrupted at the hardware level. It is not
evidence that "bigger is worse." What is robust across all four sizes is the thing
we actually care about: **composition stays at 0.000** no matter the capacity.

## The honest framing

This is a *useful* negative result. It tells us where not to look (raw scaling in the
~1–30M regime) and points at where to look instead (structural data / inductive bias).
And it reframes the whole book: the interesting question is not "how big should the
model be?" but "what kind of capability emerges from what kind of training — and where
does scaling stop being the answer?"

The model was the instrument. The experiment — and the boundary it revealed — was the
subject.
