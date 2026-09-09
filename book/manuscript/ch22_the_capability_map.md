# 22. The Capability Map

We have run a handful of tightly-controlled experiments. Rather than a list of
results, let us draw the **capability map**: one picture that says, for each behavior
we tested, whether the model acquired it, whether it generalizes, what it costs, and
where it breaks.

We record each finding with an honest epistemic label — what is *proven* (measured),
what is *supported*, what is *suggestive*, and what is *unknown*.

## The four-level generalization map

Recall the four levels from Chapter 2. Here is what we measured at each, on the ~0.9M
model:

| Level | The question | Measured result | Status |
|-------|--------------|-----------------|--------|
| **L1 Mem** | Can it be explained by remembering? | Held-out 59/60; canary → general program | `[PROVEN]` it generalizes primitives, doesn't parrot |
| **L2 Dist** | Does it work on new instances of the same task? | In-distribution 0.900 | `[PROVEN]` yes |
| **L3 Surf** | Does it survive superficial change? | New wording → 0.000; new identifiers → 0.350 | `[PROVEN]` no — surface-tied |
| **L4 Struct** | Can it compose known pieces in unseen ways? | 0.000 (baselines also 0.000) | `[PROVEN]` no |

## The scaling map (what changes it)

| Lever | Tested | Effect on composition |
|-------|--------|-----------------------|
| Model size | 0.88M → 29.3M (~33×) | **none** — still 0.000 at all four sizes |
| Data size | 100 → 3000 examples | helps *in-distribution* (0.10→0.64), not composition |
| Training protocol | sequential vs replay | **big** — fixes continual retention (0.000→1.000) |

## What's proven vs. what's unknown

**Proven (measured, this setup):**
- The model learns single operations to ~90% in-distribution and generalizes them
  across instances (L1/L2).
- It is surface-tied: new wording → 0.000, new identifiers → 0.350 (L3).
- It cannot compose: unseen combinations → 0.000, and neither ~33× capacity (across
  0.88M→29.3M) nor more data changes this (L4).
- Continual learning is a procedure problem: sequential forgets (A → 0.000), replay
  retains (A → 1.000) with no acquisition cost.
- The pilot task was retrieval-solvable (retrieval = 1.000), so that split is "too
  easy"; the composition split is not (all baselines 0.000).

**Supported / suggestive:**
- The composition failure is likely *structural-data* (exposure to combinations),
  not capacity — but we did not test feeding the model compositions directly, so this
  is suggestive.

**Unknown (did not test):**
- Whether feeding composites during training unlocks composition.
- Whether behavior on 3+ capabilities or post-continual composition holds.
- Human-written task transfer (recommended external sanity check, not yet run).
- Whether a fundamentally different inductive bias (not scale) helps.

## The boundary, in one line

> **A small model learns narrow, individual mappings well and generalizes them across
> instances, but its knowledge is surface-tied and non-compositional — and within the
> tested range, neither more parameters nor more data nor a different training order
> turns that into robust, compositional capability.**

## Why the map is the deliverable

This map is the book's real output. It is not a single headline accuracy that would
mislead; it is a precise, honest picture of where capability exists, where it
collapses, and what (and what doesn't) shift the boundary. It is the answer to the
central question — and it is falsifiable, built from real measured runs, and honest
about what remains unknown.
