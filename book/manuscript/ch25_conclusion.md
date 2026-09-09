# 25. Conclusion and Where This Brew Leads

We have built a laboratory, run a battery of controlled experiments, and drawn an
honest map. This is where we stand — and where the investigation goes next.

## What the experiment established

At the core, the answer to the book's central question is now clear and measured:

> How much structured programming capability can a small language model actually
> learn — and how can we tell whether it learned rather than memorized?

The experiments separate cleanly into what the model **can** do and what it **cannot**.

**It can learn, and it learns well — within a narrow regime.** On individual
operations, the model reliably maps a natural-language spec to correct Python, reaching
**~0.90 pass@1** in-distribution on a 0.88M parameter model. It generalizes across
*instances*: on held-out prompts it passes, and on a canary it produces the general
program, not a memorized literal. So this is genuine learning of the narrow task,
not parroting.

**But it is surface-tied and non-compositional.** The two limits that matter:

1. **It anchors to phrasing, not meaning.** Change the variable names (`a,b` →
   `left,right`) and it drops to 0.35; change the wording (same computation, different
   words) and it falls to **0.000** — below both baselines. The external reality check
   confirmed it: a human-written test set scored **0/16**, because the model learned a
   *template*, not the *task*.

2. **It cannot compose what it knows.** Train on `abs` and `add` separately, then ask
   for `abs_add` — it scores **0.000**. And the baselines also collapse to 0.000, so
   the split is fair: only genuine composition solves it, and the model has none.

**The scaling conclusion is the sharpest negative result.** Composition stays at
**0.000** across model sizes from 0.88M to 10.2M. More capacity does not buy
composition. This is not a capacity ceiling in the ~1–10M regime; it is a
structural/learning limit.

## The four-point grid (so far)

| Model | in-distribution | composition |
|-------|-----------------|-------------|
| 0.88M | 0.900 | **0.000** |
| 6.5M  | 0.900 | **0.000** |
| 10.2M | 0.383 | **0.000** |
| 30M   | *(Pending)*    | *(Pending)* |

Two honest notes on this grid. First, the 10.2M point's *in-distribution* regressed to
0.383 — the deeper config was under-trained on this narrow task, an instance of
"bigger isn't always better" at tiny scale; it doesn't change the composition result.
Second, the 30M point is confirmatory: the composition conclusion is already robust at
three sizes.

## The methodology findings

Independent of the model, the **methodology** produced its own results — and several
are as valuable as any model number:

- **Test the tester.** Our own evaluator reported the model at 0.000 on its first run.
  It was the *judge* that was broken (a null-byte artifact), not the model. Fixing it
  revealed the true 0.897. Never trust a number from a system you haven't audited.
- **Test the teacher.** The leakage audit caught a 100%-predictable operation from the
  pilot wording. This is why surface splits need held-out template families.
- **Test the data.** The diversity-vs-quantity experiment showed the *same* example
  count produces surface-fragility (0.000) with minimal diversity or robust
  generalization (1.000) with high diversity. Diversity — not quantity — is what
  creates robust capability.
- **Baselines are first-class.** A trivial TF-IDF retriever dominated the pilot task
  (1.000), proving it was "too easy," and forced us to build harder splits. And the
  moments the model *fell below* a baseline were the most informative results.
- **The protocol, not capacity, determines continual learning.** Sequential training
  destroyed capability A (0.000) when learning B; replay preserved A perfectly (1.000)
  at no cost to B. This is a *procedure* finding.

## Where this brew leads

The honest map points at specific next experiments, not vague "more data / bigger
model":

1. **Does compositional exposure unlock composition?** The biggest open question. We
   never fed the model composited examples directly. Feeding a few (familiar) ones and
   testing unseen ones would tell us whether composition is learnable or a hard
   structure limit.
2. **Does the 10.2M in-distribution regression replicate?** The 0.383 was unexpected.
   A proper training-duration and config sweep at 10M would isolate whether it's
   under-training or a real depth penalty.
3. **Does continuing to scale past 30M shift the boundary?** The grid stops where the
   brew lab's CPU becomes impractical. A larger-scale run (or a GPU) would probe
   whether the composition wall eventually moves.
4. **Does diversity fix composition?** Diversity fixed the *surface* problem
   (0.000 → 1.000). Whether the *same* lever helps composition is the natural next
   test of the "structural data" hypothesis.
5. **Human-style training.** The 0/16 human test set shows the model fails on
   naturally-phrased prompts. Training on diverse, human-style prompts — the lever
   that already fixed surface robustness — is the obvious path to real usability.

## The honest ending

The model was the instrument. The experiment was the subject. We did not build a
general programmer, and we will not pretend otherwise. What we *did* build is the
means to ask, precisely and honestly, what a small model can and cannot learn — and we
got an answer worth having:

> A small model learns narrow tasks well, but its knowledge is surface-tied and
> non-compositional, and within the tested range neither more capacity nor more data
> turns it into robust, compositional capability.

And the brakes we learned — test the tester, test the teacher, compare against
baselines, audit shortcuts, preserve failures — are the durable part. That is the
method worth keeping, and it's the reason the book's real subject was never the model.
