# 22. The Capability Map

We have run a handful of tightly-controlled experiments. Rather than a list of
results, let us draw the **capability map**: one picture that says, for each behavior
we tested, whether the model acquired it, whether it generalizes, what it costs, and
where it breaks.

We record each finding with an honest epistemic label — what is *proven* (measured),
what is *supported*, what is *suggestive*, and what is *unknown*.

## Why a map, and not a single score

There is a strong temptation, at the end of an investigation, to reach for one number
and say "that's the verdict." It would be satisfying and simple. But every experiment
in this book has argued against exactly that. The model is good at some things and
terrible at others, and those are both true at once. A single number would have to
collapse them, and collapsing them would hide the most important thing: the *shape* of
the boundary.

So we draw a map instead. A map does not pretend to be one verdict; it shows
*dimensions*. It answers, for each question we asked, what we found — and, crucially,
what we did *not* find. That honesty about the unknown is what makes the map worth
more than a headline.

## The four-level generalization map

![The capability map](figures/fig_capability_map.png)

The map puts the measured grid on two axes: the breadth of tasks and the depth
of generalization. The narrow job is well-learned; the broader ground is not.

Recall the four levels from Chapter 2. Here is what we measured at each, on the ~0.9M
model:

| Level | The question | Measured result | Status (in this setup) |
|-------|--------------|-----------------|--------|
| **L1 Mem** | Can it be explained by remembering? | Held-out 59/60; canary → general program | `[MEASURED]` it generalizes primitives, doesn't parrot |
| **L2 Dist** | Does it work on new instances of the same task? | In-distribution 0.900 | `[MEASURED]` yes — here |
| **L3 Surf** | Does it survive superficial change? | *Narrowly-trained model:* new wording → 0.000; new identifiers → 0.350. *Diversity-trained model (same count):* **1.000 / 1.000** — but the strong form ("generalizes to a never-seen family") is not established, since the surface test's family & identifiers were present in the diverse pool | `[MEASURED]` — brittle when trained narrowly; diverse training covers more surfaces (generalization to a truly-held-out family untested) |
| **L4 Struct** | Can it compose known pieces in unseen ways? | 0.000 (baselines also 0.000) | `[MEASURED]` no — in this regime |

This is the map's spine. Read it vertically and it shows a steady decline in how much
we can trust the model's "understanding" as we move from "did it see this before"
(Level 1) to "can it put things together" (Level 4). The model passes the first two
levels cleanly and fails the last two completely. That is the boundary we keep coming
back to.

## The scaling map (what changes it)

| Lever | Tested | Effect on composition |
|-------|--------|-----------------------|
| Model size | 0.88M → 29.3M (~33×) | **none** — still 0.000 at all four sizes |
| Data size | 100 → 3000 examples | helps *in-distribution* (0.10→0.64), not composition |
| Training protocol | sequential vs replay | **big** — fixes continual retention (0.000→1.000) |

The second half of the map is about levers, and it is where the surprising findings
live. We tried three ways to move the composition boundary — more capacity, more data,
and a different training procedure. Two of them did nothing to composition, and one of
them was the decisive lever for a *different* problem (continual learning). This
asymmetry is worth circling, because it tells us where effort does and does not pay.

## What's measured vs. what's unknown

*Every result here is tied to this specific setup — one synthetic task, one
architecture family, one training configuration, capped at ~30M parameters. We say
"here" and "in this regime" deliberately, because these are well-controlled
measurements in one configuration, not proofs that hold everywhere.*

**Measured (this setup):**
- The model learns single operations to ~90% in-distribution and generalizes them
  across instances (L1/L2).
- The *narrowly-trained* model is surface-tied: new wording → 0.000, new identifiers →
  0.350 (L3). The *diversity-trained* model (same count) reaches 1.000/1.000 on the
  tested surface — though, as the caveat notes, that is strongest as a coverage
  statement, not proof of generalization to a wholly unseen wording family.
- It cannot compose: unseen combinations → 0.000, and neither ~33× capacity (across
  0.88M→29.3M) nor more data changes this (L4).
- Continual learning is a procedure problem: sequential forgets (A → 0.000), replay
  retains (A → 1.000) with no acquisition cost.
- The pilot task was retrieval-solvable (retrieval = 1.000), so that split is "too
  easy"; the composition split is not (all baselines 0.000).

**Supported / suggestive / open:**
- The composition failure is now **tested twice, not simply suggestive**: (a) exposure
  to a few composites during training does **not** unlock composition on unseen ones
  (the model memorizes the seen combinations at 0.667 but stays at 0.000 on held-out
  ones); and (b) diversifying the *surface* of the composite exposure (many phrasings ×
  id-sets) also leaves the held-out composite at **0.000**. So it is neither a "just
  show it combinations" fix nor a "diversify the phrasing" fix (Chapter 16).
- The one lever we have **not** isolated is diversity of the *inner structure* — many
  *different* primitive pairings rather than different phrasings of the same few. That
  is the remaining open experiment.
- Whether the composition wall is truly structural or simply sits above our ~30M
  ceiling is **untested** — we stop where the CPU lab becomes impractical.

**Unknown (did not test):**
- Whether behavior on 3+ capabilities or post-continual composition holds.
- Whether a fundamentally different inductive bias (not scale) helps.

*(The composition-exposure question — whether feeding a few composites during training
unlocks composition — we tested in both a naive-exposure and a diversity form; in both
it did **not**: the model memorized the seen combinations but scored 0.000 on held-out
ones. We report this as a measured result under those two schedules, not as proof that
no exposure schedule could unlock composition.)*

## The boundary, in one line

> **A small model learns narrow, individual mappings well and generalizes them across
> instances, but its knowledge is surface-tied and non-compositional — and within the
> tested range, neither more parameters nor more data turns that into robust,
> compositional capability. (We also tested a scheduling change — sequential vs. joint
> training — but that experiment measured retention of *separately learned* task groups,
> not composition, so it does not speak to the composition boundary.)**

## Why the map is the deliverable

This map is the book's real output. It is not a single headline accuracy that would
mislead; it is a precise, honest picture of where capability exists, where it
collapses, and what (and what doesn't) shift the boundary. It is the answer to the
central question — and it is falsifiable, built from real measured runs, and honest
about what remains unknown.

The deeper value of the map is what it does to our confidence. Before drawing it, we
knew "the model is limited." After drawing it, we know more precisely which limits we
*moved* with a lever and which we *did not*: composition and surface-tiedness were not
moved by scale or more-of-the-same data (in our runs), while continual forgetting was
both seen and fixed by how we trained. We are careful not to call the unmoved ones
"structural" as if we had proven their cause — we observed that the tested levers did
not reach them. That distinction — which limits we could move and which we could not —
is the kind of knowledge that changes what a practitioner would try next. It is not
the same as saying "small models are weak"; it is saying "here is where the weakness
lived under our tests, and here is what did and did not reach it."

That precision, not a dramatic narrative, is the honest payoff of the whole brew. And
it is why we are willing to state as an *unknown* the questions we did not answer,
rather than fill the map with confident guesses. A map with a blank region is more
useful than a map painted over with speculation, because the blank marks where the
next investigation should go.
