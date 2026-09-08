# Chapter 20/21 — The Cost of Capability

This chapter answers: *what does each additional capability actually cost?* Using the
measured experiments, we build a cost matrix that makes the trade-offs explicit —
and reveals something important about what "capability" is costing us.

## The cost matrix

Each row is a capability or behavior from our experiments; the columns are the
measurable costs — data, parameters, training steps, and — decisively — the
*generalization* cost.

| Capability | data (examples) | parameters | steps | in-dist pass@1 | surface generalizes? | composes? |
|------------|-----------------|------------|-------|----------------|----------------------|-----------|
| Single primitive (add, sub, …) | 1400 | 0.88M | 1500 | 0.900 | ✗ (new wording → 0.000) | ✗ |
| New identifier robustness | 1400 | 0.88M | 1500 | 0.900 | ✗ (0.350 on new IDs) | — |
| Composition (abs_add, sum_of_abs) | ∞-needed | 0.9M–6.5M | — | — | — | ✗ (0.000) |
| Continual: A then B (sequential) | 1400+1400 | 0.88M | 1400 | B: 0.889 | — | ✗ (A forgotten) |
| Continual: A+B (replay) | 2800 interleaved | 0.88M | 1400 | A: 1.000, B: 0.889 | — | ✗ |

## What the costs tell us

**Capability is cheap; robustness is not.** Learning a single primitive costs ~1400
examples and a few minutes on a 0.88M model, and it "works" (0.900). So the *apparent*
cost of a capability is low. But that number is misleading: it measures only
in-distribution correctness.

**The real cost appears when you ask for generalization.** To make a single primitive
robust to *surface* change (new identifiers, new wording), the experiments suggest
you'd need to change the data substantially — diverse identifiers and wording — not
just add capacity. And composition is not purchasable at this scale at all: it stayed
0.000 at both 0.88M and 6.5M.

**The cost matrix makes a dangerous pricing error visible.** If you only look at the
"in-dist pass@1" column, you'd conclude capability is nearly free and scale up naively.
The generalization and composition columns reveal that the cheap number hides a much
more expensive requirement — robust, compositional capability — which we did not
achieve by scaling data or capacity within our tested range.

## The honest framing

The most honest "cost" we measured is the cost of **mistaking surface association for
grounded capability**. That cost is high: it makes a model that scores 90%
in-distribution *look* capable while it collapses to 0.000 on any change to the
surface. In a deployed system, that is precisely the failure that appears late and
costs the most.

So the real answer to "what does each capability cost?" is: the easy-to-see cost
(data, parameters, steps) is small and scales predictably; the hard-to-see cost —
making the capability actually generalize and compose — is where the true expense
lies, and at this scale it is simply not purchasable with more of the same resource.
