# 21. The Cost of Capability

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

## The cost matrix

Each row is a capability or behavior from our experiments; the columns are the
measurable costs — data, parameters, training steps, and — decisively — the
*generalization* cost.

| Capability | data (examples) | parameters | steps | in-dist pass@1 | surface generalizes? | composes? |
|------------|-----------------|------------|-------|----------------|----------------------|-----------|
| Single primitive (add, sub, …) | 1400 | 0.88M | 1500 | 0.900 | ✗ (new wording → 0.000) | ✗ |
| New identifier robustness | 1400 | 0.88M | 1500 | 0.900 | ✗ (0.350 on new IDs) | — |
| Composition (abs_add, sum_of_abs) | not achieved within tested budgets | 0.9M–29.3M | 1500 | varied by run (exposed) / **0.000** on held-out | ✗ | ✗ (0.000) |
| Continual: A then B (sequential) | 1400+1400 | 0.88M | 1400 | B: 0.889 | — | ✗ (A forgotten) |
| Continual: A+B (replay) | 2800 interleaved | 0.88M | 1400 | A: 1.000, B: 0.889 | — | ✗ |

\*The "exposed" cell is the score on combinations *shown* during training, which varied
across the exposure and diversity runs (0.550–1.000). The held-out composite — the real
composition test — is **0.000** in every run. We do not know how much data would be
needed to achieve composition; we only know it was not achieved within the budgets we
tried. Marking it "∞" would overstate an unmeasured quantity.

## What the costs tell us

**Capability is cheap; robustness is not.** Learning a single primitive costs ~1400
examples and a few minutes on a 0.88M model, and it "works" (0.900). So the *apparent*
cost of a capability is low. But that number is misleading: it measures only
in-distribution correctness.

**The real cost appears when we ask for generalization.** To make a single primitive
robust to *surface* change (new identifiers, new wording), the experiments suggest
the data would need to change substantially — diverse identifiers and wording — not
just add capacity. And composition is not purchasable at this scale at all: it stayed
0.000 at 0.88M, 6.5M, 10.2M, and 29.3M.

**The cost matrix makes a dangerous pricing error visible.** If we only look at the
"in-dist pass@1" column, we would conclude capability is nearly free and scale up
naively. The generalization and composition columns reveal that the cheap number
hides a much more expensive requirement — robust, compositional capability — which we
did not achieve by scaling data or capacity within our tested range.

## The price of each column, read honestly

Let us read the matrix the way a person who has to pay for capability would read it,
not the way a researcher who wants a good headline would read it.

- **A single primitive "costs" about 1,400 examples and a few minutes.** That is the
  cheap row, and it is genuinely cheap. But its surface-generalization column says
  ✗ and its composition column says ✗. So we have bought a capability that works one
  way, one time.
- **New-identifier robustness** is the next row. It costs the *same* 1,400 examples,
  and still fails (0.350 on new IDs). We cannot buy this with more of the same.
- **Composition** is the row that tells the sharpest story: it is marked
  "∞-needed" for data, meaning no amount in our range got us there. The parameter
  column spans 0.9M–29.3M, and it made no difference.
- **Continual learning** is the most interesting row for a practitioner, because it
  is the one where the *cost changed at no cost*. Sequential training loses A (0.000
  retention); replay buys A back at 1.000 with B acquisition unchanged at 0.889. So
  here, one capability was obtained *for free* — no extra data, no extra compute,
  just a different training order. Cost is not always toward "more expense"; the
  right procedure can make a capability free.

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
in-distribution *look* capable while it collapses to 0.000 on any change to the
surface. In a deployed system, that is precisely the failure that appears late and
costs the most.

So the real answer to "what does each capability cost?" is: the easy-to-see cost
(data, parameters, steps) is small and scales predictably; the hard-to-see cost —
making the capability actually generalize and compose — is where the true expense
lies, and at this scale it is simply not purchasable with more of the same resource.

And there is a bright spot in the matrix worth holding onto. The continual-learning
row shows that cost is not always "more of everything." Sometimes, the same inputs,
the same compute, and the same model buy a capability that was previously lost — for
free — simply by choosing a better procedure. Cost, like capability, is often about
*how* we do things, not *how much* we spend.
